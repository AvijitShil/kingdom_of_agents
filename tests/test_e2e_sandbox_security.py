"""
End-to-End Sandbox Security Test Suite (Features 1–5, Scenarios 2 & 6).

Implements 4-tier testing:
- Tier 1: Feature Coverage (≥5 tests per feature)
- Tier 2: Boundary & Corner Cases (Windows ADS, UNC, traversal, device names, shell operators, egress)
- Tier 3: Cross-Feature Interactions
- Tier 4: Real-World Application Scenarios (Scenario 2: Hostile Escape, Scenario 6: Boundary Expansion)
"""

import os
import sys
import socket
import pathlib
import secrets
import subprocess
import pytest
pytestmark = pytest.mark.skip_sandbox

from sandbox import (
    SecuritySandbox,
    SandboxContext,
    PathValidator,
    PathBoundary,
    Permission,
    ExecutionGuard,
    NetworkGuard,
    PasswordManager,
    PBKDF2_ITERATIONS,
    SALT_BYTES,
)
from sandbox.exceptions import (
    PathTraversalViolation,
    AlternateDataStreamViolation,
    DeviceNameViolation,
    ExecutionBlockedViolation,
    NetworkEgressBlocked,
    AuthenticationError,
    TamperProtectionViolation,
)


@pytest.fixture
def sandbox_env(isolated_project_dir, sandbox_admin_password):
    """Sets up a SecuritySandbox inside an isolated project directory."""
    sb = SecuritySandbox(
        project_root=isolated_project_dir,
        config_file=".sandbox_config.json",
        default_password=sandbox_admin_password,
    )
    return {
        "root": isolated_project_dir,
        "password": sandbox_admin_password,
        "sandbox": sb,
    }


# ============================================================================
# TIER 1: FEATURE COVERAGE (≥5 per feature across F1–F5)
# ============================================================================

# --- Feature 1: Windows Path Confinement ---

@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier1
def test_f1_read_valid_file_in_root(sandbox_env):
    """F1.1: Reading an existing valid file inside repository boundary succeeds."""
    sb = sandbox_env["sandbox"]
    content = sb.read_text("data.txt")
    assert content == "ISOLATED_DATA_SOURCE"


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier1
def test_f1_write_valid_file_in_subfolder(sandbox_env):
    """F1.2: Writing a file inside a repository subfolder (journal/) succeeds."""
    sb = sandbox_env["sandbox"]
    sb.write_text("journal/2026-11-22.md", "# Daily Journal Test")
    assert sb.read_text("journal/2026-11-22.md") == "# Daily Journal Test"


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier1
def test_f1_designated_read_only_boundary(sandbox_env, tmp_path):
    """F1.3: Accessing a designated read-only external boundary allows reads but blocks writes."""
    sb = sandbox_env["sandbox"]
    ext_dir = tmp_path / "designated_model"
    ext_dir.mkdir()
    (ext_dir / "weights.bin").write_text("MODEL_WEIGHTS", encoding="utf-8")

    sb.validator.boundaries.append(PathBoundary(ext_dir, Permission.READ))

    # Read succeeds
    read_p = sb.validator.validate_access(ext_dir / "weights.bin", Permission.READ)
    assert read_p.exists()

    # Write raises PathTraversalViolation
    with pytest.raises(PathTraversalViolation):
        sb.validator.validate_access(ext_dir / "weights.bin", Permission.WRITE)


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier1
def test_f1_list_directory_within_boundary(sandbox_env):
    """F1.4: Listing directory contents within boundary resolves correctly."""
    root = sandbox_env["root"]
    validator = sandbox_env["sandbox"].validator
    valid_p = validator.validate_access(root / "society", Permission.READ)
    assert valid_p.is_dir()


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier1
def test_f1_relative_path_normalization(sandbox_env):
    """F1.5: Relative paths with dot components normalize safely within boundary."""
    sb = sandbox_env["sandbox"]
    sb.write_text("journal/../data_copy.txt", "COPY_DATA")
    assert sb.read_text("data_copy.txt") == "COPY_DATA"


