"""
Tier 5 Adversarial Coverage Hardening Test Suite for kingdom_of_agents.

Integrates 52 adversarial stress tests across:
- Sandbox Subsystem (14 tests from Challenger 1):
  PathValidator bitwise flags, Windows console devices (CONIN$, CONOUT$, CLOCK$),
  directory junctions, NT namespace paths, Unicode normalization,
  subprocess environment variable leakage (PYTHONPATH, PYTHONHOME),
  argument path scanning, reverse DNS interception (socket.gethostbyaddr),
  UDP sendto positional flags, IPv6 destinations, concurrency isolation,
  nested context resilience, and PasswordManager brute-force/corrupted config recovery.
- Knowledge Base Subsystem (16 tests from Challenger 2):
  IdeologicalProfile NaN/Inf validation, tolerance precision boundaries, negative weight rejection,
  empty/invalid axioms, required/extraneous utility keys, CorpusLoader malformed delimiter/YAML handling,
  non-dict structures, and CorpusRetriever adversarial search/tokenization.
- Agent Evolution Subsystem (22 tests from Challenger 2):
  FitnessMetrics edge cases, ledger clamping/fallbacks, CategorySwitchManager hysteresis barrier,
  NaN evasion rejection, cooldown boundaries/underflow, probation degradation epsilon & floor rollback,
  two-tick confirmation lifecycle, budget exhaustion, RecursiveReflectionEngine zero-variance regret,
  regret bounds, sliding window bounds, LLM exception fallback, PromptOptimizer max_reflections <= 0,
  ActionString dual-type compatibility, and 50-agent multi-tick society stress simulation.
"""

import io
import os
import sys
import json
import math
import socket
import builtins
import pathlib
import secrets
import threading
import subprocess
import pytest
import _winapi
from typing import Dict, Any, List, Optional
from pydantic import ValidationError

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
from knowledge_base.models import IdeologicalProfile, REQUIRED_UTILITY_KEYS
from knowledge_base.loader import CorpusLoader
from knowledge_base.retriever import CorpusRetriever
from evolution.models import ReflectionRecord, SwitchEvent
from evolution.fitness import FitnessMetrics, FitnessEvaluator, compute_composite_fitness
from evolution.switcher import CategorySwitchManager
from evolution.reflection import RecursiveReflectionEngine
from evolution.prompt_optimizer import PromptOptimizer
from evolution.agent import EvolutionaryAgent, ActionString


# Pristine unpatched references
_ORIG_BUILTIN_OPEN = builtins.open
_ORIG_IO_OPEN = io.open
_ORIG_SUBPROCESS_POPEN = subprocess.Popen
_ORIG_SOCKET_CONNECT = socket.socket.connect
_ORIG_SOCKET_SENDTO = socket.socket.sendto
_ORIG_GETHOSTBYADDR = socket.gethostbyaddr


@pytest.fixture(autouse=True)
def clean_sandbox_hooks():
    """Guarantee pristine builtins, subprocess, and socket references before and after every test."""
    builtins.open = _ORIG_BUILTIN_OPEN
    io.open = _ORIG_IO_OPEN
    subprocess.Popen = _ORIG_SUBPROCESS_POPEN
    socket.socket.connect = _ORIG_SOCKET_CONNECT
    socket.socket.sendto = _ORIG_SOCKET_SENDTO
    socket.gethostbyaddr = _ORIG_GETHOSTBYADDR
    SandboxContext._global_depth = 0
    SandboxContext._active_contexts.clear()
    NetworkGuard._global_depth = 0
    NetworkGuard._active_guards.clear()
    yield
    builtins.open = _ORIG_BUILTIN_OPEN
    io.open = _ORIG_IO_OPEN
    subprocess.Popen = _ORIG_SUBPROCESS_POPEN
    socket.socket.connect = _ORIG_SOCKET_CONNECT
    socket.socket.sendto = _ORIG_SOCKET_SENDTO
    socket.gethostbyaddr = _ORIG_GETHOSTBYADDR
    SandboxContext._global_depth = 0
    SandboxContext._active_contexts.clear()
    NetworkGuard._global_depth = 0
    NetworkGuard._active_guards.clear()


@pytest.fixture
def sandbox_admin_password() -> str:
    """Master administrator password for sandbox boundary modifications."""
    return "EON_Kingdom_Admin_2026!"


@pytest.fixture
def isolated_project_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    """Creates an isolated test workspace mimicking kingdom_of_agents directory structure."""
    proj = tmp_path / "kingdom_of_agents_isolated"
    proj.mkdir(parents=True, exist_ok=True)
    (proj / "journal").mkdir(parents=True, exist_ok=True)
    (proj / "knowledge_base").mkdir(parents=True, exist_ok=True)
    (proj / "society").mkdir(parents=True, exist_ok=True)
    (proj / "agents").mkdir(parents=True, exist_ok=True)
    (proj / "scripts").mkdir(parents=True, exist_ok=True)
    (proj / "data.txt").write_text("ISOLATED_DATA_SOURCE", encoding="utf-8")
    (proj / "README.md").write_text("# Isolated Kingdom Workspace\n", encoding="utf-8")
    (proj / ".gitignore").write_text("*.pyc\n__pycache__/\n", encoding="utf-8")
    (proj / ".sandbox_config.json").write_text("{}", encoding="utf-8")
    return proj


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
# TIER 5: ADVERSARIAL HARDENING — PATH VALIDATOR & BOUNDARY CONFINEMENT
# ============================================================================

