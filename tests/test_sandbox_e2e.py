"""
End-to-End Integration Tests for SecuritySandbox and SandboxContext.

Validates active runtime interception hooks on builtins.open, io.open,
pathlib.Path file operations, subprocess.Popen, and socket communication,
followed by full restoration on context exit.
"""

import io
import socket
import builtins
import subprocess
import pathlib
import pytest
pytestmark = pytest.mark.skip_sandbox

from sandbox import SecuritySandbox, SandboxContext, Permission
from sandbox.exceptions import (
    PathTraversalViolation,
    ExecutionBlockedViolation,
    NetworkEgressBlocked,
    TamperProtectionViolation,
)


@pytest.fixture
def test_environment(tmp_path):
    """Setup a test repository and external directory."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "data.txt").write_text("INITIAL_REPO_DATA", encoding="utf-8")
    (repo / ".sandbox_config.json").write_text("{}", encoding="utf-8")

    external = tmp_path / "external"
    external.mkdir()
    (external / "secret.txt").write_text("EXTERNAL_HOST_SECRET", encoding="utf-8")

    sandbox = SecuritySandbox(
        project_root=repo,
        config_file=".sandbox_config.json",
        default_password="E2E_Admin_Password_2026!",
    )
    return {
        "repo": repo,
        "external": external,
        "sandbox": sandbox,
    }


def test_builtin_open_confinement(test_environment):
    """Test that builtins.open is confined inside SandboxContext."""
    repo = test_environment["repo"]
    external = test_environment["external"]
    sandbox = test_environment["sandbox"]

    with sandbox.get_context():
        # In-repo read succeeds
        with open(repo / "data.txt", "r", encoding="utf-8") as f:
            content = f.read()
        assert content == "INITIAL_REPO_DATA"

        # In-repo write succeeds
        with open(repo / "new.txt", "w", encoding="utf-8") as f:
            f.write("NEW_DATA")
        assert (repo / "new.txt").read_text(encoding="utf-8") == "NEW_DATA"

        # External read raises PathTraversalViolation
        with pytest.raises(PathTraversalViolation):
            with open(external / "secret.txt", "r", encoding="utf-8") as f:
                f.read()

        # External write raises PathTraversalViolation
        with pytest.raises(PathTraversalViolation):
            with open(external / "leak.txt", "w", encoding="utf-8") as f:
                f.write("LEAKED_DATA")


def test_pathlib_io_confinement(test_environment):
    """Test that pathlib.Path.read_text and write_text are confined inside SandboxContext."""
    repo = test_environment["repo"]
    external = test_environment["external"]
    sandbox = test_environment["sandbox"]

    with sandbox.get_context():
        # In-repo Path reading and writing
        file_path = repo / "data.txt"
        assert file_path.read_text(encoding="utf-8") == "INITIAL_REPO_DATA"

        write_target = repo / "pathlib_out.txt"
        write_target.write_text("PATHLIB_SUCCESS", encoding="utf-8")
        assert write_target.read_text(encoding="utf-8") == "PATHLIB_SUCCESS"

        # External Path reading raises PathTraversalViolation
        with pytest.raises(PathTraversalViolation):
            (external / "secret.txt").read_text(encoding="utf-8")

        # External Path writing raises PathTraversalViolation
        with pytest.raises(PathTraversalViolation):
            (external / "exfil.txt").write_text("EXFILTRATED", encoding="utf-8")


def test_tamper_protection_in_context(test_environment):
    """Test that modifying .sandbox_config.json inside context is blocked."""
    repo = test_environment["repo"]
    sandbox = test_environment["sandbox"]

    with sandbox.get_context():
        # Reading config is permitted
        config_path = repo / ".sandbox_config.json"
        assert config_path.exists()

        # Modifying config is blocked
        with pytest.raises(TamperProtectionViolation):
            with open(config_path, "w", encoding="utf-8") as f:
                f.write('{"tampered": true}')

        with pytest.raises(TamperProtectionViolation):
            config_path.write_text('{"tampered": true}', encoding="utf-8")


def test_subprocess_popen_confinement(test_environment):
    """Test that subprocess.Popen is intercepted and confined inside SandboxContext."""
    repo = test_environment["repo"]
    sandbox = test_environment["sandbox"]

    with sandbox.get_context():
        # Allowed Python process execution
        proc = subprocess.Popen(
            ["python", "-c", "print('POPEN_SUCCESS')"],
            cwd=str(repo),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = proc.communicate(timeout=10)
        assert proc.returncode == 0
        assert "POPEN_SUCCESS" in stdout

        # Prohibited system binary execution
        with pytest.raises(ExecutionBlockedViolation):
            subprocess.Popen(
                ["powershell.exe", "-Command", "Get-Process"],
                cwd=str(repo),
            )


def test_network_egress_confinement_in_context(test_environment):
    """Test that network operations inside SandboxContext block WAN egress."""
    sandbox = test_environment["sandbox"]

    with sandbox.get_context():
        # External TCP connection blocked
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            with pytest.raises(NetworkEgressBlocked):
                sock.connect(("8.8.8.8", 53))
        finally:
            sock.close()

        # External UDP transmission blocked
        sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            with pytest.raises(NetworkEgressBlocked):
                sock_udp.sendto(b"telemetry", ("1.1.1.1", 53))
        finally:
            sock_udp.close()


def test_clean_restoration_on_context_exit(test_environment):
    """Test that all patched methods are fully restored after exiting SandboxContext."""
    orig_builtin_open = builtins.open
    orig_io_open = io.open
    orig_popen = subprocess.Popen
    orig_connect = socket.socket.connect

    sandbox = test_environment["sandbox"]

    with sandbox.get_context():
        assert builtins.open != orig_builtin_open
        assert io.open != orig_io_open
        assert subprocess.Popen != orig_popen
        assert socket.socket.connect != orig_connect

    # Outside context, everything is restored
    assert builtins.open == orig_builtin_open
    assert io.open == orig_io_open
    assert subprocess.Popen == orig_popen
    assert socket.socket.connect == orig_connect


def test_sandbox_facade_methods(test_environment):
    """Test high level methods on SecuritySandbox: read_text, write_text, run_command."""
    repo = test_environment["repo"]
    external = test_environment["external"]
    sandbox = test_environment["sandbox"]

    # read_text inside repo
    assert sandbox.read_text("data.txt") == "INITIAL_REPO_DATA"

    # write_text inside repo
    sandbox.write_text("sub/output.txt", "FACADE_WRITE_SUCCESS")
    assert (repo / "sub" / "output.txt").read_text(encoding="utf-8") == "FACADE_WRITE_SUCCESS"

    # read_text outside repo fails
    with pytest.raises(PathTraversalViolation):
        sandbox.read_text(external / "secret.txt")

    # write_text outside repo fails
    with pytest.raises(PathTraversalViolation):
        sandbox.write_text(external / "leak.txt", "MALICIOUS")

    # run_command succeeds
    res = sandbox.run_command(["python", "-c", "print('FACADE_CMD_SUCCESS')"])
    assert res.returncode == 0
    assert "FACADE_CMD_SUCCESS" in res.stdout



def test_nested_context_does_not_disarm_outer_context(test_environment):
    """Test that exiting an inner context does not disarm outer sandbox context."""
    external = test_environment["external"]
    sandbox = test_environment["sandbox"]
    ctx = sandbox.get_context()

    with ctx:
        with ctx:
            # Nested inside inner
            pass
        # Now in outer context: guards MUST remain fully armed
        assert ctx.is_active is True

        # 1. File access outside sandbox must be blocked
        with pytest.raises(PathTraversalViolation):
            with open(external / "secret.txt", "r", encoding="utf-8") as f:
                f.read()

        # 2. Network WAN connection must be blocked
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            with pytest.raises(NetworkEgressBlocked):
                sock.connect(("8.8.8.8", 53))
            with pytest.raises(NetworkEgressBlocked):
                sock.connect_ex(("8.8.8.8", 53))
        finally:
            sock.close()

        # 3. DNS lookup must be blocked
        with pytest.raises(NetworkEgressBlocked):
            socket.gethostbyname("attacker.com")

    # Outside outer context: hooks are restored
    assert ctx.is_active is False


def test_multithreaded_context_isolation_and_lifetime(test_environment):
    """Test that concurrent thread context exit does not disarm other active thread contexts."""
    import time
    import threading

    external = test_environment["external"]
    sandbox = test_environment["sandbox"]
    thread2_caught_violation = []
    thread2_errors = []

    def thread_1_work():
        with sandbox.get_context():
            time.sleep(0.05)
        # Thread 1 exits here

    def thread_2_work():
        try:
            with sandbox.get_context():
                time.sleep(0.15)
                # Thread 1 has exited; verify Thread 2 still blocks unauthorized open
                try:
                    with open(external / "secret.txt", "r", encoding="utf-8") as f:
                        f.read()
                    thread2_caught_violation.append(False)
                except PathTraversalViolation:
                    thread2_caught_violation.append(True)
        except Exception as e:
            thread2_errors.append(e)

    t1 = threading.Thread(target=thread_1_work)
    t2 = threading.Thread(target=thread_2_work)

    t2.start()
    time.sleep(0.01)
    t1.start()

    t1.join()
    t2.join()

    assert not thread2_errors, f"Thread 2 encountered unexpected error: {thread2_errors}"
    assert thread2_caught_violation == [True], "Thread 2 was disarmed prematurely by Thread 1 exit!"