# --- Feature 2: Subprocess Execution Guard ---

@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier1
def test_f2_whitelisted_python_interpreter(sandbox_env):
    """F2.1: Executing whitelisted Python interpreter succeeds and returns output."""
    sb = sandbox_env["sandbox"]
    res = sb.run_command([sys.executable, "-c", "print('SUBPROCESS_OK')"])
    assert res.returncode == 0
    assert "SUBPROCESS_OK" in res.stdout


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier1
def test_f2_whitelisted_git_binary(sandbox_env):
    """F2.2: Executing whitelisted git binary succeeds."""
    sb = sandbox_env["sandbox"]
    res = sb.run_command(["git", "--version"])
    assert res.returncode == 0
    assert "git version" in res.stdout.lower()


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier1
def test_f2_confined_working_directory(sandbox_env):
    """F2.3: Subprocess executes confined to the repository root directory."""
    sb = sandbox_env["sandbox"]
    res = sb.run_command(
        [sys.executable, "-c", "import os; print(os.getcwd())"],
        cwd=sandbox_env["root"],
    )
    assert res.returncode == 0
    assert os.path.normcase(res.stdout.strip()) == os.path.normcase(str(sandbox_env["root"]))


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier1
def test_f2_safe_command_argument_parsing(sandbox_env):
    """F2.4: ExecutionGuard correctly handles safe argument lists."""
    guard = sandbox_env["sandbox"].execution
    sanitized = guard.validate_command([sys.executable, "-c", "x = 40 + 2; print(x)"])
    assert len(sanitized) == 3
    assert sanitized[0] == os.path.realpath(sys.executable)


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier1
def test_f2_command_returncode_capture(sandbox_env):
    """F2.5: Subprocess execution captures non-zero exit codes accurately."""
    sb = sandbox_env["sandbox"]
    res = sb.run_command([sys.executable, "-c", "import sys; sys.exit(7)"])
    assert res.returncode == 7


# --- Feature 3: Zero-Telemetry Socket Interception ---

@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier1
def test_f3_loopback_ipv4_permitted(clean_sandbox_hooks):
    """F3.1: NetworkGuard permits outbound connections to 127.0.0.1."""
    guard = NetworkGuard()
    assert guard.is_destination_allowed(("127.0.0.1", 8000)) is True


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier1
def test_f3_localhost_hostname_permitted(clean_sandbox_hooks):
    """F3.2: NetworkGuard permits outbound connections to localhost."""
    guard = NetworkGuard()
    assert guard.is_destination_allowed(("localhost", 8000)) is True


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier1
def test_f3_ipv6_loopback_permitted(clean_sandbox_hooks):
    """F3.3: NetworkGuard permits IPv6 loopback (::1)."""
    guard = NetworkGuard()
    assert guard.is_destination_allowed(("::1", 8000)) is True


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier1
def test_f3_loopback_string_address_permitted(clean_sandbox_hooks):
    """F3.4: NetworkGuard accepts loopback addresses represented as raw strings."""
    guard = NetworkGuard()
    assert guard.is_destination_allowed("127.0.0.1") is True


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier1
def test_f3_install_and_uninstall_lifecycle(clean_sandbox_hooks):
    """F3.5: NetworkGuard installs socket interceptor and restores original socket methods on uninstall."""
    orig_connect = socket.socket.connect
    guard = NetworkGuard()
    assert not guard.is_active

    guard.install()
    assert guard.is_active
    assert socket.socket.connect != orig_connect

    guard.uninstall()
    assert not guard.is_active
    assert socket.socket.connect == orig_connect


# --- Feature 4: Password Boundary Control ---

