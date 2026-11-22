"""
Windows-Hardened Canonical Path Confinement & Validation.

Enforces filesystem access strictly within repository and designated project boundaries.
Neutralizes Windows-specific attack vectors including directory traversal (..),
mixed slashes, case folding, NTFS Alternate Data Streams (ADS), reserved device names,
Windows 8.3 short names, UNC network shares, and NTFS junction/symlink escapes.
"""

import os
import sys
import ctypes
import pathlib
from enum import Flag, auto
from typing import List, Set, Optional, Union

from sandbox.exceptions import (
    PathTraversalViolation,
    AlternateDataStreamViolation,
    DeviceNameViolation,
    TamperProtectionViolation,
)


class Permission(Flag):
    """Access permissions for sandbox path boundaries."""
    NONE = 0
    READ = auto()
    WRITE = auto()
    EXECUTE = auto()
    READ_WRITE = READ | WRITE
    ALL = READ | WRITE | EXECUTE


RESERVED_DEVICE_NAMES: Set[str] = {
    "CON", "PRN", "AUX", "NUL",
    "CONIN$", "CONOUT$", "CLOCK$",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


class PathBoundary:
    """Represents an allowed directory boundary and its granted permissions."""

    def __init__(self, root_path: Union[str, pathlib.Path], permission: Permission = Permission.ALL):
        self.root_path = pathlib.Path(root_path).resolve()
        self.normalized_root = os.path.normcase(str(self.root_path))
        self.permission = permission

    def contains(self, target_path: Union[str, pathlib.Path]) -> bool:
        """Check if target_path is equal to or resides inside this boundary."""
        norm_target = os.path.normcase(str(target_path))
        if norm_target == self.normalized_root:
            return True
        try:
            target_p = pathlib.Path(norm_target)
            root_p = pathlib.Path(self.normalized_root)
            if target_p.is_relative_to(root_p):
                return True
        except (ValueError, TypeError, AttributeError):
            pass

        try:
            return os.path.commonpath([self.normalized_root, norm_target]) == self.normalized_root
        except (ValueError, TypeError):
            return False

    def __repr__(self) -> str:
        return f"PathBoundary(root={self.root_path}, perm={self.permission.name})"


class PathValidator:
    """
    Authoritative Windows path validator and confinement engine.
    Sanitizes, canonicalizes, and verifies all filesystem paths against active boundaries.
    """

    def __init__(
        self,
        primary_root: Union[str, pathlib.Path],
        additional_boundaries: Optional[List[PathBoundary]] = None,
        protected_files: Optional[Set[str]] = None,
    ):
        self.primary_root = pathlib.Path(primary_root).resolve()
        self.boundaries: List[PathBoundary] = [
            PathBoundary(self.primary_root, Permission.ALL)
        ]
        if additional_boundaries:
            self.boundaries.extend(additional_boundaries)

        # Files that cannot be modified even if located inside an allowed root
        self.protected_files: Set[str] = protected_files or {
            ".sandbox_config.json",
            ".git/config",
            ".git/credentials",
        }

    def sanitize_raw_string(self, raw_path: str) -> str:
        """
        Sanitize raw path string before canonicalization:
        - Detect null bytes
        - Detect UNC network shares (prohibit \\\\server\\\\share, normalize \\\\?\\\\C:\\)
        - Detect NTFS Alternate Data Streams (prohibit colon beyond drive letter)
        - Detect Windows reserved device names (CON, PRN, AUX, NUL, COM1-9, LPT1-9)
        """
        if "\0" in raw_path:
            raise PathTraversalViolation("Null byte injection detected in path.")

        stripped = raw_path.strip()
        norm = os.path.normpath(stripped)

        # Guard 1: Detect UNC Network Shares (\\\\server\\share, //server/share, etc.) and NT Object Manager paths
        if norm.startswith(r"\??") or stripped.startswith(r"\??"):
            raise PathTraversalViolation(f"NT object manager paths are prohibited: {raw_path}")

        if norm.startswith(r"\\") or stripped.startswith(r"\\") or stripped.startswith("//"):
            # Allow extended local drive prefix: \\?\C:\... or \\.\C:\...
            upper_norm = norm.upper()
            prefix_q = "\\\\?\\"
            prefix_dot = "\\\\.\\"
            if (upper_norm.startswith(prefix_q) or upper_norm.startswith(prefix_dot)) and len(norm) >= 6:
                if norm[5] == ":" and norm[4].isalpha():
                    norm = norm[4:]  # Convert \\?\C:\path to C:\path
                else:
                    raise PathTraversalViolation(f"UNC network paths and device namespaces are prohibited: {raw_path}")
            else:
                raise PathTraversalViolation(f"UNC network paths are prohibited: {raw_path}")

        # Guard 2: Detect NTFS Alternate Data Streams (colon beyond drive letter index 1)
        drive_suffix = norm
        if len(norm) >= 2 and norm[1] == ":" and norm[0].isalpha():
            drive_suffix = norm[2:]
        if ":" in drive_suffix:
            raise AlternateDataStreamViolation(f"NTFS Alternate Data Stream detected: {raw_path}")

        # Guard 3: Detect Reserved Device Names in path components
        parts = pathlib.PurePath(norm).parts
        for part in parts:
            # Skip Windows drive specifier like 'C:\' or 'c:'
            if len(part) == 2 and part[1] == ":" and part[0].isalpha():
                continue
            if len(part) == 3 and part[1] == ":" and part[0].isalpha() and part[2] in ("\\", "/"):
                continue

            stem = part.split(".")[0].upper()
            if stem in RESERVED_DEVICE_NAMES:
                raise DeviceNameViolation(f"Access to Windows reserved device name '{part}' is blocked.")

        return norm

    def expand_long_path(self, path: pathlib.Path) -> pathlib.Path:
        """Expand Windows 8.3 short names to long filenames using Win32 API."""
        if sys.platform == "win32" and hasattr(ctypes, "windll"):
            try:
                buf = ctypes.create_unicode_buffer(1024)
                res = ctypes.windll.kernel32.GetLongPathNameW(str(path), buf, 1024)
                if res > 0:
                    return pathlib.Path(buf.value)
            except Exception:
                pass
        return path

    def canonicalize(self, target: Union[str, pathlib.Path]) -> pathlib.Path:
        """
        Fully resolve symlinks, junction points, and relative references.
        For non-existent targets (new write targets), resolves the nearest existing ancestor.
        """
        sanitized_str = self.sanitize_raw_string(str(target))
        path_obj = pathlib.Path(sanitized_str)

        # If relative, anchor to primary root
        if not path_obj.is_absolute():
            path_obj = self.primary_root / path_obj

        # For existing paths, resolve symlinks and junctions
        if path_obj.exists():
            resolved = pathlib.Path(os.path.realpath(str(path_obj)))
        else:
            # If target does not exist yet (e.g. write target), resolve nearest existing ancestor
            ancestor = path_obj.parent
            non_existent_parts = [path_obj.name]
            while not ancestor.exists() and ancestor != ancestor.parent:
                non_existent_parts.insert(0, ancestor.name)
                ancestor = ancestor.parent

            resolved_ancestor = pathlib.Path(os.path.realpath(str(ancestor)))
            resolved = resolved_ancestor.joinpath(*non_existent_parts)

        return self.expand_long_path(resolved)

    def validate_access(
        self,
        target: Union[str, pathlib.Path],
        required_perm: Permission = Permission.READ,
    ) -> pathlib.Path:
        """
        Validate that target path resides within an authorized boundary with required permissions.
        Raises PathTraversalViolation, AlternateDataStreamViolation, DeviceNameViolation,
        or TamperProtectionViolation on violation.
        Returns the canonical, validated Path object on success.
        """
        canonical_path = self.canonicalize(target)
        norm_canonical = os.path.normcase(str(canonical_path))

        # Check system-protected files against writes / modification
        if bool(required_perm & (Permission.WRITE | Permission.EXECUTE)):
            for prot in self.protected_files:
                prot_canon = os.path.normcase(str((self.primary_root / prot).resolve()))
                if norm_canonical == prot_canon:
                    raise TamperProtectionViolation(f"Modifying system-protected file '{prot}' is prohibited.")

                # Check relative path
                try:
                    rel = canonical_path.relative_to(self.primary_root)
                    rel_str = rel.as_posix().lower()
                    if rel_str == prot.lower() or os.path.normcase(str(rel)) == os.path.normcase(prot):
                        raise TamperProtectionViolation(f"Modifying system-protected file '{prot}' is prohibited.")
                except ValueError:
                    pass

        # Evaluate against active boundaries
        for boundary in self.boundaries:
            if boundary.contains(canonical_path):
                if (boundary.permission.value & required_perm.value) == required_perm.value:
                    return canonical_path
                else:
                    raise PathTraversalViolation(
                        f"Permission denied: '{canonical_path}' requires permission {required_perm.name}, "
                        f"but boundary '{boundary.root_path}' only grants {boundary.permission.name}."
                    )

        raise PathTraversalViolation(
            f"Access blocked: Path '{canonical_path}' is outside designated sandbox boundaries."
        )
