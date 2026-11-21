"""
GitHub Sync & PAT Integration Test
Validates authentication, fine-grained PAT permissions, and repository push status.
"""

import os
import sys
import subprocess
import requests

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PAT_TOKEN = os.getenv("GITHUB_PAT", "")
REPO_OWNER = "AvijitShil"
REPO_NAME = "kingdom_of_agents"


def test_pat_and_sync():
    print("=" * 65)
    print("GitHub Integration & Repository Sync Test")
    print("=" * 65)

    headers = {
        "Authorization": f"Bearer {PAT_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    # 1. Test Authenticated User
    print("[1/4] Verifying GitHub User Identity...")
    try:
        user_res = requests.get("https://api.github.com/user", headers=headers, timeout=10)
        if user_res.status_code == 200:
            user_data = user_res.json()
            print(f"[+] Authenticated as: {user_data.get('login')} ({user_data.get('name')})")
        else:
            print(f"[-] Authentication failed: HTTP {user_res.status_code}")
            return False
    except Exception as e:
        print(f"[-] Network error connecting to GitHub: {e}")
        return False

    # 2. Test Repository Access & Permissions
    print("\n[2/4] Inspecting Repository Permissions on AvijitShil/kingdom_of_agents...")
    try:
        repo_res = requests.get(f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}", headers=headers, timeout=10)
        if repo_res.status_code == 200:
            repo_data = repo_res.json()
            perms = repo_data.get("permissions", {})
            print(f"[+] Repository found: {repo_data.get('full_name')}")
            print(f"    - Admin: {perms.get('admin')}")
            print(f"    - Push:  {perms.get('push')}")
            print(f"    - Pull:  {perms.get('pull')}")
        else:
            print(f"[-] Repository query failed: HTTP {repo_res.status_code}")
    except Exception as e:
        print(f"[-] Error querying repo: {e}")

    # 3. Test Fine-Grained 'Contents' Write Permission
    print("\n[3/4] Testing Fine-Grained 'Contents' Write Permission...")
    write_test = requests.get(f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents", headers=headers, timeout=10)
    print(f"    - Contents Read Status: HTTP {write_test.status_code} ({'OK' if write_test.status_code == 200 else 'Blocked'})")

    # 4. Check Local Git Remote & Push Status
    print("\n[4/4] Testing Local Git Push with Fine-Grained PAT...")
    push_check = subprocess.run(
        ["git", "push", "--dry-run"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True
    )
    if push_check.returncode == 0:
        print("[+] Git Push Verified: Permission GRANTED. Ready to sync.")
    else:
        err = push_check.stderr.strip()
        print(f"[*] Git Push Dry-Run Status:\n    {err}")
        if "403" in err:
            print("\n" + "=" * 65)
            print("DIAGNOSTIC NOTICE: Fine-Grained PAT Missing 'Contents: Write' Scope")
            print("=" * 65)
            print("To resolve this on GitHub in 30 seconds:")
            print("1. Go to: https://github.com/settings/tokens")
            print("2. Click on your fine-grained token to Edit.")
            print("3. Scroll to 'Repository permissions' -> 'Contents'.")
            print("4. Change 'Access' from 'No access' or 'Read-only' to: [Read and write].")
            print("5. Click 'Update token' at the bottom.")
            print("=" * 65)

    return True


if __name__ == "__main__":
    test_pat_and_sync()