@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier1
def test_f4_default_admin_password_verification(sandbox_env):
    """F4.1: PasswordManager verifies default administrator password."""
    auth = sandbox_env["sandbox"].auth_manager
    assert auth.verify_password(sandbox_env["password"]) is True


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier1
def test_f4_change_admin_password(sandbox_env):
    """F4.2: PasswordManager allows updating administrator password with prior authentication."""
    auth = sandbox_env["sandbox"].auth_manager
    new_pw = "New_Secure_Admin_Password_2026!"
    auth.change_password(sandbox_env["password"], new_pw)
    assert auth.verify_password(new_pw) is True
    assert auth.verify_password(sandbox_env["password"]) is False


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier1
def test_f4_add_boundary_with_password(sandbox_env, tmp_path):
    """F4.3: Adding an allowed boundary requires and succeeds with valid master password."""
    sb = sandbox_env["sandbox"]
    new_boundary = tmp_path / "extra_allowed"
    new_boundary.mkdir()

    boundary = sb.add_allowed_path(new_boundary, "r", password=sandbox_env["password"])
    assert boundary.root_path == new_boundary.resolve()
    assert boundary.permission == Permission.READ


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier1
def test_f4_remove_boundary_with_password(sandbox_env, tmp_path):
    """F4.4: Removing an authorized boundary requires and succeeds with valid password."""
    sb = sandbox_env["sandbox"]
    new_boundary = tmp_path / "removable_boundary"
    new_boundary.mkdir()

    sb.add_allowed_path(new_boundary, "r", password=sandbox_env["password"])
    sb.remove_allowed_path(new_boundary, password=sandbox_env["password"])
    assert not any(b.root_path == new_boundary.resolve() for b in sb.validator.boundaries)


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier1
def test_f4_pbkdf2_metadata_validation(sandbox_env):
    """F4.5: PasswordManager persists PBKDF2 iterations and 32-byte cryptographic salt."""
    auth = sandbox_env["sandbox"].auth_manager
    assert auth._iterations == PBKDF2_ITERATIONS
    assert len(auth._salt) == SALT_BYTES
    assert len(auth._hash) == 32


# --- Feature 5: Sandbox Runtime Hook Context ---