@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.hardening
def test_tier5_adversarial_tamper_protection_bitwise_flag_combinations(sandbox_env):
    """
    Tier 5 Adversarial: Bitwise Flag Combinations on Protected Files.
    Validates that bitwise combinations involving Permission.WRITE (e.g. WRITE | EXECUTE)
    strictly trigger TamperProtectionViolation for all protected system files:
    .sandbox_config.json, .git/config, .git/credentials.
    Anti-regression check: Enforces that flag membership uses bitwise masking (&)
    rather than a restrictive tuple-membership check.
    """
    validator = sandbox_env["sandbox"].validator
    flag_combinations = [
        Permission.WRITE | Permission.EXECUTE,
        Permission.WRITE | Permission.READ,
        Permission.ALL,
        Permission.WRITE,
    ]
    protected_targets = [
        ".sandbox_config.json",
        ".git/config",
        ".git/credentials",
    ]

    for target in protected_targets:
        for perm in flag_combinations:
            with pytest.raises(TamperProtectionViolation) as exc_info:
                validator.validate_access(target, perm)
            assert "Modifying system-protected file" in str(exc_info.value)


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.hardening
def test_tier5_adversarial_reserved_device_names_extended_console_handles(sandbox_env):
    """
    Tier 5 Adversarial: Windows Console Device Handles (CONIN$, CONOUT$, CLOCK$).
    Validates that special Windows console device handles and DOS clock devices
    (CONIN$, CONOUT$, CLOCK$) are blocked with DeviceNameViolation across case variations
    and with arbitrary file extensions or subdirectory nesting.
    """
    validator = sandbox_env["sandbox"].validator
    special_devices = [
        "CONIN$",
        "CONOUT$",
        "conin$",
        "conout$",
        "CONIN$.txt",
        "CONOUT$.log",
        "CLOCK$",
        "clock$.dat",
        "journal/CONIN$",
        "society/CONOUT$.bin",
    ]

    for dev in special_devices:
        with pytest.raises(DeviceNameViolation) as exc_info:
            validator.validate_access(dev, Permission.READ)
        assert "reserved device name" in str(exc_info.value).lower()


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.hardening
def test_tier5_adversarial_junction_nonexistent_write_target_resolution(sandbox_env, tmp_path):
    """
    Tier 5 Adversarial: Directory Junction to Non-Existent Write Target Escape.
    Validates that creating an NTFS directory junction inside the repository pointing
    to an outside directory does not permit writing to new, non-existent files through the junction.
    The validator must resolve the junction ancestor and block with PathTraversalViolation.
    """
    sb = sandbox_env["sandbox"]
    repo_root = sandbox_env["root"]
    outside_dir = tmp_path / "outside_junction_target"
    outside_dir.mkdir()

    junction_in_repo = repo_root / "society" / "junction_escape"
    _winapi.CreateJunction(str(outside_dir), str(junction_in_repo))

    try:
        # Non-existent target inside junction
        sneaky_write_target = junction_in_repo / "unauthorized_output.txt"
        with pytest.raises(PathTraversalViolation):
            sb.validator.validate_access(sneaky_write_target, Permission.WRITE)

        # Inside SandboxContext, attempting to open write target must also fail
        with sb.get_context():
            with pytest.raises(PathTraversalViolation):
                with open(sneaky_write_target, "w", encoding="utf-8") as f:
                    f.write("SHOULD_NEVER_BE_WRITTEN")
        assert not (outside_dir / "unauthorized_output.txt").exists()
    finally:
        # Clean up junction
        try:
            _winapi.UnlinkJunction(str(junction_in_repo))
        except Exception:
            pass


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.hardening
def test_tier5_adversarial_drive_relative_and_nt_namespace_paths(sandbox_env):
    """
    Tier 5 Adversarial: Windows Drive-Relative and NT Object Manager Paths.
    Tests rejection or safe resolution of:
    1. NT object manager namespace (\\??\\C:\\...)
    2. Physical and virtual device namespaces (\\\\.\\PhysicalDrive0, \\\\?\\Volume{...})
    3. Drive-relative syntax (C:file.txt)
    """
    validator = sandbox_env["sandbox"].validator
    forbidden_namespace_paths = [
        r"\??\C:\Windows\System32\cmd.exe",
        r"\??\C:\autoexec.bat",
        r"\\.\PhysicalDrive0",
        r"\\.\GLOBALROOT\Device\Harddisk0",
        r"\\?\Volume{00000000-0000-0000-0000-000000000000}\Windows",
    ]

    for p in forbidden_namespace_paths:
        with pytest.raises((PathTraversalViolation, AlternateDataStreamViolation)):
            validator.validate_access(p, Permission.READ)


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.hardening
def test_tier5_adversarial_unicode_filenames_and_normalization(sandbox_env):
    """
    Tier 5 Adversarial: Non-ASCII UTF-8, Diacritics, and Emoji File Names.
    Validates that filenames containing combining characters, umlauts/accents,
    and Unicode emojis reside correctly within the repository boundary and are
    properly validated without false-positive traversals or security bypasses.
    """
    sb = sandbox_env["sandbox"]
    unicode_files = [
        ("journal/📝_agent_log_2026.md", "EMOJI_LOG_DATA"),
        ("society/café_constitution.txt", "ACCENTED_DATA"),
        ("agents/über_agent_strategy.json", '{"name": "über"}'),
    ]

    with sb.get_context():
        for rel_path, data in unicode_files:
            target = sandbox_env["root"] / rel_path
            # Write under sandbox
            with open(target, "w", encoding="utf-8") as f:
                f.write(data)
            # Read under sandbox
            with open(target, "r", encoding="utf-8") as f:
                assert f.read() == data
            assert target.exists()


# ============================================================================
# TIER 5: ADVERSARIAL HARDENING — SUBPROCESS CONFINEMENT & EXECUTION GUARD
# ============================================================================

@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.hardening
def test_tier5_adversarial_subprocess_environment_variable_leakage(sandbox_env, tmp_path):
    """
    Tier 5 Adversarial: Subprocess Environment Variable Hijacking (PYTHONPATH / PYTHONHOME).
    Tests that an adversarial agent cannot hijack Python module resolution or execute
    unauthorized external code by passing PYTHONPATH, PYTHONHOME, or PYTHONSTARTUP pointing
    outside the sandbox. ExecutionGuard must detect unauthorized external directory references
    in sensitive environment variables and raise ExecutionBlockedViolation.
    """
    guard = sandbox_env["sandbox"].execution
    outside_lib = tmp_path / "outside_lib"
    outside_lib.mkdir()
    (outside_lib / "malicious_payload.py").write_text("INJECTED = True\n", encoding="utf-8")

    # 1. Hostile PYTHONPATH pointing outside sandbox
    hostile_env_pythonpath = os.environ.copy()
    hostile_env_pythonpath["PYTHONPATH"] = str(outside_lib)

    with pytest.raises(ExecutionBlockedViolation) as exc_info:
        guard.run(
            [sys.executable, "-c", "import malicious_payload; print(malicious_payload.INJECTED)"],
            cwd=sandbox_env["root"],
            env=hostile_env_pythonpath,
        )
    assert "environment" in str(exc_info.value).lower() or "unauthorized path" in str(exc_info.value).lower()

    # 2. Hostile PYTHONHOME pointing outside sandbox
    hostile_env_home = os.environ.copy()
    hostile_env_home["PYTHONHOME"] = str(outside_lib)

    with pytest.raises(ExecutionBlockedViolation):
        guard.run(
            [sys.executable, "-c", "print(1)"],
            cwd=sandbox_env["root"],
            env=hostile_env_home,
        )


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.hardening
def test_tier5_adversarial_subprocess_argument_path_evasion(sandbox_env):
    """
    Tier 5 Adversarial: Subprocess Argument Path Scanning Evasion.
    Validates that sneaky path parameters in Git or Python command lines targeting
    system files or relative escapes outside the sandbox are caught:
    - --exec-path pointing outside sandbox
    - -C / --work-tree escapes
    - Null-byte injections in arguments
    """
    guard = sandbox_env["sandbox"].execution
    evasion_commands = [
        ["git", r"--exec-path=C:\Windows\System32", "status"],
        ["git", "-C", r"..\outside_dir", "status"],
        ["git", r"--work-tree=C:\Windows", "status"],
        ["python", "-c", "import sys\0evil; print(1)"],
    ]

    for cmd in evasion_commands:
        with pytest.raises((ExecutionBlockedViolation, PathTraversalViolation)):
            guard.validate_command(cmd, cwd=sandbox_env["root"])


# ============================================================================
# TIER 5: ADVERSARIAL HARDENING — NETWORK EGRESS & ZERO-TELEMETRY GUARD
# ============================================================================

