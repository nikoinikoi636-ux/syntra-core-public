import subprocess, os
from pathlib import Path
from .utils import ts

def git(*args):
    return subprocess.check_call(["git"] + list(args))

def bridge_push(ev_dir: Path, repo: str, branch: str = "sintra-sync"):
    # Clone or reuse local dir
    repo_dir = Path("sintra_repo")
    if not repo_dir.exists():
        git("clone", repo, str(repo_dir))
    os.chdir(str(repo_dir))
    git("checkout", "-B", branch)

    target = Path("sync") / ev_dir.name
    target.mkdir(parents=True, exist_ok=True)

    for fname in ["summary.md", "anomalies.json"]:
        src = ev_dir / fname
        if src.exists():
            dst = target / fname
            dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    git("add", ".")
    git("commit", "-m", f"Sync {ev_dir.name} at {ts()}")
    git("push", "origin", branch)
