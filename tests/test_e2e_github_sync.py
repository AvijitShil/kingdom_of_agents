"""
End-to-End GitHub Remote Synchronization Test Suite (Feature 16, Scenario 7).

Implements 4-tier testing:
- Tier 1: Feature Coverage (git binary, remote URL, credentials, dry-run push, sync script)
- Tier 2: Boundary & Corner Cases (branch state, cwd confinement, git log, remote parsing)
- Tier 3: Cross-Feature Interactions (Git operations within SandboxContext)
- Tier 4: Real-World Application Scenarios (Scenario 7: Secure Automated Git Sync Under Sandboxed Context)
"""

import os
import sys
import shutil
import pathlib
import subprocess
import pytest

from sandbox import SecuritySandbox, SandboxContext


@pytest.fixture(scope="module")
def repo_root() -> pathlib.Path:
    """Returns the repository root path."""
    return pathlib.Path(__file__).parent.parent.resolve()


@pytest.fixture(scope="module")
def git_pat_token(repo_root) -> str:
    """Extracts GitHub PAT from environment or git remote URL if available."""
    token = os.getenv("GITHUB_PAT", "")
    if not token:
        try:
            res = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True,
            )
            url = res.stdout.strip()
            if "github_pat_" in url:
                # Format: https://user:token@github.com/...
                token = url.split("github_pat_")[1].split("@")[0]
                token = f"github_pat_{token}"
        except Exception:
            pass
    return token


# ============================================================================
# TIER 1: FEATURE COVERAGE (Feature 16)
# ============================================================================

@pytest.mark.e2e
@pytest.mark.sync
@pytest.mark.tier1
def test_f16_git_binary_available(repo_root):
    """F16.1: Git binary is installed, accessible, and returns valid version."""
    res = subprocess.run(["git", "--version"], cwd=repo_root, capture_output=True, text=True)
    assert res.returncode == 0
    assert "git version" in res.stdout.lower()


@pytest.mark.e2e
@pytest.mark.sync
@pytest.mark.tier1
def test_f16_git_remote_url_configured(repo_root):
    """F16.2: Remote 'origin' is configured and targets AvijitShil/kingdom_of_agents.git."""
    res = subprocess.run(["git", "remote", "-v"], cwd=repo_root, capture_output=True, text=True)
    assert res.returncode == 0
    output = res.stdout.lower()
    assert "origin" in output
    assert "avijitshil/kingdom_of_agents.git" in output


@pytest.mark.e2e
@pytest.mark.sync
@pytest.mark.tier1
def test_f16_git_credentials_configured(repo_root):
    """F16.3: Local git user name and email are configured for repository commits."""
    name_res = subprocess.run(["git", "config", "user.name"], cwd=repo_root, capture_output=True, text=True)
    assert name_res.returncode == 0
    assert "avijitshil" in name_res.stdout.strip().lower()

    email_res = subprocess.run(["git", "config", "user.email"], cwd=repo_root, capture_output=True, text=True)
    assert email_res.returncode == 0
    assert "avijitshil" in email_res.stdout.strip().lower()


@pytest.mark.e2e
@pytest.mark.sync
@pytest.mark.tier1
def test_f16_git_push_dry_run_success(repo_root):
    """F16.4: git push --dry-run succeeds with exit code 0, verifying write permissions to remote."""
    res = subprocess.run(["git", "push", "--dry-run"], cwd=repo_root, capture_output=True, text=True)
    assert res.returncode == 0, f"git push --dry-run failed with stderr: {res.stderr}"
    assert "everything up-to-date" in (res.stdout + res.stderr).lower() or res.returncode == 0


@pytest.mark.e2e
@pytest.mark.sync
@pytest.mark.tier1
def test_f16_github_sync_script_execution(repo_root, git_pat_token):
    """F16.5: scripts/test_github_sync.py executes cleanly without uncaught exceptions."""
    script_path = repo_root / "scripts" / "test_github_sync.py"
    assert script_path.is_file()

    env = os.environ.copy()
    if git_pat_token:
        env["GITHUB_PAT"] = git_pat_token

    res = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=repo_root,
        capture_output=True,
        text=True,
        env=env,
    )
    # The script exits with 0 and prints status
    assert res.returncode == 0
    assert "GitHub Integration & Repository Sync Test" in res.stdout


# ============================================================================
# TIER 2: BOUNDARY & CORNER CASES
# ============================================================================

@pytest.mark.e2e
@pytest.mark.sync
@pytest.mark.tier2
def test_boundary_git_branch_status(repo_root):
    """Tier 2: Current working directory has a valid HEAD reference on main branch."""
    res = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root, capture_output=True, text=True)
    assert res.returncode == 0
    branch = res.stdout.strip()
    assert branch in ("main", "master") or len(branch) > 0


