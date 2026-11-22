"""
Subprocess Execution Guard and Binary Confinement.

Restricts process execution to whitelisted interpreters (sys.executable) and tools (git),
confines working directories (cwd) to the repository boundary, sanitizes command-line
arguments for path traversal, and blocks shell chaining and redirection operators.
"""

import os
import sys
import shlex
import shutil
import subprocess
from typing import List, Set, Optional, Union

from sandbox.validator import PathValidator, Permission
from sandbox.exceptions import ExecutionBlockedViolation


APPROVED_SYSTEM_BINARIES: Set[str] = {"git", "git.exe"}
SHELL_OPERATORS: Set[str] = {";", "&", "|", ">", "<", "$", "`"}


class ExecutionGuard:
    """
    Guards process execution against unauthorized binaries, path leakage,
    and shell injection attacks.
    """

    def __init__(
        self,
        validator: PathValidator,
        allowed_binaries: Optional[Set[str]] = None,
    ):
        self.validator = validator
        self.allowed_interpreter = os.path.realpath(sys.executable)
        self.approved_system_binaries: Set[str] = set(
            b.lower() for b in (allowed_binaries or APPROVED_SYSTEM_BINARIES)
        )

    def validate_command(
        self,
        command: Union[str, List[str]],
        cwd: Optional[Union[str, os.PathLike]] = None,
    ) -> List[str]:
        """
        Validate command executable, arguments, and working directory against sandbox boundaries.
        Returns the sanitized argument list.
        """
        # 1. Enforce CWD confinement
        effective_cwd = cwd or self.validator.primary_root
        try:
            self.validator.validate_access(effective_cwd, Permission.READ)
        except Exception as e:
            raise ExecutionBlockedViolation(
                f"Working directory '{effective_cwd}' is outside sandbox boundaries: {e}"
            ) from e

        # 2. Parse command string or list
        if isinstance(command, str):
            for op in SHELL_OPERATORS:
                if op in command:
                    raise ExecutionBlockedViolation(
                        f"Shell chaining and redirection operator '{op}' is prohibited."
                    )
            try:
                raw_args = shlex.split(command, posix=False)
            except Exception:
                raw_args = command.split()
            args = [a.strip('"\'') for a in raw_args]
        else:
            args = [str(a) for a in command]

        if not args or not args[0].strip():
            raise ExecutionBlockedViolation("Empty command execution rejected.")

        # 3. Validate executable binary
        bin_entry = args[0]
        bin_name = os.path.basename(bin_entry).lower()

        if bin_name in {"python", "python.exe", "python3", "python3.exe"}:
            if bin_entry != os.path.basename(bin_entry):
                canon_passed = os.path.normcase(str(os.path.realpath(bin_entry)))
                canon_sys = os.path.normcase(str(self.allowed_interpreter))
                if canon_passed != canon_sys:
                    raise ExecutionBlockedViolation(
                        f"Binary path '{bin_entry}' does not match authorized interpreter '{self.allowed_interpreter}'."
                    )
            args[0] = self.allowed_interpreter
        elif bin_name in self.approved_system_binaries:
            # Authorized system tool (e.g. git)
            resolved_sys_bin = shutil.which(bin_name)
            if not resolved_sys_bin:
                raise ExecutionBlockedViolation(
                    f"Approved system binary '{bin_name}' is not found in system PATH."
                )

            is_bare_name = (bin_entry == os.path.basename(bin_entry))
            if is_bare_name:
                # Bare command name (e.g. 'git') resolving to legitimate system PATH location
                pass
            else:
                # A path was passed; verify canonical path matches system binary
                canon_passed = os.path.normcase(str(os.path.realpath(bin_entry)))
                canon_sys = os.path.normcase(str(os.path.realpath(resolved_sys_bin)))
                if canon_passed != canon_sys:
                    raise ExecutionBlockedViolation(
                        f"Binary path '{bin_entry}' does not match authorized system binary '{resolved_sys_bin}'."
                    )
        else:
            resolved_sys_bin = shutil.which(bin_entry)
            target_to_validate = None

            if (self.validator.primary_root / bin_entry).exists():
                target_to_validate = bin_entry
            elif resolved_sys_bin:
                target_to_validate = resolved_sys_bin
            else:
                target_to_validate = bin_entry

            try:
                # Target must reside within an authorized boundary with EXECUTE permission
                canon_bin = self.validator.validate_access(target_to_validate, Permission.EXECUTE)
                if not canon_bin.exists():
                    raise ExecutionBlockedViolation(
                        f"Binary or script '{bin_entry}' does not exist."
                    )
                args[0] = str(canon_bin)
            except Exception as e:
                raise ExecutionBlockedViolation(
                    f"Execution of binary '{bin_entry}' is blocked: {e}"
                ) from e

        # 4. Scan remaining arguments for path references
        def _check_path_candidate(candidate: str, raw_arg: str):
            clean = candidate.strip("\"'")
            if not clean:
                return
            # Check for Windows drive path, relative traversal, UNC, or root-relative path
            is_path_like = (
                ":\\" in clean
                or ":/" in clean
                or ".." in clean
                or clean.startswith("\\")
                or clean.startswith("/")
            )
            if is_path_like:
                try:
                    self.validator.validate_access(clean, Permission.READ)
                except Exception as e:
                    raise ExecutionBlockedViolation(
                        f"Command argument refers to unauthorized path '{raw_arg}': {e}"
                    ) from e

        for arg in args[1:]:
            if arg.startswith("-"):
                if "=" in arg:
                    _, _, opt_val = arg.partition("=")
                    _check_path_candidate(opt_val, arg)
            else:
                _check_path_candidate(arg, arg)

        return args

    def run(
        self,
        command: Union[str, List[str]],
        cwd: Optional[Union[str, os.PathLike]] = None,
        timeout: int = 60,
        capture_output: bool = True,
        text: bool = True,
        check: bool = False,
        **kwargs,
    ) -> subprocess.CompletedProcess:
        """
        Execute command with validated binary, arguments, cwd, and shell=False enforcement.
        """
        sanitized_args = self.validate_command(command, cwd=cwd)
        effective_cwd = str(self.validator.canonicalize(cwd or self.validator.primary_root))
        kwargs.pop("shell", None)

        return subprocess.run(
            sanitized_args,
            cwd=effective_cwd,
            timeout=timeout,
            capture_output=capture_output,
            text=text,
            check=check,
            shell=False,
            **kwargs,
        )
