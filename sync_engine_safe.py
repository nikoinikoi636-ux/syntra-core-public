#!/usr/bin/env python3
import os, time, subprocess, json, hashlib, sys
from pathlib import Path

ROOT = Path.home() / "WorkingProgram" / "HeartCore"
IGNORE = ("logs/", "state/", "__pycache__/", ".git/")
DEBOUNCE_SEC = 15

def snapshot():
    files = []
    for p in ROOT.rglob("*"):
        rel = p.relative_to(ROOT).as_posix()
        if any(rel.startswith(ig) for ig in IGNORE): continue
        if p.is_file():
            try:
                st = p.stat()
                files.append((rel, int(st.st_mtime), int(st.st_size)))
            except FileNotFoundError:
                pass
    files.sort()
    data = json.dumps(files).encode()
    return hashlib.sha1(data).hexdigest()

def run_sync():
    # stage -> commit -> push; respect .gitignore + pre-commit hook
    cmds = [
        ["git","-C",str(ROOT),"add","-A"],
        ["git","-C",str(ROOT),"commit","-m","🔁 Auto-sync update"],
        ["git","-C",str(ROOT),"push","-u","origin","main"],
    ]
    for c in cmds:
        r = subprocess.run(c, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        # Allow "nothing to commit"
        if r.returncode != 0 and "nothing to commit" not in r.stdout.lower():
            print("[sync] cmd fail:", " ".join(c))
            print(r.stdout)
            break
        else:
            print(r.stdout.strip())

def main():
    print("🛰️ sync_engine_safe: watching code with debounce", DEBOUNCE_SEC, "sec")
    last = snapshot()
    last_sync = 0
    while True:
        now = time.time()
        cur = snapshot()
        if cur != last and (now - last_sync) >= DEBOUNCE_SEC:
            print("🔍 code changed → syncing…")
            run_sync()
            last = cur
            last_sync = now
        time.sleep(2)

if __name__ == "__main__":
    main()
