"""
Remote Push Synchronization Verification Test Suite (Milestone M4, Feature 16).

Verifies that:
1. Git remote origin is configured for AvijitShil/kingdom_of_agents.git.
2. Git credentials and permissions allow push access (push dry-run).
3. The local working tree is clean.
4. The local commit HEAD SHA matches the remote origin/main SHA on GitHub.
5. Remote sync operations can execute safely within the SecuritySandbox context.
"""

import os
import sys
import pathlib
import subprocess
import pytest

from sandbox import SecuritySandbox


@pytest.fixture(scope="module")
def repo_root() -> pathlib.Path:
    """Returns the repository root path."""
    return pathlib.Path(__file__).parent.parent.resolve()


@pytest.mark.e2e
@pytest.mark.sync
def test_remote_origin_configured(repo_root):
    """Verify that remote 'origin' is configured to AvijitShil/kingdom_of_agents.git."""
    res = subprocess.run(
        ["git", "remote", "-v"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    output = res.stdout.lower()
    assert "origin" in output
    assert "avijitshil/kingdom_of_agents.git" in output


@pytest.mark.e2e
@pytest.mark.sync
def test_git_push_dry_run_success(repo_root):
    """Verify that git push dry-run succeeds with exit code 0."""
    res = subprocess.run(
        ["git", "push", "--dry-run"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"git push --dry-run failed: {res.stderr}"


@pytest.mark.e2e
@pytest.mark.sync
def test_git_working_tree_clean(repo_root):
    """Verify that the repository working tree is clean (no untracked/modified files)."""
    res = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    output = res.stdout.strip()
    assert output == "", f"Working tree is not clean:\n{output}"


@pytest.mark.e2e
@pytest.mark.sync
def test_remote_head_matches_local_head(repo_root):
    """Verify that local commit HEAD SHA matches the remote refs/heads/main commit SHA."""
    # Local HEAD SHA
    local_sha_res = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    local_sha = local_sha_res.stdout.strip()
    assert len(local_sha) == 40, f"Invalid local SHA: {local_sha}"

    # Remote refs/heads/main SHA
    remote_res = subprocess.run(
        ["git", "ls-remote", "origin", "refs/heads/main"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    remote_out = remote_res.stdout.strip()
    assert remote_out, "Empty output from git ls-remote origin refs/heads/main"
    remote_sha = remote_out.split()[0]
    assert len(remote_sha) == 40, f"Invalid remote SHA: {remote_sha}"

    assert local_sha == remote_sha, (
        f"Local HEAD SHA ({local_sha}) does not match remote origin/main SHA ({remote_sha})"
    )


@pytest.mark.e2e
@pytest.mark.sync
def test_sandboxed_git_sync_execution(repo_root):
    """Verify that git push dry-run and status execute cleanly under SandboxContext."""
    sb = SecuritySandbox(project_root=repo_root)
    with sb.get_context():
        proc = subprocess.Popen(
            ["git", "push", "--dry-run"],
            cwd=repo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        out, err = proc.communicate()
        assert proc.returncode == 0, f"Sandboxed git push --dry-run failed: {err}"