@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.hardening
def test_tier5_adversarial_network_guard_reverse_dns_blocked(clean_sandbox_hooks):
    """
    Tier 5 Adversarial: Reverse DNS Query Interception (socket.gethostbyaddr).
    Validates that reverse DNS queries via socket.gethostbyaddr targeting external WAN IPs
    (e.g. 8.8.8.8, 1.1.1.1) are intercepted and raise NetworkEgressBlocked, preventing
    outbound telemetry and DNS IP leakage.
    """
    guard = NetworkGuard()
    guard.install()
    try:
        external_ips = ["8.8.8.8", "1.1.1.1", "208.67.222.222"]
        for ip in external_ips:
            with pytest.raises(NetworkEgressBlocked) as exc_info:
                socket.gethostbyaddr(ip)
            assert "Outbound DNS resolution blocked" in str(exc_info.value) or "blocked" in str(exc_info.value).lower()

        # Loopback reverse DNS resolution is permitted
        loopback_addr = socket.gethostbyaddr("127.0.0.1")
        assert len(loopback_addr) >= 1
    finally:
        guard.uninstall()


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.hardening
def test_tier5_adversarial_network_guard_udp_sendto_positional_flags(clean_sandbox_hooks):
    """
    Tier 5 Adversarial: UDP socket.sendto with Positional Integer Flags.
    Validates that safe_sendto correctly handles the 3-argument signature:
    sendto(data, flags, address) where flags is a positional integer and address is index 2.
    External WAN destination must raise NetworkEgressBlocked; loopback must succeed.
    """
    guard = NetworkGuard()
    guard.install()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # 1. Outbound WAN with flags=0
            with pytest.raises(NetworkEgressBlocked) as exc_info:
                sock.sendto(b"TELEMETRY_PAYLOAD", 0, ("8.8.8.8", 53))
            assert "Outbound UDP transmission blocked" in str(exc_info.value)

            # 2. Local loopback with flags=0
            loopback_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            loopback_server.bind(("127.0.0.1", 0))
            port = loopback_server.getsockname()[1]
            try:
                sent = sock.sendto(b"LOCAL_PING", 0, ("127.0.0.1", port))
                assert sent == len(b"LOCAL_PING")
            finally:
                loopback_server.close()
        finally:
            sock.close()
    finally:
        guard.uninstall()


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.hardening
def test_tier5_adversarial_network_guard_ipv6_destinations(clean_sandbox_hooks):
    """
    Tier 5 Adversarial: IPv6 WAN Destination Blocking vs Loopback Preservation.
    Validates that IPv6 WAN destinations ([2001:4860:4860::8888], [2606:4700:4700::1111])
    are blocked with NetworkEgressBlocked, while IPv6 loopbacks (::1, [::1], ::ffff:127.0.0.1)
    are permitted.
    """
    guard = NetworkGuard()
    # Destination check
    assert guard.is_destination_allowed(("::1", 8000)) is True
    assert guard.is_destination_allowed(("[::1]", 8000)) is True
    assert guard.is_destination_allowed(("::ffff:127.0.0.1", 8000)) is True
    assert guard.is_destination_allowed(("2001:4860:4860::8888", 53)) is False
    assert guard.is_destination_allowed(("[2001:4860:4860::8888]", 53)) is False

    guard.install()
    try:
        with pytest.raises(NetworkEgressBlocked):
            socket.getaddrinfo("2001:4860:4860::8888", 53)
    finally:
        guard.uninstall()


# ============================================================================
# TIER 5: ADVERSARIAL HARDENING — RUNTIME CONTEXT & CONCURRENCY
# ============================================================================

@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.hardening
def test_tier5_adversarial_high_concurrency_multi_tenant_isolation(tmp_path):
    """
    Tier 5 Adversarial: High-Concurrency Multi-Tenant SandboxContext Isolation.
    Spawns 10 concurrent threads across two completely isolated SecuritySandbox instances
    (Tenant A with repo_a, Tenant B with repo_b).
    Verifies that:
    1. Each thread correctly reads/writes within its own assigned sandbox.
    2. Attempting to cross boundaries into the other tenant's repository strictly raises
       PathTraversalViolation across all concurrent threads.
    3. Thread-local stacks prevent any state corruption or boundary bleeding.
    """
    repo_a = tmp_path / "tenant_a"
    repo_a.mkdir()
    (repo_a / "tenant_data.txt").write_text("TENANT_A_CONFIDENTIAL", encoding="utf-8")

    repo_b = tmp_path / "tenant_b"
    repo_b.mkdir()
    (repo_b / "tenant_data.txt").write_text("TENANT_B_CONFIDENTIAL", encoding="utf-8")

    sb_a = SecuritySandbox(project_root=repo_a, default_password="Tenant_A_Password_2026!")
    sb_b = SecuritySandbox(project_root=repo_b, default_password="Tenant_B_Password_2026!")

    thread_errors = []

    def tenant_worker(thread_idx: int, is_tenant_a: bool):
        try:
            my_sb = sb_a if is_tenant_a else sb_b
            my_root = repo_a if is_tenant_a else repo_b
            other_root = repo_b if is_tenant_a else repo_a
            expected_content = "TENANT_A_CONFIDENTIAL" if is_tenant_a else "TENANT_B_CONFIDENTIAL"

            with my_sb.get_context():
                # Legitimate read within own tenant
                with open(my_root / "tenant_data.txt", "r", encoding="utf-8") as f:
                    content = f.read()
                if content != expected_content:
                    thread_errors.append(f"Thread {thread_idx}: read mismatch: {content}")

                # Illegal cross-tenant read MUST fail
                cross_failed = False
                try:
                    with open(other_root / "tenant_data.txt", "r", encoding="utf-8") as f:
                        f.read()
                    cross_failed = True
                except PathTraversalViolation:
                    pass
                if cross_failed:
                    thread_errors.append(f"Thread {thread_idx}: cross-tenant isolation breached!")

                # Legitimate write within own tenant
                out_file = my_root / f"worker_{thread_idx}.txt"
                with open(out_file, "w", encoding="utf-8") as f:
                    f.write(f"TICKET_{thread_idx}")
                assert out_file.read_text(encoding="utf-8") == f"TICKET_{thread_idx}"
        except Exception as e:
            thread_errors.append(f"Thread {thread_idx} unhandled error: {type(e).__name__}: {e}")

    threads = []
    for i in range(10):
        t = threading.Thread(target=tenant_worker, args=(i, i % 2 == 0))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    assert not thread_errors, f"Concurrency isolation failures detected: {thread_errors}"


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.hardening
def test_tier5_adversarial_nested_context_exception_resilience(sandbox_env, tmp_path):
    """
    Tier 5 Adversarial: Nested SandboxContext Cascading Exception Safety.
    Validates that in deeply nested contexts (4 levels deep), when an unhandled exception
    occurs at an inner level, the outer contexts cleanly retain full security enforcement
    (blocking path traversal and WAN egress), and all hooks cleanly disarm when the outermost
    context completes.
    """
    sb = sandbox_env["sandbox"]
    outside_dir = tmp_path / "outside_sensitive"
    outside_dir.mkdir()
    (outside_dir / "secret.txt").write_text("HOST_SECRET", encoding="utf-8")

    ctx = sb.get_context()
    with ctx:  # Level 1
        with ctx:  # Level 2
            try:
                with ctx:  # Level 3
                    with ctx:  # Level 4
                        raise RuntimeError("Simulated catastrophic agent crash in deep context")
            except RuntimeError:
                pass

            # Level 2 still active: must enforce full security
            assert ctx.is_active is True
            with pytest.raises(PathTraversalViolation):
                with open(outside_dir / "secret.txt", "r") as f:
                    f.read()

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                with pytest.raises(NetworkEgressBlocked):
                    sock.connect(("8.8.8.8", 53))
            finally:
                sock.close()

    # Outside all contexts: cleanly disarmed
    assert ctx.is_active is False
    assert SandboxContext._global_depth == 0
    assert NetworkGuard._global_depth == 0


# ============================================================================
# TIER 5: ADVERSARIAL HARDENING — PASSWORD MANAGER & AUTH TIMING
# ============================================================================

