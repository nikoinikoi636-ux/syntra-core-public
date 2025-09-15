#!/usr/bin/env python3
"""
central_core_bridge.py — Git bridge for Central Core
- Push local .bionet/signals.jsonl increments to remote repo (branch)
- Pull remote inbox (repo/inbox.jsonl) and append to local signals.jsonl
- Maintains a small state file to avoid re-sending duplicates
- Works with SSH or HTTPS Git remotes
Usage:
  python central_core_bridge.py --config bridge_config.json push
  python central_core_bridge.py --config bridge_config.json pull
  python central_core_bridge.py --config bridge_config.json sync   # pull then push
  python central_core_bridge.py --config bridge_config.json loop --interval 60
"""

import argparse, os, subprocess, shutil, time, hashlib
from pathlib import Path
import json
from datetime import datetime

BIONET_DIR = Path(".bionet")
REG_PATH = BIONET_DIR / "registry.json"
SIG_PATH = BIONET_DIR / "signals.jsonl"
STATE_DIR = Path(".bridge_state")
STATE_FILE = STATE_DIR / "state.json"

def ts():
    return datetime.utcnow().isoformat() + "Z"

def ensure_local():
    BIONET_DIR.mkdir(parents=True, exist_ok=True)
    if not SIG_PATH.exists():
        SIG_PATH.write_text("", encoding="utf-8")

def load_state():
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"last_push_offset": 0, "last_pull_hash": ""}

def save_state(st):
    STATE_FILE.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")

def sha256_text(s: str) -> str:
    import hashlib
    h = hashlib.sha256(); h.update(s.encode("utf-8", errors="ignore"))
    return h.hexdigest()

def run_git(*args, cwd=None, check=True):
    return subprocess.run(["git", *args], cwd=cwd, check=check)

def clone_or_update(repo_url: str, branch: str, workdir: Path):
    if workdir.exists():
        # fetch & checkout branch
        run_git("fetch", "origin", cwd=workdir)
        run_git("checkout", branch, cwd=workdir, check=False)
        run_git("pull", "origin", branch, cwd=workdir, check=False)
    else:
        run_git("clone", "-b", branch, repo_url, str(workdir), check=True)

def read_lines(path: Path):
    if not path.exists():
        return []
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return []

def append_lines(path: Path, lines):
    with path.open("a", encoding="utf-8") as f:
        for ln in lines:
            f.write(ln + "\n")

def push(config):
    ensure_local()
    st = load_state()
    repo_url = config["repo"]
    branch = config.get("branch", "central-core")
    workdir = Path(config.get("workdir", ".bridge_repo"))
    outbox_name = config.get("outbox_name", "outbox.jsonl")

    # Prepare repo
    clone_or_update(repo_url, branch, workdir)

    # Read local signals; send only new lines
    local_lines = read_lines(SIG_PATH)
    start = st.get("last_push_offset", 0)
    if start > len(local_lines):
        start = 0  # reset if file rotated/truncated
    new_lines = local_lines[start:]
    if not new_lines:
        print("[push] nothing new")
        return

    # Append to outbox in repo
    outbox = workdir / outbox_name
    outbox.parent.mkdir(parents=True, exist_ok=True)
    append_lines(outbox, new_lines)

    # Commit & push
    run_git("add", ".", cwd=workdir, check=True)
    run_git("commit", "-m", f"bridge push {ts()} (+{len(new_lines)} lines)", cwd=workdir, check=False)
    run_git("push", "origin", branch, cwd=workdir, check=True)

    st["last_push_offset"] = len(local_lines)
    save_state(st)
    print(f"[push] sent {len(new_lines)} new lines (offset={st['last_push_offset']})")

def pull(config):
    ensure_local()
    st = load_state()
    repo_url = config["repo"]
    branch = config.get("branch", "central-core")
    workdir = Path(config.get("workdir", ".bridge_repo"))
    inbox_name = config.get("inbox_name", "inbox.jsonl")
    inbox_applied_name = config.get("inbox_applied_name", "inbox_applied.sha256")

    # Prepare repo
    clone_or_update(repo_url, branch, workdir)

    inbox = workdir / inbox_name
    lines = read_lines(inbox)
    if not lines:
        print("[pull] no inbox lines")
        return

    content = "\n".join(lines) + ("\n" if lines else "")
    h = sha256_text(content)
    last = st.get("last_pull_hash", "")
    if h == last:
        print("[pull] inbox unchanged")
        return

    # Append to local signals
    append_lines(SIG_PATH, lines)
    st["last_pull_hash"] = h
    save_state(st)

    # Mark applied in repo (optional)
    (workdir / inbox_applied_name).write_text(h + "\n", encoding="utf-8")
    run_git("add", ".", cwd=workdir, check=True)
    run_git("commit", "-m", f"bridge pull applied {ts()} (hash {h[:12]})", cwd=workdir, check=False)
    run_git("push", "origin", branch, cwd=workdir, check=True)

    print(f"[pull] appended {len(lines)} lines from inbox (hash={h[:12]})")

def sync(config):
    # Pull first, then push (so remote instructions land before we send new local)
    pull(config)
    push(config)

def loop(config, interval: int):
    print(f"[loop] bridge running every {interval}s… Ctrl+C to stop.")
    while True:
        try:
            sync(config)
        except Exception as e:
            print(f"[loop] error: {e}")
        time.sleep(interval)

def main():
    ap = argparse.ArgumentParser(description="Central Core Git Bridge")
    ap.add_argument("--config", required=True, help="Path to bridge_config.json")
    ap.add_argument("cmd", choices=["push","pull","sync","loop"])
    ap.add_argument("--interval", type=int, default=60, help="Loop interval seconds")
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    cmd = args.cmd
    if cmd == "push":
        push(cfg)
    elif cmd == "pull":
        pull(cfg)
    elif cmd == "sync":
        sync(cfg)
    elif cmd == "loop":
        loop(cfg, args.interval)

if __name__ == "__main__":
    main()
