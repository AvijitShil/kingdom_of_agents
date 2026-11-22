"""
Unit Tests for ExecutionGuard and Subprocess Confinement.

Validates binary whitelisting (python, git), shell operator rejection,
command argument path scanning, cwd confinement, and execution output.
"""

import sys
import pytest

from sandbox.validator import PathValidator, Permission
from sandbox.execution import ExecutionGuard
from sandbox.exceptions import ExecutionBlockedViolation


@pytest.fixture
def sandbox_root(tmp_path):
    """Create a temporary sandbox root directory with sample script."""
    root = tmp_path / "sandbox_repo"
    root.mkdir()
    script = root / "script.py"
    script.write_text("print('EXEC_SUCCESS')", encoding="utf-8")
    return root


@pytest.fixture
def execution_guard(sandbox_root):
    """Create ExecutionGuard bounded to sandbox_root."""
    validator = PathValidator(primary_root=sandbox_root)
    return ExecutionGuard(validator=validator)


def test_valid_python_execution(execution_guard, sandbox_root):
    """Test running allowed Python command and capturing output."""
    res = execution_guard.run(
        [sys.executable, "-c", "print('HELLO_SANDBOX')"],
        cwd=sandbox_root,
    )
    assert res.returncode == 0
    assert "HELLO_SANDBOX" in res.stdout


def test_python_alias_normalization(execution_guard, sandbox_root):
    """Test that 'python' command string maps to allowed interpreter."""
    cmd = ["python", "-c", "import sys; print(sys.version_info[0])"]
    sanitized = execution_guard.validate_command(cmd, cwd=sandbox_root)
    assert sanitized[0] == execution_guard.allowed_interpreter


def test_git_tool_allowed(execution_guard, sandbox_root):
    """Test that approved system tool 'git' is allowed in command list."""
    sanitized = execution_guard.validate_command(["git", "--version"], cwd=sandbox_root)
    assert sanitized[0] == "git"


def test_unauthorized_binary_blocked(execution_guard, sandbox_root):
    """Test that unauthorized system binaries and external executables are blocked."""
    prohibited_binaries = [
        ["powershell.exe", "-Command", "Get-Process"],
        ["cmd.exe", "/c", "dir"],
        ["certutil.exe", "-urlcache"],
        ["wscript.exe", "payload.vbs"],
        [r"C:\Windows\System32\calc.exe"],
    ]
    for bin_cmd in prohibited_binaries:
        with pytest.raises(ExecutionBlockedViolation):
            execution_guard.validate_command(bin_cmd, cwd=sandbox_root)


def test_shell_operators_rejected(execution_guard, sandbox_root):
    """Test rejection of shell chaining and redirection operators in command strings."""
    malicious_commands = [
        "python script.py; rm -rf /",
        "python script.py && dir",
        "python script.py | grep error",
        "python script.py > C:\\secret.txt",
        "python script.py < input.txt",
        "python script.py `whoami`",
        "python -c 'print($SECRET)'",
    ]
    for cmd in malicious_commands:
        with pytest.raises(ExecutionBlockedViolation):
            execution_guard.validate_command(cmd, cwd=sandbox_root)


def test_unauthorized_argument_path_blocked(execution_guard, sandbox_root):
    """Test that command arguments referencing files outside sandbox are rejected."""
    external_arg_cmds = [
        ["python", "-c", "import sys", r"C:\Windows\System32\drivers\etc\hosts"],
        ["python", "-c", "import sys", r"..\outside_secret.txt"],
        ["python", "-c", "import sys", r"\\attacker\share\data.bin"],
    ]
    for cmd in external_arg_cmds:
        with pytest.raises(ExecutionBlockedViolation):
            execution_guard.validate_command(cmd, cwd=sandbox_root)


def test_authorized_argument_path_allowed(execution_guard, sandbox_root):
    """Test that arguments referencing files inside sandbox are accepted."""
    in_repo_file = sandbox_root / "script.py"
    cmd = ["python", str(in_repo_file)]
    sanitized = execution_guard.validate_command(cmd, cwd=sandbox_root)
    assert sanitized[1] == str(in_repo_file.resolve())


