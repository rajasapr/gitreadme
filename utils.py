import os
import tempfile
import subprocess
from typing import Tuple, List
import httpx

def fetch_compare_diff(owner: str, repo: str, before: str, after: str) -> Tuple[str, List[str]]:
    import os, httpx
    url = f"https://api.github.com/repos/{owner}/{repo}/compare/{before}...{after}"
    headers = {"Accept": "application/vnd.github+json"}
    pat = os.getenv("GITHUB_PAT")
    if pat:
        headers["Authorization"] = f"Bearer {pat}"
    with httpx.Client(timeout=20) as client:
        r = client.get(url, headers=headers)
        r.raise_for_status()
        data = r.json()
    files = data.get("files", [])
    changed_files, patches = [], []
    for f in files:
        filename = f.get("filename")
        patch = f.get("patch")
        if filename:
            changed_files.append(filename)
        # Some large/binary changes have no 'patch'; we still want changed_files listed
        if filename and patch:
            patches.append(f"--- a/{filename}\n+++ b/{filename}\n{patch}")
    unified = "\n\n".join(patches)
    return unified, changed_files


def clone_and_prepare(repo_https_url: str, branch: str = "main") -> str:
    """Clones repo into a temp dir and checks out target branch."""
    tempdir = tempfile.mkdtemp(prefix="readme-agent-")
    subprocess.check_call(["git", "init"], cwd=tempdir)
    subprocess.check_call(["git", "remote", "add", "origin", repo_https_url], cwd=tempdir)
    subprocess.check_call(["git", "fetch", "origin", branch], cwd=tempdir)
    subprocess.check_call(["git", "checkout", "-B", branch, f"origin/{branch}"], cwd=tempdir)
    return tempdir

def git_commit_and_push(repo_path: str, commit_msg: str, branch: str = "main") -> bool:
    subprocess.run(["git", "config", "user.name", "readme-agent-bot"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.email", "bot@users.noreply.github.com"], cwd=repo_path, check=True)
    subprocess.run(["git", "add", "README.md"], cwd=repo_path, check=True)
    c = subprocess.run(["git", "commit", "-m", commit_msg], cwd=repo_path)
    if c.returncode != 0:
        return False
    subprocess.check_call(["git", "push", "origin", branch], cwd=repo_path)
    return True