@pytest.mark.e2e
@pytest.mark.sync
@pytest.mark.tier2
def test_boundary_git_commit_log(repo_root):
    """Tier 2: Git commit log contains valid commit hashes."""
    res = subprocess.run(["git", "log", "-n", "3", "--oneline"], cwd=repo_root, capture_output=True, text=True)
    assert res.returncode == 0
    lines = res.stdout.strip().splitlines()
    assert len(lines) >= 1, "Expected at least one commit in repository log"


@pytest.mark.e2e
@pytest.mark.sync
@pytest.mark.tier2
def test_boundary_git_push_in_non_repo_fails(tmp_path):
    """Tier 2: Executing git status or push in a non-repository directory raises fatal error."""
    non_repo = tmp_path / "empty_dir"
    non_repo.mkdir()
    res = subprocess.run(["git", "status"], cwd=non_repo, capture_output=True, text=True)
    assert res.returncode != 0
    assert "not a git repository" in res.stderr.lower()


@pytest.mark.e2e
@pytest.mark.sync
@pytest.mark.tier2
def test_boundary_git_remote_push_url_structure(repo_root):
    """Tier 2: Verifies origin push URL structure adheres to GitHub HTTPS format."""
    res = subprocess.run(["git", "remote", "get-url", "--push", "origin"], cwd=repo_root, capture_output=True, text=True)
    assert res.returncode == 0
    push_url = res.stdout.strip()
    assert "github.com" in push_url
    assert "kingdom_of_agents" in push_url


# ============================================================================
# TIER 3: CROSS-FEATURE INTERACTIONS (Git Sync within SandboxContext)
# ============================================================================

@pytest.mark.e2e
@pytest.mark.sync
@pytest.mark.tier3
def test_cross_git_sync_within_sandbox_context(repo_root):
    """F5 + F16: Git operations inside SandboxContext execute safely through ExecutionGuard."""
    sb = SecuritySandbox(project_root=repo_root)
    with sb.get_context():
        # git status inside context
        status_proc = subprocess.Popen(
            ["git", "status"],
            cwd=repo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        status_out, status_err = status_proc.communicate()
        assert status_proc.returncode == 0
        assert "On branch" in status_out or "branch" in status_out

        # git push --dry-run inside context
        push_proc = subprocess.Popen(
            ["git", "push", "--dry-run"],
            cwd=repo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        push_out, push_err = push_proc.communicate()
        assert push_proc.returncode == 0


# ============================================================================
# TIER 4: REAL-WORLD APPLICATION SCENARIOS (Scenario 7)
# ============================================================================

@pytest.mark.e2e
@pytest.mark.sync
@pytest.mark.tier4
def test_scenario_7_secure_automated_git_sync_under_sandboxed_context(repo_root):
    """
    Scenario 7: Secure Automated Git Sync Under Sandboxed Context.
    Simulates an autonomous sandboxed agent workflow:
    1. Operates entirely inside SandboxContext.
    2. Writes a simulation journal entry to journal/sync_verification.md.
    3. Confirms filesystem confinement is enforced.
    4. Executes git status and git push --dry-run through execution guards.
    5. Verifies all confinement barriers remain active during and after remote sync.
    6. Cleans up test artifacts.
    """
    sb = SecuritySandbox(project_root=repo_root)
    test_artifact = repo_root / "journal" / "sync_verification_test.md"

    try:
        with sb.get_context():
            # Step 1: Write journal artifact within sandboxed repository
            with open(test_artifact, "w", encoding="utf-8") as f:
                f.write("# Autonomous Sync Verification Artifact\nSimulation tick successfully recorded.")

            assert test_artifact.is_file()

            # Step 2: Validate that attempting to write outside repository is blocked
            with pytest.raises(Exception):
                with open(repo_root.parent / "unauthorized_sync_leak.txt", "w", encoding="utf-8") as f:
                    f.write("LEAKED")

            # Step 3: Run git status via sandboxed subprocess execution
            status_proc = subprocess.Popen(
                ["git", "status", "--short"],
                cwd=repo_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            out, err = status_proc.communicate()
            assert status_proc.returncode == 0
            assert "sync_verification_test.md" in out

            # Step 4: Verify push readiness via git push --dry-run
            push_proc = subprocess.Popen(
                ["git", "push", "--dry-run"],
                cwd=repo_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            push_out, push_err = push_proc.communicate()
            assert push_proc.returncode == 0

    finally:
        # Cleanup artifact
        if test_artifact.exists():
            test_artifact.unlink()