@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier1
def test_f5_context_manager_lifecycle(sandbox_env):
    """F5.1: SandboxContext activates runtime hooks on enter and cleanly restores on exit."""
    sb = sandbox_env["sandbox"]
    ctx = sb.get_context()
    assert not ctx.is_active

    with ctx:
        assert ctx.is_active

    assert not ctx.is_active


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier1
def test_f5_context_intercepts_builtin_open_read(sandbox_env):
    """F5.2: SandboxContext intercepts builtins.open for valid repository reads."""
    sb = sandbox_env["sandbox"]
    with sb.get_context():
        with open(sandbox_env["root"] / "data.txt", "r", encoding="utf-8") as f:
            content = f.read()
    assert content == "ISOLATED_DATA_SOURCE"


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier1
def test_f5_context_intercepts_builtin_open_write(sandbox_env):
    """F5.3: SandboxContext intercepts builtins.open for repository writes."""
    sb = sandbox_env["sandbox"]
    target = sandbox_env["root"] / "journal" / "hook_test.txt"
    with sb.get_context():
        with open(target, "w", encoding="utf-8") as f:
            f.write("HOOK_WRITE_SUCCESS")

    assert target.read_text(encoding="utf-8") == "HOOK_WRITE_SUCCESS"


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier1
def test_f5_context_intercepts_pathlib_io(sandbox_env):
    """F5.4: SandboxContext intercepts pathlib.Path file operations."""
    sb = sandbox_env["sandbox"]
    target = sandbox_env["root"] / "data.txt"
    with sb.get_context():
        assert target.read_text(encoding="utf-8") == "ISOLATED_DATA_SOURCE"


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier1
def test_f5_context_intercepts_subprocess_popen(sandbox_env):
    """F5.5: SandboxContext intercepts subprocess.Popen and validates execution."""
    sb = sandbox_env["sandbox"]
    with sb.get_context():
        proc = subprocess.Popen(
            [sys.executable, "-c", "print('POPEN_SUCCESS')"],
            cwd=sandbox_env["root"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        out, _ = proc.communicate()
    assert "POPEN_SUCCESS" in out


# ============================================================================
# TIER 2: BOUNDARY & CORNER CASES (Adversarial Edge Cases)
# ============================================================================

# --- Traversal & Windows Specific Vectors ---

@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier2
def test_boundary_parent_directory_traversal(sandbox_env):
    """F1 Tier 2: Path traversal variations (..\\..\\Windows, ../../etc/passwd) rejected."""
    validator = sandbox_env["sandbox"].validator
    for escape in [
        "..\\..\\Windows\\System32\\cmd.exe",
        "../../../../etc/passwd",
        "folder/../../../Windows",
        "..\\..\\..\\..\\Windows",
    ]:
        with pytest.raises(PathTraversalViolation):
            validator.validate_access(escape, Permission.READ)


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier2
def test_boundary_mixed_slashes_traversal(sandbox_env):
    """F1 Tier 2: Mixed slash traversal sequences rejected."""
    validator = sandbox_env["sandbox"].validator
    for escape in [
        "..//..\\Windows",
        "society/..\\//..\\..//System32",
        "..\\//..//Windows",
    ]:
        with pytest.raises(PathTraversalViolation):
            validator.validate_access(escape, Permission.READ)


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier2
def test_boundary_windows_8_3_aliases(sandbox_env):
    """F1 Tier 2: Windows 8.3 short name aliases are canonicalized and outside traversal is blocked."""
    validator = sandbox_env["sandbox"].validator
    
    # 1. Traversal outside sandbox using 8.3 short names is blocked
    for short_path in [
        r"C:\PROGRA~1",
        r"C:\PROGRA~2",
        r"..\..\PROGRA~1",
        r"C:\RUNNIN~1\test.txt",
    ]:
        with pytest.raises(PathTraversalViolation):
            validator.validate_access(short_path, Permission.READ)

    # 2. Verify 8.3 short name expansion genuinely functions and fails if circumvented
    prog_files_short = pathlib.Path(r"C:\PROGRA~1")
    if prog_files_short.exists():
        expanded = validator.expand_long_path(prog_files_short)
        expected = pathlib.Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
        assert expanded == expected, (
            f"8.3 expansion circumvented: '{expanded}' != '{expected}'"
        )



@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier2
def test_boundary_alternate_data_streams(sandbox_env):
    """F1 Tier 2: NTFS Alternate Data Streams (colon injection) rejected."""
    validator = sandbox_env["sandbox"].validator
    for ads in [
        "README.md:hidden_stream",
        "data.txt:$DATA",
        "journal/log.txt:secret",
    ]:
        with pytest.raises(AlternateDataStreamViolation):
            validator.validate_access(ads, Permission.WRITE)


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier2
def test_boundary_unc_network_paths(sandbox_env):
    """F1 Tier 2: UNC network paths rejected as traversal attacks."""
    validator = sandbox_env["sandbox"].validator
    for unc in [
        r"\\attacker.com\share\loot.txt",
        r"\\127.0.0.1\c$\Windows\System32",
        "//attacker.com/malicious/payload",
    ]:
        with pytest.raises(PathTraversalViolation):
            validator.validate_access(unc, Permission.READ)


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier2
def test_boundary_reserved_device_names(sandbox_env):
    """F1 Tier 2: Windows reserved device names (CON, PRN, AUX, NUL, COM1, LPT1) rejected."""
    validator = sandbox_env["sandbox"].validator
    for dev in ["CON", "PRN", "AUX", "NUL", "COM1", "COM9", "LPT1", "lpt2", "aux.txt"]:
        with pytest.raises(DeviceNameViolation):
            validator.validate_access(dev, Permission.WRITE)


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier2
def test_boundary_tamper_protection_system_files(sandbox_env):
    """F1 Tier 2: Protected system files (.sandbox_config.json, .git/config) protected against modification."""
    validator = sandbox_env["sandbox"].validator
    for protected in [".sandbox_config.json", ".git/config", ".git/credentials"]:
        with pytest.raises(TamperProtectionViolation):
            validator.validate_access(protected, Permission.WRITE)


# --- Execution Guard Evasion Vectors ---

@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier2
def test_boundary_shell_injection_semicolon(sandbox_env):
    """F2 Tier 2: Command chaining operator ';' blocked."""
    guard = sandbox_env["sandbox"].execution
    with pytest.raises(ExecutionBlockedViolation):
        guard.validate_command("python -c 'print(1)'; calc.exe")


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier2
def test_boundary_shell_injection_ampersand(sandbox_env):
    """F2 Tier 2: Command chaining operator '&' blocked."""
    guard = sandbox_env["sandbox"].execution
    with pytest.raises(ExecutionBlockedViolation):
        guard.validate_command("python -c 'print(1)' & dir")


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier2
def test_boundary_shell_redirection_pipe(sandbox_env):
    """F2 Tier 2: Pipeline operator '|' and redirection '>' blocked."""
    guard = sandbox_env["sandbox"].execution
    with pytest.raises(ExecutionBlockedViolation):
        guard.validate_command("python -c 'print(1)' | whoami")

    with pytest.raises(ExecutionBlockedViolation):
        guard.validate_command("python -c 'print(1)' > leaked.txt")


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier2
def test_boundary_unapproved_binaries(sandbox_env):
    """F2 Tier 2: Unapproved system executables (cmd, powershell, calc, curl) blocked."""
    guard = sandbox_env["sandbox"].execution
    for binary in ["cmd.exe", "powershell.exe", "calc.exe", "curl.exe", "bash"]:
        with pytest.raises(ExecutionBlockedViolation):
            guard.validate_command([binary, "-c", "echo 1"])


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier2
def test_boundary_disallowed_working_directory(sandbox_env, tmp_path):
    """F2 Tier 2: Process execution with cwd outside sandbox boundaries blocked."""
    guard = sandbox_env["sandbox"].execution
    external = tmp_path / "outside_cwd"
    external.mkdir()
    with pytest.raises(ExecutionBlockedViolation):
        guard.validate_command([sys.executable, "-c", "print(1)"], cwd=external)


# --- Zero-Telemetry Network Egress Evasion Vectors ---

@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier2
def test_boundary_external_wan_tcp_blocked(clean_sandbox_hooks):
    """F3 Tier 2: Outbound TCP socket to public IP (8.8.8.8:53) raises NetworkEgressBlocked."""
    guard = NetworkGuard()
    guard.install()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        with pytest.raises(NetworkEgressBlocked) as exc_info:
            sock.connect(("8.8.8.8", 53))
        assert "Outbound network egress blocked" in str(exc_info.value)
    finally:
        guard.uninstall()


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier2
def test_boundary_external_wan_hostname_blocked(clean_sandbox_hooks):
    """F3 Tier 2: Outbound socket to public hostname (api.github.com:443) raises NetworkEgressBlocked."""
    guard = NetworkGuard()
    guard.install()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        with pytest.raises(NetworkEgressBlocked) as exc_info:
            sock.connect(("api.github.com", 443))
        assert "Outbound network egress blocked" in str(exc_info.value)
    finally:
        guard.uninstall()


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier2
def test_boundary_udp_sendto_external_blocked(clean_sandbox_hooks):
    """F3 Tier 2: Outbound UDP sendto to external destination raises NetworkEgressBlocked."""
    guard = NetworkGuard()
    guard.install()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        with pytest.raises(NetworkEgressBlocked) as exc_info:
            sock.sendto(b"LEAK_DATA", ("1.1.1.1", 53))
        assert "Outbound UDP transmission blocked" in str(exc_info.value)
    finally:
        guard.uninstall()


# --- Password Boundary & Authentication Evasion ---

@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier2
def test_boundary_auth_incorrect_password_rejected(sandbox_env):
    """F4 Tier 2: Incorrect password raises AuthenticationError."""
    auth = sandbox_env["sandbox"].auth_manager
    with pytest.raises(AuthenticationError):
        auth.authenticate_and_authorize("Incorrect_Password_1234!")


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier2
def test_boundary_auth_short_password_rejected(sandbox_env):
    """F4 Tier 2: Password shorter than 12 characters rejected upon update."""
    auth = sandbox_env["sandbox"].auth_manager
    with pytest.raises(ValueError):
        auth.change_password(sandbox_env["password"], "short")


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier2
def test_boundary_auth_constant_time_verification(sandbox_env):
    """F4 Tier 2: Password verification uses constant-time comparison."""
    auth = sandbox_env["sandbox"].auth_manager
    # Ensure invalid characters or partial match fails
    assert auth.verify_password(sandbox_env["password"][:-1]) is False
    assert auth.verify_password("") is False


# ============================================================================
# TIER 3: CROSS-FEATURE INTERACTIONS (Pairwise combinations)
# ============================================================================

@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier3
def test_cross_sandbox_context_with_file_and_network(sandbox_env):
    """F1 + F3 + F5: Inside SandboxContext, repo file access succeeds while WAN network egress fails."""
    sb = sandbox_env["sandbox"]
    with sb.get_context():
        # In-repo file read and write succeed
        with open(sandbox_env["root"] / "data.txt", "r", encoding="utf-8") as f:
            data = f.read()
        assert data == "ISOLATED_DATA_SOURCE"

        # Outbound WAN connection blocked
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        with pytest.raises(NetworkEgressBlocked):
            sock.connect(("8.8.8.8", 80))


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier3
def test_cross_boundary_expansion_under_auth(sandbox_env, tmp_path):
    """F1 + F4 + F5: Boundary expansion with password allows file operations within expanded path."""
    sb = sandbox_env["sandbox"]
    new_dir = tmp_path / "model_weights_boundary"
    new_dir.mkdir()
    (new_dir / "weights.bin").write_text("WEIGHTS_DATA", encoding="utf-8")

    # Before authorization, access is blocked
    with pytest.raises(PathTraversalViolation):
        sb.validator.validate_access(new_dir / "weights.bin", Permission.READ)

    # Authorize boundary with password
    sb.add_allowed_path(new_dir, "r", password=sandbox_env["password"])

    # Within SandboxContext, reading from newly authorized directory succeeds
    with sb.get_context():
        with open(new_dir / "weights.bin", "r", encoding="utf-8") as f:
            content = f.read()
        assert content == "WEIGHTS_DATA"

    # Revoke boundary with password
    sb.remove_allowed_path(new_dir, password=sandbox_env["password"])

    # Subsequent access is blocked
    with pytest.raises(PathTraversalViolation):
        sb.validator.validate_access(new_dir / "weights.bin", Permission.READ)


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier3
def test_cross_sandbox_context_subprocess_and_path(sandbox_env, tmp_path):
    """F1 + F2 + F5: Inside SandboxContext, subprocess attempts to violate path boundaries are blocked."""
    sb = sandbox_env["sandbox"]
    ext_dir = tmp_path / "unauthorized_dir"
    ext_dir.mkdir()

    with sb.get_context():
        # Blocked: spawning process with unauthorized cwd
        with pytest.raises(ExecutionBlockedViolation):
            subprocess.Popen(
                [sys.executable, "-c", "print(1)"],
                cwd=ext_dir,
            )

        # Blocked: spawning unapproved binary
        with pytest.raises(ExecutionBlockedViolation):
            subprocess.Popen(
                ["calc.exe"],
                cwd=sandbox_env["root"],
            )


# ============================================================================
# TIER 4: REAL-WORLD APPLICATION SCENARIOS (Scenarios 2 & 6)
# ============================================================================

@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier4
def test_scenario_2_hostile_sandbox_escape_and_exfiltration(sandbox_env, tmp_path):
    """
    Scenario 2: Hostile Sandbox Escape & Exfiltration Simulation.
    An adversarial agent script attempts multi-vector evasion:
    1. Parent traversal to host temp / system directories -> blocked.
    2. NTFS Alternate Data Stream stealth write -> blocked.
    3. Chained command injection to spawn shell or unapproved tool -> blocked.
    4. Outbound socket connection to remote exfiltration server -> blocked.
    5. Tampering with .sandbox_config.json security settings -> blocked.
    Verifies total neutralization across all vectors.
    """
    sb = sandbox_env["sandbox"]
    root = sandbox_env["root"]
    host_target = tmp_path / "host_sensitive"
    host_target.mkdir()
    (host_target / "host_passwords.txt").write_text("HOST_PASSWORDS", encoding="utf-8")

    with sb.get_context():
        # Vector 1: Host filesystem traversal
        with pytest.raises(PathTraversalViolation):
            with open(host_target / "host_passwords.txt", "r") as f:
                f.read()

        # Vector 2: ADS injection stealth write
        with pytest.raises(AlternateDataStreamViolation):
            with open(root / "data.txt:payload.exe", "w") as f:
                f.write("MALICIOUS_PAYLOAD")

        # Vector 3: Command injection via shell chaining
        with pytest.raises(ExecutionBlockedViolation):
            subprocess.Popen(
                f"{sys.executable} -c 'print(1)' & calc.exe",
                cwd=root,
            )

        # Vector 4: Exfiltration via outbound socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        with pytest.raises(NetworkEgressBlocked):
            sock.connect(("203.0.113.195", 443))

        # Vector 5: Tamper with security configuration
        with pytest.raises(TamperProtectionViolation):
            with open(root / ".sandbox_config.json", "w") as f:
                f.write('{"tampered": true}')


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier4
def test_scenario_6_authorized_boundary_expansion(sandbox_env, tmp_path):
    """
    Scenario 6: Authorized Boundary Expansion with Password Reconfiguration.
    Verifies that an administrator can securely expand boundaries:
    1. Unauthorized modification attempt fails.
    2. Master password authorizes access to an external model repository.
    3. Sandboxed runtime can read model files from the authorized path.
    4. Sandboxed runtime is blocked from writing to read-only model path.
    5. Admin revokes permission, returning to initial strict confinement.
    """
    sb = sandbox_env["sandbox"]
    model_cache = tmp_path / "gemma_model_cache"
    model_cache.mkdir()
    (model_cache / "model.safetensors").write_text("TENSOR_WEIGHTS", encoding="utf-8")

    # Step 1: Unauthorized boundary expansion rejected
    with pytest.raises(AuthenticationError):
        sb.add_allowed_path(model_cache, "r", password="WRONG_PASSWORD")

    # Step 2: Authorized expansion with master password
    sb.add_allowed_path(model_cache, "r", password=sandbox_env["password"])

    # Step 3: Sandboxed runtime reads from new boundary
    with sb.get_context():
        with open(model_cache / "model.safetensors", "r", encoding="utf-8") as f:
            weights = f.read()
        assert weights == "TENSOR_WEIGHTS"

        # Step 4: Write to read-only boundary is blocked
        with pytest.raises(PathTraversalViolation):
            with open(model_cache / "hack.txt", "w", encoding="utf-8") as f:
                f.write("CORRUPT")

    # Step 5: Boundary revoked
    sb.remove_allowed_path(model_cache, password=sandbox_env["password"])
    with pytest.raises(PathTraversalViolation):
        sb.validator.validate_access(model_cache / "model.safetensors", Permission.READ)