def test_cwd_confinement(execution_guard, tmp_path, sandbox_root):
    """Test that working directory outside repository is strictly rejected."""
    outside_dir = tmp_path / "outside_dir"
    outside_dir.mkdir()

    # Outside CWD raises ExecutionBlockedViolation
    with pytest.raises(ExecutionBlockedViolation):
        execution_guard.validate_command(["python", "-c", "print(1)"], cwd=outside_dir)

    # In-repo CWD succeeds
    sanitized = execution_guard.validate_command(["python", "-c", "print(1)"], cwd=sandbox_root)
    assert sanitized[0] == execution_guard.allowed_interpreter


def test_empty_command_rejected(execution_guard, sandbox_root):
    """Test that empty command list or string raises ExecutionBlockedViolation."""
    with pytest.raises(ExecutionBlockedViolation):
        execution_guard.validate_command([], cwd=sandbox_root)

    with pytest.raises(ExecutionBlockedViolation):
        execution_guard.validate_command("", cwd=sandbox_root)



def test_disguised_external_git_binary_rejected(execution_guard, tmp_path, sandbox_root):
    """Test that an external binary named git.exe outside repository is rejected."""
    outside_dir = tmp_path / "outside_bin"
    outside_dir.mkdir()
    fake_git = outside_dir / "git.exe"
    fake_git.write_text("#!fake git", encoding="utf-8")

    with pytest.raises(ExecutionBlockedViolation) as exc_info:
        execution_guard.validate_command([str(fake_git), "status"], cwd=sandbox_root)
    assert "does not match authorized system binary" in str(exc_info.value) or "blocked" in str(exc_info.value)


def test_disguised_external_python_binary_rejected(execution_guard, tmp_path, sandbox_root):
    """Test that an external binary named python.exe outside repository is rejected."""
    outside_dir = tmp_path / "outside_py"
    outside_dir.mkdir()
    fake_py = outside_dir / "python.exe"
    fake_py.write_text("#!fake python", encoding="utf-8")

    with pytest.raises(ExecutionBlockedViolation) as exc_info:
        execution_guard.validate_command([str(fake_py), "-c", "print(1)"], cwd=sandbox_root)
    assert "does not match authorized interpreter" in str(exc_info.value) or "blocked" in str(exc_info.value)


def test_argument_path_scanning_with_equals_sign(execution_guard, sandbox_root):
    """Test that arguments with --option=path syntax are scanned and validated."""
    # Unauthorized path after '=' must be blocked
    unauthorized_args = [
        ["git", r"--output=C:\Windows\System32\evil.txt"],
        ["git", r"--config=..\outside_secret.txt"],
        ["git", r"--log=\Windows\System32\log.txt"],
    ]
    for cmd in unauthorized_args:
        with pytest.raises(ExecutionBlockedViolation) as exc_info:
            execution_guard.validate_command(cmd, cwd=sandbox_root)
        assert "unauthorized path" in str(exc_info.value)

    # Authorized in-repo path after '=' must succeed
    in_repo_file = sandbox_root / "output.txt"
    cmd_ok = ["git", f"--output={in_repo_file}"]
    sanitized = execution_guard.validate_command(cmd_ok, cwd=sandbox_root)
    assert sanitized[1] == f"--output={in_repo_file}"


def test_root_relative_path_argument_rejected(execution_guard, sandbox_root):
    """Test that root-relative paths starting with backslash or forward slash are blocked."""
    root_rel_commands = [
        ["git", r"\Windows\System32\drivers\etc\hosts"],
        ["git", "/Windows/System32/drivers/etc/hosts"],
        ["python", "-c", "import sys", r"\ProgramData\secret.dat"],
        ["python", "-c", "import sys", "/ProgramData/secret.dat"],
    ]
    for cmd in root_rel_commands:
        with pytest.raises(ExecutionBlockedViolation) as exc_info:
            execution_guard.validate_command(cmd, cwd=sandbox_root)
        assert "unauthorized path" in str(exc_info.value)
