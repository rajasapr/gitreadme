import os
from typing import Any, Dict
from fastapi import FastAPI, Request, HTTPException
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from utils import fetch_compare_diff, clone_and_prepare, git_commit_and_push

app = FastAPI()

GITHUB_PAT = os.getenv("GITHUB_PAT", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DEFAULT_BRANCH = os.getenv("DEFAULT_BRANCH", "main")
COMMIT_BACK = os.getenv("COMMIT_BACK", "true").lower() == "true"

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2, api_key=OPENAI_API_KEY)

README_PROMPT = """You are a documentation assistant.

Context:
- Unified diff of the latest commit range:
<DIFF>

- Current README.md (may be empty):
<README>

Task:
1) Identify user-facing changes (new/changed public APIs, CLI flags, endpoints, config keys, examples).
2) Update README.md to accurately reflect these changes.
3) Keep it concise, correct, and well-structured. Prefer editing existing sections where possible.
4) Output ONLY the full, final README.md content. No explanations, no code fences.
"""

def should_consider(filename: str) -> bool:
    important_exts = (".py", ".ts", ".js", ".md", ".yml", ".yaml", ".toml", ".json")
    return filename.endswith(important_exts) or filename.startswith(("docs/", "app/", "src/"))
def this_is_test():
    return "Fourth Test sucess "

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/webhook")
async def webhook(req: Request) -> Dict[str, Any]:
    data = await req.json()
    event = req.headers.get("X-GitHub-Event", "")
    if event != "push":
        return {"ok": True, "skipped": f"event={event}"}

    repo = data["repository"]["name"]
    full_name = data["repository"]["full_name"]
    owner = data["repository"]["owner"].get("name") or data["repository"]["owner"].get("login")

    # Branch from payload
    ref = data.get("ref", "refs/heads/main")
    branch = ref.split("/")[-1]
    before = data.get("before")
    after = data.get("after")

    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="Set OPENAI_API_KEY")

    # Clone repo (token if present so we can push)
    GITHUB_PAT = os.getenv("GITHUB_PAT", "")
    https_url = (
        f"https://x-access-token:{GITHUB_PAT}@github.com/{owner}/{repo}.git"
        if GITHUB_PAT else
        f"https://github.com/{owner}/{repo}.git"
    )
    repo_path = clone_and_prepare(https_url, branch=branch)

    # Make sure SHAs are present locally and compute diff with git (no rate limits)
    # Fetch both SHAs explicitly (shallow is fine)
    try:
        subprocess.check_call(["git", "fetch", "origin", before, after], cwd=repo_path)
    except Exception:
        # fallback: fetch full branch history if the SHAs aren’t in refs
        subprocess.check_call(["git", "fetch", "--unshallow"], cwd=repo_path)

    unified_diff = subprocess.check_output(
        ["git", "diff", f"{before}..{after}"], cwd=repo_path
    ).decode("utf-8", errors="ignore")

    changed_files = subprocess.check_output(
        ["git", "diff", "--name-only", f"{before}..{after}"], cwd=repo_path
    ).decode().splitlines()

    if not unified_diff.strip():
        return {"ok": True, "message": "No diff for this push", "branch": branch}

    # Current README
    readme_path = os.path.join(repo_path, "README.md")
    current_readme = ""
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            current_readme = f.read()

    # Ask the LLM
    system = SystemMessage(content="You write and edit technical documentation with precision.")
    human = HumanMessage(content=README_PROMPT.replace("<DIFF>", unified_diff).replace("<README>", current_readme))
    resp = llm.invoke([system, human])
    patched_readme = (resp.content or "").strip()

    # Ensure a commit happens even if content is identical
    if not patched_readme or patched_readme.strip() == (current_readme or "").strip():
        from datetime import datetime
        footer = f"\n\n<!-- auto: {datetime.utcnow().isoformat()}Z {after[:7]} -->\n"
        patched_readme = (current_readme or "# Project\n") + footer

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(patched_readme)

    pushed = False
    if os.getenv("COMMIT_BACK", "true").lower() == "true":
        pushed = git_commit_and_push(repo_path, "docs: auto-update README from latest changes", branch=branch)

    return {
        "ok": True,
        "repo": full_name,
        "branch": branch,
        "changed_files_seen": changed_files,
        "committed": pushed,
        "mode": "commit" if pushed else "no-change-or-error",
    }
