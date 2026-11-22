"""
Sandbox Package for kingdom_of_agents.

Provides application-level security, Windows-hardened path confinement,
subprocess execution guards, zero-telemetry network isolation, and
PBKDF2-HMAC-SHA256 password protection for boundary administration.
"""

import os
import pathlib
from typing import Union, Optional, List, Set

from sandbox.exceptions import (
    SecuritySandboxViolation,
    PathTraversalViolation,
    AlternateDataStreamViolation,
    DeviceNameViolation,
    ExecutionBlockedViolation,
    NetworkEgressBlocked,
    AuthenticationError,
    TamperProtectionViolation,
)
from sandbox.validator import (
    Permission,
    PathBoundary,
    PathValidator,
    RESERVED_DEVICE_NAMES,
)
from sandbox.execution import (
    ExecutionGuard,
    APPROVED_SYSTEM_BINARIES,
    SHELL_OPERATORS,
)
from sandbox.network import (
    NetworkGuard,
    DEFAULT_LOOPBACK_HOSTS,
)
from sandbox.auth import (
    PasswordManager,
    PBKDF2_ITERATIONS,
    SALT_BYTES,
    MIN_PASSWORD_LENGTH,
    DEFAULT_ADMIN_PASSWORD,
)
from sandbox.context import SandboxContext
from sandbox.config import (
    SandboxConfig,
    DEFAULT_PROJECT_ROOT,
    DEFAULT_DESIGNATED_MODEL_PATH,
    DEFAULT_PROTECTED_FILES,
)


class SecuritySandbox:
    """
    Master sandbox facade for kingdom_of_agents.
    Coordinates path validation, execution confinement, telemetry blocking,
    and administrative password authorization.
    """

    def __init__(
        self,
        project_root: Optional[Union[str, pathlib.Path]] = None,
        config_file: str = ".sandbox_config.json",
        default_password: Optional[str] = None,
    ):
        if project_root:
            self.root = pathlib.Path(project_root).resolve()
        else:
            # Detect whether DEFAULT_PROJECT_ROOT exists; if not, anchor to current repo
            if DEFAULT_PROJECT_ROOT.exists():
                self.root = DEFAULT_PROJECT_ROOT
            else:
                self.root = pathlib.Path(__file__).parent.parent.resolve()

        config_path = self.root / config_file

        # Configure designated external path for frozen Gemma 4 model weights
        designated_model = DEFAULT_DESIGNATED_MODEL_PATH
        additional_boundaries = [
            PathBoundary(designated_model, Permission.READ)
        ]

        self.auth_manager = PasswordManager(
            config_path=config_path,
            default_password=default_password,
        )
        self.validator = PathValidator(
            primary_root=self.root,
            additional_boundaries=additional_boundaries,
            protected_files=set(DEFAULT_PROTECTED_FILES),
        )
        self.execution = ExecutionGuard(self.validator)
        self.network = NetworkGuard()

    def get_context(self) -> SandboxContext:
        """Obtain a runtime SandboxContext manager for active interception."""
        return SandboxContext(self.validator, self.execution, self.network)

    def add_allowed_path(
        self,
        path: Union[str, pathlib.Path],
        permission: Union[str, Permission],
        password: str,
    ) -> PathBoundary:
        """
        Authorize and add a new directory boundary.
        Requires administrative password verification.
        """
        self.auth_manager.authenticate_and_authorize(password)

        if isinstance(permission, Permission):
            perm_flag = permission
        else:
            perm_flag = Permission.NONE
            p_str = permission.lower()
            if "all" in p_str:
                perm_flag = Permission.ALL
            else:
                if "r" in p_str:
                    perm_flag |= Permission.READ
                if "w" in p_str:
                    perm_flag |= Permission.WRITE
                if "x" in p_str:
                    perm_flag |= Permission.EXECUTE

        boundary = PathBoundary(path, perm_flag)
        self.validator.boundaries.append(boundary)
        return boundary

    def remove_allowed_path(self, path: Union[str, pathlib.Path], password: str):
        """
        Remove an authorized boundary.
        Requires administrative password verification.
        """
        self.auth_manager.authenticate_and_authorize(password)
        target = os.path.normcase(str(pathlib.Path(path).resolve()))
        self.validator.boundaries = [
            b for b in self.validator.boundaries if b.normalized_root != target
        ]

    def read_text(
        self,
        relative_or_abs_path: Union[str, pathlib.Path],
        encoding: str = "utf-8",
    ) -> str:
        """Read text from a validated file path within allowed boundaries."""
        valid_path = self.validator.validate_access(relative_or_abs_path, Permission.READ)
        with open(valid_path, "r", encoding=encoding) as f:
            return f.read()

    def write_text(
        self,
        relative_or_abs_path: Union[str, pathlib.Path],
        content: str,
        encoding: str = "utf-8",
    ):
        """Write text to a validated file path within allowed boundaries."""
        valid_path = self.validator.validate_access(relative_or_abs_path, Permission.WRITE)
        valid_path.parent.mkdir(parents=True, exist_ok=True)
        with open(valid_path, "w", encoding=encoding) as f:
            f.write(content)

    def run_command(
        self,
        cmd: Union[str, List[str]],
        cwd: Optional[Union[str, pathlib.Path]] = None,
        **kwargs,
    ):
        """Execute a command under subprocess execution confinement."""
        return self.execution.run(cmd, cwd=cwd, **kwargs)


__all__ = [
    "SecuritySandbox",
    "SandboxContext",
    "PathValidator",
    "PathBoundary",
    "Permission",
    "RESERVED_DEVICE_NAMES",
    "ExecutionGuard",
    "APPROVED_SYSTEM_BINARIES",
    "SHELL_OPERATORS",
    "NetworkGuard",
    "DEFAULT_LOOPBACK_HOSTS",
    "PasswordManager",
    "PBKDF2_ITERATIONS",
    "SALT_BYTES",
    "MIN_PASSWORD_LENGTH",
    "DEFAULT_ADMIN_PASSWORD",
    "SandboxConfig",
    "DEFAULT_PROJECT_ROOT",
    "DEFAULT_DESIGNATED_MODEL_PATH",
    "DEFAULT_PROTECTED_FILES",
    "SecuritySandboxViolation",
    "PathTraversalViolation",
    "AlternateDataStreamViolation",
    "DeviceNameViolation",
    "ExecutionBlockedViolation",
    "NetworkEgressBlocked",
    "AuthenticationError",
    "TamperProtectionViolation",
]