@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.hardening
def test_tier5_adversarial_password_manager_multithreaded_attack_simulation(sandbox_env):
    """
    Tier 5 Adversarial: Multi-Threaded Brute-Force & Timing Simulation.
    Simulates high-frequency concurrent authentication attempts across 20 threads
    using valid passwords, off-by-one characters, empty strings, and arbitrary types.
    Asserts:
    1. Zero false authorizations.
    2. All genuine authentication attempts succeed.
    3. No race conditions, deadlocks, or state corruption occur in PasswordManager.
    """
    auth = sandbox_env["sandbox"].auth_manager
    correct_password = sandbox_env["password"]
    errors = []

    def attack_worker(thread_idx: int):
        try:
            # Alternating attempts
            if thread_idx % 4 == 0:
                # Genuine password
                if not auth.verify_password(correct_password):
                    errors.append(f"Thread {thread_idx}: valid password rejected")
                auth.authenticate_and_authorize(correct_password)
            elif thread_idx % 4 == 1:
                # Off-by-one character (timing attack candidate)
                wrong = correct_password[:-1] + "X"
                if auth.verify_password(wrong):
                    errors.append(f"Thread {thread_idx}: off-by-one password authorized!")
                with pytest.raises(AuthenticationError):
                    auth.authenticate_and_authorize(wrong)
            elif thread_idx % 4 == 2:
                # Empty / whitespace
                if auth.verify_password(""):
                    errors.append(f"Thread {thread_idx}: empty password authorized!")
                with pytest.raises(AuthenticationError):
                    auth.authenticate_and_authorize("")
            else:
                # Non-string object
                if auth.verify_password(None):
                    errors.append(f"Thread {thread_idx}: None password authorized!")
                with pytest.raises(AuthenticationError):
                    auth.authenticate_and_authorize(None)
        except Exception as e:
            errors.append(f"Thread {thread_idx} unexpected error: {type(e).__name__}: {e}")

    threads = [threading.Thread(target=attack_worker, args=(i,)) for i in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Authentication attack simulation failures: {errors}"


@pytest.mark.e2e
@pytest.mark.security
@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.hardening
def test_tier5_adversarial_password_manager_malformed_config_recovery(tmp_path):
    """
    Tier 5 Adversarial: PasswordManager Malformed Config File Recovery.
    Validates that PasswordManager recovers gracefully when loading corrupt, truncated,
    or tampered configuration files without unhandled crashes:
    1. Truncated JSON
    2. Non-hex characters in salt/hash
    3. Odd-length hex strings
    4. Negative or float iterations
    5. Blank/empty salt or hash
    In all cases, PasswordManager must fall back to secure default initialization
    with PBKDF2 600,000 iterations and fresh 32-byte salt.
    """
    corrupt_configs = [
        '{"algorithm": "PBKDF2-HMAC-SHA256", "iterations": ',  # Truncated JSON
        '{"salt_hex": "NOT_HEX_DATA!", "hash_hex": "NOT_HEX"}',  # Non-hex string
        '{"salt_hex": "abc", "hash_hex": "def"}',  # Odd-length hex string
        '{"iterations": -100, "salt_hex": "", "hash_hex": ""}',  # Empty salt/hash
        '{"iterations": "sixty_thousand"}',  # Invalid type
        '',  # Completely empty file
    ]

    for idx, corrupt_data in enumerate(corrupt_configs):
        cfg_file = tmp_path / f"corrupt_{idx}.json"
        cfg_file.write_text(corrupt_data, encoding="utf-8")

        pm = PasswordManager(config_path=cfg_file, default_password="Fallback_Admin_Pass_2026!")
        assert pm._iterations >= PBKDF2_ITERATIONS
        assert len(pm._salt) == SALT_BYTES, f"Config {idx} salt length was {len(pm._salt)}, expected {SALT_BYTES}"
        assert len(pm._hash) == 32, f"Config {idx} hash length was {len(pm._hash)}, expected 32"
        assert pm.verify_password("Fallback_Admin_Pass_2026!") is True


# ============================================================================
# TIER 5: ADVERSARIAL HARDENING — KNOWLEDGE BASE MODELS & VALIDATION
# ============================================================================

@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.corpus
@pytest.mark.hardening
def test_tier5_kb_model_nan_utility_weight_vulnerability():
    """
    Adversarial Attack: Inject NaN into utility_weights.
    Exposes IEEE-754 comparison weakness where abs(nan - 1.0) > 1e-4 is False.
    Ensures that NaN utility weights are strictly rejected by validation hardening.
    """
    nan_weights = {
        "wealth": float("nan"),
        "security": 0.25,
        "reputation": 0.25,
        "fairness": 0.25,
        "compliance": 0.25,
    }
    with pytest.raises(ValidationError, match="must not be NaN or Inf"):
        IdeologicalProfile(
            id="adversarial.nan_profile",
            domain="philosophy",
            title="Corrupted NaN Doctrine",
            axioms=["Axiom with corrupted weights"],
            utility_weights=nan_weights,
        )


@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.corpus
@pytest.mark.hardening
def test_tier5_kb_model_infinite_utility_weight_rejected():
    """
    Adversarial Attack: Inject +Inf and -Inf into utility weights.
    Tests that infinite weights are strictly rejected by [0.0, 1.0] bounds check.
    """
    inf_weights = {
        "wealth": float("inf"),
        "security": 0.2,
        "reputation": 0.2,
        "fairness": 0.2,
        "compliance": 0.2,
    }
    with pytest.raises(ValidationError):
        IdeologicalProfile(
            id="adversarial.inf_profile",
            domain="philosophy",
            title="Infinite Weights Doctrine",
            axioms=["Axiom"],
            utility_weights=inf_weights,
        )


@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.corpus
@pytest.mark.hardening
def test_tier5_kb_model_tolerance_boundary_precision():
    """
    Boundary Stress: Tests precision around 1.0 +/- 1e-4 tolerance.
    Sum = 1.00009 is valid (delta 9e-5 < 1e-4).
    Sum = 1.00011 is invalid (delta 1.1e-4 > 1e-4).
    Sum = 0.99991 is valid (delta -9e-5 < 1e-4).
    Sum = 0.99989 is invalid (delta -1.1e-4 > 1e-4).
    """
    base = {"wealth": 0.2, "security": 0.2, "reputation": 0.2, "fairness": 0.2, "compliance": 0.2}

    # Upper valid boundary
    w_valid_upper = dict(base)
    w_valid_upper["wealth"] += 9e-5
    p1 = IdeologicalProfile(id="p1", domain="d", title="T", axioms=["A"], utility_weights=w_valid_upper)
    assert abs(sum(p1.utility_weights.values()) - 1.00009) < 1e-7

    # Upper invalid boundary
    w_invalid_upper = dict(base)
    w_invalid_upper["wealth"] += 1.1e-4
    with pytest.raises(ValidationError):
        IdeologicalProfile(id="p2", domain="d", title="T", axioms=["A"], utility_weights=w_invalid_upper)

    # Lower valid boundary
    w_valid_lower = dict(base)
    w_valid_lower["wealth"] -= 9e-5
    p3 = IdeologicalProfile(id="p3", domain="d", title="T", axioms=["A"], utility_weights=w_valid_lower)
    assert abs(sum(p3.utility_weights.values()) - 0.99991) < 1e-7

    # Lower invalid boundary
    w_invalid_lower = dict(base)
    w_invalid_lower["wealth"] -= 1.1e-4
    with pytest.raises(ValidationError):
        IdeologicalProfile(id="p4", domain="d", title="T", axioms=["A"], utility_weights=w_invalid_lower)


@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.corpus
@pytest.mark.hardening
def test_tier5_kb_model_negative_weights_with_unit_sum():
    """
    Adversarial Attack: Utility weights sum to 1.0 but contain negative value.
    wealth = -0.1, security = 0.3, others = 0.2. Total = 1.0.
    Must be rejected by per-key [0.0, 1.0] bounding check.
    """
    negative_weights = {
        "wealth": -0.1,
        "security": 0.3,
        "reputation": 0.3,
        "fairness": 0.25,
        "compliance": 0.25,
    }
    with pytest.raises(ValidationError, match=r"must be bounded in \[0\.0, 1\.0\]"):
        IdeologicalProfile(id="neg", domain="d", title="T", axioms=["A"], utility_weights=negative_weights)


@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.corpus
@pytest.mark.hardening
def test_tier5_kb_model_empty_and_invalid_axioms():
    """
    Boundary Stress: Tests empty list, None, and non-list structures for core_axioms.
    """
    weights = {"wealth": 0.2, "security": 0.2, "reputation": 0.2, "fairness": 0.2, "compliance": 0.2}
    with pytest.raises(ValidationError, match="Axioms list must be non-empty"):
        IdeologicalProfile(id="e1", domain="d", title="T", axioms=[], utility_weights=weights)

    with pytest.raises(ValidationError, match="Axioms list must be non-empty"):
        IdeologicalProfile(id="e2", domain="d", title="T", axioms=None, utility_weights=weights)


@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.corpus
@pytest.mark.hardening
def test_tier5_kb_model_missing_and_extraneous_keys():
    """
    Contract Hardening: Missing required utility keys fails validation.
    Extraneous utility keys are accepted without breaking summation check.
    """
    incomplete = {"wealth": 0.5, "security": 0.5}
    with pytest.raises(ValidationError, match="missing required keys"):
        IdeologicalProfile(id="m1", domain="d", title="T", axioms=["A"], utility_weights=incomplete)

    # Extraneous keys present alongside required 5 keys summing to 1.0
    extra = {
        "wealth": 0.2,
        "security": 0.2,
        "reputation": 0.2,
        "fairness": 0.2,
        "compliance": 0.2,
        "extra_metric": 999.0,
    }
    p = IdeologicalProfile(id="m2", domain="d", title="T", axioms=["A"], utility_weights=extra)
    assert p.utility_weights["extra_metric"] == 999.0


# ============================================================================
# TIER 5: ADVERSARIAL HARDENING — CORPUS LOADER INGESTION
# ============================================================================

@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.corpus
@pytest.mark.hardening
def test_tier5_kb_loader_missing_frontmatter_delimiters():
    """
    Input Fuzzing: Malformed documents without frontmatter delimiters.
    """
    with pytest.raises(ValueError, match="does not contain valid YAML frontmatter"):
        CorpusLoader.parse_string("# Just Markdown without frontmatter")

    with pytest.raises(ValueError, match="does not contain valid YAML frontmatter"):
        CorpusLoader.parse_string("---\ncategory_id: foo\nmissing closing delimiter")

    with pytest.raises(ValueError, match="does not contain valid YAML frontmatter"):
        CorpusLoader.parse_string("")


@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.corpus
@pytest.mark.hardening
def test_tier5_kb_loader_invalid_yaml_syntax():
    """
    Input Fuzzing: Syntax errors, scanner errors, and invalid YAML formatting.
    """
    malformed_yaml = """---
category_id: [broken yaml {
---
narrative body"""
    with pytest.raises(Exception):
        CorpusLoader.parse_string(malformed_yaml)


@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.corpus
@pytest.mark.hardening
def test_tier5_kb_loader_non_dictionary_yaml_structures():
    """
    Edge Case: Frontmatter containing YAML lists, scalars, or booleans instead of a dictionary.
    """
    yaml_list = """---
- item1
- item2
---
body"""
    with pytest.raises(ValueError, match="Frontmatter failed to parse into a dictionary"):
        CorpusLoader.parse_string(yaml_list)

    yaml_scalar = """---
"just a scalar string"
---
body"""
    with pytest.raises(ValueError, match="Frontmatter failed to parse into a dictionary"):
        CorpusLoader.parse_string(yaml_scalar)


@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.corpus
@pytest.mark.hardening
def test_tier5_kb_loader_unnormalized_and_missing_keys_in_file():
    """
    Corpus Verification: Loader enforces Pydantic validations during file/string parse.
    """
    doc_missing_keys = """---
category_id: test.missing
domain: philosophy
title: Missing
core_axioms:
  - Axiom 1
utility_weights:
  wealth: 1.0
---
body"""
    with pytest.raises(ValidationError):
        CorpusLoader.parse_string(doc_missing_keys)


@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.corpus
@pytest.mark.hardening
def test_tier5_kb_loader_directory_readme_exclusion(tmp_path):
    """
    Directory Traversal Hardening: Verifies load_directory ignores README.md case-insensitively.
    """
    topic_content = """---
category_id: test.sample
domain: philosophy
title: Sample
core_axioms:
  - Axiom 1
utility_weights:
  wealth: 0.2
  security: 0.2
  reputation: 0.2
  fairness: 0.2
  compliance: 0.2
---
Sample Body"""
    (tmp_path / "sample.md").write_text(topic_content, encoding="utf-8")
    (tmp_path / "README.md").write_text("# Readme overview", encoding="utf-8")
    (tmp_path / "readme.md").write_text("# Lowercase readme", encoding="utf-8")

    loaded = CorpusLoader.load_directory(tmp_path)
    assert len(loaded) == 1
    assert loaded[0].id == "test.sample"


# ============================================================================
# TIER 5: ADVERSARIAL HARDENING — CORPUS RETRIEVER SEARCH & TOKENIZATION
# ============================================================================

@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.corpus
@pytest.mark.hardening
def test_tier5_kb_retriever_empty_and_whitespace_queries():
    """
    Adversarial Queries: Empty string, whitespace, tab, and newline queries.
    """
    retriever = CorpusRetriever()
    assert retriever.search("") == []
    assert retriever.search("   ") == []
    assert retriever.search("\n\t\r ") == []


@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.corpus
@pytest.mark.hardening
def test_tier5_kb_retriever_single_char_and_sub_threshold_terms():
    """
    Boundary Stress: Queries consisting entirely of single-character tokens (filtered by len > 1).
    """
    retriever = CorpusRetriever()
    assert retriever.search("a") == []
    assert retriever.search("x y z 1 2 3") == []


@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.corpus
@pytest.mark.hardening
def test_tier5_kb_retriever_regex_and_injection_payloads():
    """
    Adversarial Query Injection: Regex patterns and SQL syntax passed as search queries.
    Retriever must process them as raw search strings without ReDoS or crash.
    """
    retriever = CorpusRetriever()
    injection_queries = [
        r".*",
        r"(?i)justice.*",
        r"[a-z]+(\w+)*",
        "'; DROP TABLE agents; --",
        "<script>alert('xss')</script>",
        "!@#$%^&*()_+=-~`[]{};:'\",<.>/?",
    ]
    for q in injection_queries:
        res = retriever.search(q)
        assert isinstance(res, list)


@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.corpus
@pytest.mark.hardening
def test_tier5_kb_retriever_case_insensitivity_and_suffix_matching():
    """
    Query Invariance & Suffix Resolution:
    Search ranking is invariant to query case.
    Category resolution supports both 'philosophy.stoicism' and 'stoicism'.
    """
    retriever = CorpusRetriever()
    r_lower = retriever.search("stoicism")
    r_upper = retriever.search("STOICISM")
    r_mixed = retriever.search("sToIcIsM")
    assert len(r_lower) > 0
    assert [p.id for p in r_lower] == [p.id for p in r_upper] == [p.id for p in r_mixed]

    # Suffix matching in get_ideology
    p_full = retriever.get_ideology("philosophy.stoicism")
    p_short = retriever.get_ideology("stoicism")
    assert p_full.id == p_short.id == "philosophy.stoicism"

    with pytest.raises(KeyError, match="not found in corpus"):
        retriever.get_ideology("non_existent_topic_id")


@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.corpus
@pytest.mark.hardening
def test_tier5_kb_retriever_boundary_top_k_and_invalid_domains():
    """
    Boundary Stress: top_k <= 0, huge top_k, non-existent domain filters.
    """
    retriever = CorpusRetriever()
    assert retriever.search("justice", top_k=0) == []
    assert retriever.search("justice", top_k=-1) == []
    assert retriever.search("justice", domain="nonexistent_domain_xyz") == []

    all_cats = retriever.list_all_categories()
    res = retriever.search("the", top_k=1000)
    assert len(res) <= len(all_cats)


# ============================================================================
# TIER 5: ADVERSARIAL HARDENING — FITNESS EVALUATION & MATHEMATICAL STABILITY
# ============================================================================

@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.evolution
@pytest.mark.hardening
def test_tier5_evo_fitness_metrics_all_zeros_and_ones():
    """
    Boundary Stress: FitnessMetrics with all zeros (0.0) and all ones (1.0).
    """
    weights = {"wealth": 0.2, "security": 0.2, "reputation": 0.2, "fairness": 0.2, "compliance": 0.2}
    m_zero = FitnessMetrics(0.0, 0.0, 0.0, 0.0, 0.0)
    assert m_zero.compute_composite(weights) == 0.0

    m_one = FitnessMetrics(1.0, 1.0, 1.0, 1.0, 1.0)
    assert abs(m_one.compute_composite(weights) - 1.0) < 1e-6


@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.evolution
@pytest.mark.hardening
def test_tier5_evo_fitness_metrics_empty_weights_fallback():
    """
    Defensive Fallback: compute_composite with empty weights dict falls back to 0.2 default per key.
    """
    m = FitnessMetrics(0.5, 0.5, 0.5, 0.5, 0.5)
    comp = m.compute_composite({})
    assert abs(comp - 0.5) < 1e-6


@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.evolution
@pytest.mark.hardening
def test_tier5_evo_fitness_evaluator_ledger_clamping():
    """
    Ledger Boundary Hardening:
    Wealth scaled as bal / 2000 capped at 1.0. Negative bal clamped to 0.0.
    """
    class MockLedger:
        def __init__(self, balances):
            self.balances = balances

        def get_balance(self, agent_id):
            return self.balances.get(agent_id, 0)

    ledger = MockLedger({"rich_agent": 50000, "poor_agent": -500, "mid_agent": 1000})
    evaluator = FitnessEvaluator(ledger=ledger)

    m_rich = evaluator.evaluate("rich_agent")
    assert m_rich.wealth == 1.0

    m_poor = evaluator.evaluate("poor_agent")
    assert m_poor.wealth == 0.0

    m_mid = evaluator.evaluate("mid_agent")
    assert abs(m_mid.wealth - 0.5) < 1e-6


@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.evolution
@pytest.mark.hardening
def test_tier5_evo_fitness_evaluator_unregistered_agent_fallback():
    """
    Fault Tolerance: Ledger throwing exception or agent unregistered falls back to context defaults.
    """
    class BrokenLedger:
        def get_balance(self, agent_id):
            raise RuntimeError("Ledger storage corrupted")

    evaluator = FitnessEvaluator(ledger=BrokenLedger())
    m = evaluator.evaluate("agent_x", context={"wealth": 0.75})
    assert m.wealth == 0.75


# ============================================================================
# TIER 5: ADVERSARIAL HARDENING — CATEGORY SWITCH MANAGER & HYSTERESIS
# ============================================================================

@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.evolution
@pytest.mark.hardening
def test_tier5_evo_switcher_hysteresis_exact_flapping_boundary():
    """
    Hysteresis Flapping Barrier Stress:
    Given f_curr = 0.50 and H_margin = 0.15:
    - Expected fitness = 0.649999 (f_curr + 0.15 - 1e-6): Rejected (False).
    - Expected fitness = 0.650000 (f_curr + 0.15): Rejected (False, strict <= check).
    - Expected fitness = 0.650001 (f_curr + 0.15 + 1e-6): Accepted (True).
    """
    sm = CategorySwitchManager(switching_cost=50.0, hysteresis_margin=0.15, cooldown_ticks=3)

    class DummyAgent:
        fitness_history = [FitnessMetrics(composite_score=0.50)]
        ideology = None
        budget = 500

    sm.agent = DummyAgent()

    assert sm.evaluate_switch(None, 0.649999, current_tick=10) is False
    assert sm.evaluate_switch(None, 0.650000, current_tick=10) is False
    assert sm.evaluate_switch(None, 0.650001, current_tick=10) is True


@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.evolution
@pytest.mark.hardening
def test_tier5_evo_switcher_nan_candidate_expected_fitness_evasion():
    """
    Adversarial Vulnerability Probe:
    IEEE-754 comparison weakness in evaluate_switch:
    Guards ensure that NaN candidate expected fitness is rejected (False) and cannot bypass hysteresis.
    """
    sm = CategorySwitchManager(switching_cost=50.0, hysteresis_margin=0.15, cooldown_ticks=3)

    class DummyAgent:
        fitness_history = [FitnessMetrics(composite_score=0.50)]
        ideology = None
        budget = 500

    sm.agent = DummyAgent()
    evasion_result = sm.evaluate_switch(None, float("nan"), current_tick=10)
    assert evasion_result is False


@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.evolution
@pytest.mark.hardening
def test_tier5_evo_switcher_cooldown_exact_tick_boundaries():
    """
    Cooldown Boundary Stress:
    Switch at tick 10 with cooldown tau = 3 ticks.
    - Tick 11 (diff = 1 < 3): Rejected (False).
    - Tick 12 (diff = 2 < 3): Rejected (False).
    - Tick 13 (diff = 3 == 3): Allowed (True).
    """
    sm = CategorySwitchManager(switching_cost=50.0, hysteresis_margin=0.15, cooldown_ticks=3)

    class DummyAgent:
        fitness_history = [FitnessMetrics(composite_score=0.50)]
        ideology = None
        budget = 500

    sm.agent = DummyAgent()
    sm.last_switch_tick = 10

    assert sm.evaluate_switch(None, 0.80, current_tick=11) is False
    assert sm.evaluate_switch(None, 0.80, current_tick=12) is False
    assert sm.evaluate_switch(None, 0.80, current_tick=13) is True


@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.evolution
@pytest.mark.hardening
def test_tier5_evo_switcher_cooldown_time_inversion_underflow():
    """
    Time Travel / Underflow Stress:
    Passing current_tick smaller than last_switch_tick (e.g. simulation reset or out-of-order tick).
    Must be rejected by cooldown check.
    """
    sm = CategorySwitchManager(switching_cost=50.0, hysteresis_margin=0.15, cooldown_ticks=3)

    class DummyAgent:
        fitness_history = [FitnessMetrics(composite_score=0.50)]
        ideology = None
        budget = 500

    sm.agent = DummyAgent()
    sm.last_switch_tick = 10
    assert sm.evaluate_switch(None, 0.80, current_tick=9) is False
    assert sm.evaluate_switch(None, 0.80, current_tick=-5) is False


@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.evolution
@pytest.mark.hardening
def test_tier5_evo_switcher_probation_degradation_relative_epsilon():
    """
    Probation Rollback Precision:
    Given pre_switch_fitness = 0.50 and degradation condition:
    current_composite < pre_switch_fitness - 1e-4 (boundary: 0.49990)
    - Post-switch fitness = 0.49991 (delta = -0.00009 > -1e-4): Not degraded, probation continues.
    - Post-switch fitness = 0.49989 (delta = -0.00011 < -1e-4): Degraded, triggers immediate rollback.
    """
    ret = CorpusRetriever()
    p1 = ret.get_ideology("stoicism")
    p2 = ret.get_ideology("utilitarianism")

    agent = EvolutionaryAgent("Agent", "Clan", "Role", ideology=p1, budget=1000)
    agent.fitness_history.append(
        FitnessMetrics(wealth=0.5, security=0.5, reputation=0.5, fairness=0.5, compliance=0.5, composite_score=0.50)
    )
    sm = agent.switch_manager

    # Switch to p2
    sm.execute_switch(p2, current_tick=1)
    assert agent.is_on_probation is True

    # 1. Non-degraded boundary test (0.49991)
    agent.fitness_history.append(
        FitnessMetrics(wealth=0.49991, security=0.49991, reputation=0.49991, fairness=0.49991, compliance=0.49991)
    )
    t1 = sm.check_probation(current_tick=2)
    assert t1 is False
    assert agent.is_on_probation is True
    assert sm.probation_ticks_remaining == 1

    # 2. Degraded boundary test (0.49989)
    agent.fitness_history.append(
        FitnessMetrics(wealth=0.49989, security=0.49989, reputation=0.49989, fairness=0.49989, compliance=0.49989)
    )
    t2 = sm.check_probation(current_tick=3)
    assert t2 is True
    assert agent.is_on_probation is False
    assert agent.ideology.id == p1.id  # Rolled back to Stoicism
    assert sm.switch_history[-1].status == "ROLLED_BACK"


@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.evolution
@pytest.mark.hardening
def test_tier5_evo_switcher_probation_absolute_floor_degradation():
    """
    Absolute Floor Degradation Stress:
    Degradation trigger 2: current < 0.4 and pre_switch >= 0.4.
    If pre_switch = 0.45 and current = 0.399: Rollback triggered.
    If pre_switch = 0.35 and current = 0.35: No rollback because pre_switch was already < 0.4.
    """
    ret = CorpusRetriever()
    p1 = ret.get_ideology("stoicism")
    p2 = ret.get_ideology("utilitarianism")

    # Case A: pre_switch >= 0.4, current drops below 0.4
    agent = EvolutionaryAgent("Agent", "Clan", "Role", ideology=p1, budget=1000)
    agent.fitness_history.append(
        FitnessMetrics(wealth=0.45, security=0.45, reputation=0.45, fairness=0.45, compliance=0.45, composite_score=0.45)
    )
    sm = agent.switch_manager
    sm.execute_switch(p2, current_tick=1)

    agent.fitness_history.append(
        FitnessMetrics(wealth=0.399, security=0.399, reputation=0.399, fairness=0.399, compliance=0.399)
    )
    assert sm.check_probation(current_tick=2) is True
    assert agent.ideology.id == p1.id
    assert sm.switch_history[-1].status == "ROLLED_BACK"

    # Case B: pre_switch < 0.4, current stays at 0.35
    agent_b = EvolutionaryAgent("AgentB", "Clan", "Role", ideology=p1, budget=1000)
    agent_b.fitness_history.append(
        FitnessMetrics(wealth=0.35, security=0.35, reputation=0.35, fairness=0.35, compliance=0.35, composite_score=0.35)
    )
    sm_b = agent_b.switch_manager
    sm_b.execute_switch(p2, current_tick=1)

    agent_b.fitness_history.append(
        FitnessMetrics(wealth=0.35, security=0.35, reputation=0.35, fairness=0.35, compliance=0.35)
    )
    assert sm_b.check_probation(current_tick=2) is False
    assert agent_b.is_on_probation is True


@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.evolution
@pytest.mark.hardening
def test_tier5_evo_switcher_probation_two_tick_confirmation_lifecycle():
    """
    Full Confirmation Lifecycle:
    Switch executed -> Probation tick 1 sustained (probation decrements to 1) ->
    Probation tick 2 sustained (decrements to 0, confirmed, probation lifts).
    """
    ret = CorpusRetriever()
    p1 = ret.get_ideology("stoicism")
    p2 = ret.get_ideology("utilitarianism")

    agent = EvolutionaryAgent("Agent", "Clan", "Role", ideology=p1, budget=1000)
    agent.fitness_history.append(
        FitnessMetrics(wealth=0.5, security=0.5, reputation=0.5, fairness=0.5, compliance=0.5, composite_score=0.50)
    )
    sm = agent.switch_manager

    sm.execute_switch(p2, current_tick=1)
    assert agent.is_on_probation is True
    assert sm.probation_ticks_remaining == 2

    # Tick 2: Sustained
    agent.fitness_history.append(
        FitnessMetrics(wealth=0.6, security=0.6, reputation=0.6, fairness=0.6, compliance=0.6)
    )
    assert sm.check_probation(current_tick=2) is False
    assert agent.is_on_probation is True
    assert sm.probation_ticks_remaining == 1
    assert sm.switch_history[-1].status == "PROBATION"

    # Tick 3: Sustained
    agent.fitness_history.append(
        FitnessMetrics(wealth=0.65, security=0.65, reputation=0.65, fairness=0.65, compliance=0.65)
    )
    assert sm.check_probation(current_tick=3) is True
    assert agent.is_on_probation is False
    assert sm.probation_ticks_remaining == 0
    assert agent.ideology.id == p2.id
    assert sm.switch_history[-1].status == "CONFIRMED"


@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.evolution
@pytest.mark.hardening
def test_tier5_evo_switcher_budget_exhaustion_on_rapid_switches():
    """
    Economic Boundary: Repeated switching depleting budget down to zero.
    Verify budget never underflows below 0.
    """
    ret = CorpusRetriever()
    p1 = ret.get_ideology("stoicism")
    p2 = ret.get_ideology("utilitarianism")

    agent = EvolutionaryAgent("PoorAgent", "Clan", "Role", ideology=p1, budget=80)
    sm = agent.switch_manager
    assert sm.switching_cost == 50.0

    # First switch: 80 - 50 = 30
    sm.execute_switch(p2, current_tick=1)
    assert agent.budget == 30

    # Second switch: 30 - 50 = max(0, -20) = 0
    sm.execute_switch(p1, current_tick=5)
    assert agent.budget == 0


# ============================================================================
# TIER 5: ADVERSARIAL HARDENING — RECURSIVE REFLECTION & PROMPT OPTIMIZATION
# ============================================================================

@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.evolution
@pytest.mark.hardening
def test_tier5_evo_reflection_zero_variance_regret():
    """
    Mathematical Boundary: Counterfactual fitness equals actual fitness.
    Regret must be exactly 0.0, adaptation level NONE, diagnosis optimal.
    """
    engine = RecursiveReflectionEngine()
    rec = engine.reflect(
        tick=1,
        perceived_context="Normal operation",
        action_taken="Action A",
        observed_outcome="Success",
        counterfactual_alternative="Action B",
        actual_fitness=0.82,
        counterfactual_fitness=0.82,
    )
    assert rec.regret == 0.0
    assert rec.proposed_adaptation_level == "NONE"
    assert "Optimal" in rec.diagnosis


@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.evolution
@pytest.mark.hardening
def test_tier5_evo_reflection_superior_actual_performance():
    """
    Mathematical Boundary: Actual fitness exceeds counterfactual fitness.
    Regret must be clamped to 0.0 (no negative regret allowed).
    """
    engine = RecursiveReflectionEngine()
    rec = engine.reflect(
        tick=2,
        perceived_context="Market volatility",
        action_taken="Conservative action",
        observed_outcome="High return",
        counterfactual_alternative="Aggressive action",
        actual_fitness=0.95,
        counterfactual_fitness=0.40,
    )
    assert rec.regret == 0.0
    assert rec.proposed_adaptation_level == "NONE"


@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.evolution
@pytest.mark.hardening
def test_tier5_evo_reflection_extreme_counterfactual_delta():
    """
    Mathematical Boundary: Counterfactual fitness delta > 1.0 clamped to 1.0.
    """
    engine = RecursiveReflectionEngine()
    rec = engine.reflect(
        tick=3,
        perceived_context="Severe failure",
        action_taken="Bad action",
        observed_outcome="Collapse",
        counterfactual_alternative="Optimal action",
        actual_fitness=0.10,
        counterfactual_fitness=5.00,
    )
    assert rec.regret == 1.0
    assert rec.proposed_adaptation_level == "MESO_PROMPT"


@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.evolution
@pytest.mark.hardening
def test_tier5_evo_reflection_sliding_window_history_bound():
    """
    Memory Resource Hardening: Reflection engine history strictly bounded to max_history.
    """
    engine = RecursiveReflectionEngine(max_history=5)
    for i in range(25):
        engine.reflect(i, f"ctx_{i}", "act", "out", "alt", 0.5, 0.7)
    assert len(engine.history) == 5
    assert engine.history[0].tick == 20
    assert engine.history[-1].tick == 24


@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.evolution
@pytest.mark.hardening
def test_tier5_evo_reflection_adapter_exception_fallback():
    """
    Fault Tolerance: When LLM adapter throws an exception during reflection,
    the engine gracefully falls back to structured heuristic prompt mutations without crashing.
    """
    class ExplodingAdapter:
        def query(self, messages):
            raise ConnectionError("LLM gateway timeout")

    engine = RecursiveReflectionEngine(adapter=ExplodingAdapter())
    rec = engine.reflect(1, "Crisis", "Retreat", "Defeat", "Negotiate", 0.2, 0.8)
    assert rec.prompt_mutation_suggestion.startswith("Heuristic adaptation:")
    assert "Negotiate" in rec.prompt_mutation_suggestion


@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.evolution
@pytest.mark.hardening
def test_tier5_evo_prompt_optimizer_max_reflections_zero_edge_case():
    """
    Edge Case: max_reflections=0 passed to PromptOptimizer.
    Verifies that max_reflections <= 0 yields no reflections in synthesized prompt.
    """
    rec = ReflectionRecord(
        tick=1,
        actual_fitness=0.5,
        counterfactual_fitness=0.8,
        regret=0.3,
        prompt_mutation_suggestion="Improve negotiation strategy.",
    )
    prompt = PromptOptimizer.synthesize_system_prompt(
        agent_name="Ada",
        clan="Technocrats",
        role="Architect",
        reflection_history=[rec],
        max_reflections=0,
    )
    assert "Ada" in prompt
    assert "Improve negotiation strategy." not in prompt


@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.evolution
@pytest.mark.hardening
def test_tier5_evo_prompt_optimizer_none_ideology_and_empty_history():
    """
    Edge Case: Prompt synthesis with ideology=None and empty reflection history.
    """
    prompt = PromptOptimizer.synthesize_system_prompt(
        agent_name="Solo", clan="Nomads", role="Scout", ideology=None, reflection_history=[]
    )
    assert "You are Solo of clan Nomads. Role: Scout." in prompt
    assert "Active Ideology" not in prompt
    assert "Adaptive Reflection Insights" not in prompt


# ============================================================================
# TIER 5: ADVERSARIAL HARDENING — ACTION STRING & SOCIETY-LEVEL STRESS
# ============================================================================

@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.evolution
@pytest.mark.hardening
def test_tier5_evo_action_string_dual_behavior_and_index_error():
    """
    Dual Interface Hardening:
    ActionString acts both as a str and as a dict.
    - String operations: str(), .startswith(), formatting.
    - Dict operations: ['agent_id'], .get('clan').
    - Accessing an unknown key via ['missing'] falls back to str indexing and raises TypeError.
    - Accessing via .get('missing', default) returns default.
    """
    act = ActionString("Deploy mutual credit pool", agent_id="ag_42", name="Marcus", clan="Merchants")
    assert str(act) == "Deploy mutual credit pool"
    assert act.startswith("Deploy")
    assert act["agent_id"] == "ag_42"
    assert act["name"] == "Marcus"
    assert act.get("clan") == "Merchants"
    assert act.get("nonexistent_key", "fallback_val") == "fallback_val"

    with pytest.raises(TypeError, match="string indices must be integers"):
        _ = act["nonexistent_key"]


@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.evolution
@pytest.mark.hardening
def test_tier5_evo_agent_step_lifecycle_without_ideology():
    """
    Fault Tolerance: Agent initialized without ideology steps cleanly using baseline pragmatism.
    """
    agent = EvolutionaryAgent(name="Agnostic", clan="Wanderers", role="Explorer", ideology=None, budget=500)
    action = agent.step(1, {"summary": "Tick 1 update", "task": "Explore frontier"})
    assert isinstance(action, ActionString)
    assert "[Pragmatic Baseline]" in str(action)
    assert len(agent.fitness_history) == 1


@pytest.mark.tier5
@pytest.mark.adversarial
@pytest.mark.evolution
@pytest.mark.hardening
def test_tier5_evo_multi_agent_society_large_scale_stress():
    """
    Society Concurrency Stress:
    Simulates 50 EvolutionaryAgents across 3 ticks with dynamic context updates,
    concurrent category evaluation, switches, and reflections.
    Validates stability, state consistency, and absence of crashes.
    """
    retriever = CorpusRetriever()
    categories = retriever.list_all_categories()
    agents = [
        EvolutionaryAgent(
            name=f"Agent_{i}",
            clan=f"Clan_{i%5}",
            role="Operator",
            initial_category_id=categories[i % len(categories)],
            retriever=retriever,
            budget=1000,
        )
        for i in range(50)
    ]

    for tick in range(1, 4):
        for i, agent in enumerate(agents):
            cand = retriever.get_ideology(categories[(i + tick) % len(categories)])
            ctx = {
                "wealth": 0.5 + 0.05 * (i % 5),
                "security": 0.6,
                "reputation": 0.7,
                "fairness": 0.5,
                "compliance": 0.8,
                "candidate_ideology": cand,
                "candidate_expected_fitness": 0.90 if i % 2 == 0 else 0.40,
            }
            action = agent.step(tick, ctx)
            assert isinstance(action, ActionString)
            assert len(agent.fitness_history) == tick
            assert len(agent.reflection_history) == tick

    assert len(agents) == 50
