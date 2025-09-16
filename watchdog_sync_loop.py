#!/usr/bin/env python3
import os, time, sys, atexit
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOGDIR = ROOT / "logs" / "modules"
LOGDIR.mkdir(parents=True, exist_ok=True)
LOG = LOGDIR / "watcher.log"
LOCK = ROOT / "state" / "watcher.lock"
(LOCK.parent).mkdir(parents=True, exist_ok=True)

try:
    from filter_guard import should_process, reason
except Exception:
    def should_process(p:str)->bool: return True
    def reason(p:str)->str: return ""

SCAN_EVERY_SEC = 15
SHOW_MAX = 24
SEEN = set()

def emit(line: str):
    msg = line.rstrip()
    print(msg, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")

def already_running()->bool:
    if not LOCK.exists(): return False
    try:
        pid = int(LOCK.read_text().strip())
    except Exception:
        return False
    # check if pid alive
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False

def take_lock():
    LOCK.write_text(str(os.getpid()))
    atexit.register(lambda: LOCK.exists() and LOCK.unlink())

def list_files(root: Path):
    skip_dirs = {".git","__pycache__","node_modules","downloads","logs",
                 "sentinel-lab","bionet_collected_code","syntra-core-private_temp",
                 ".sofia",".sofia_v1"}
    for r, dirs, files in os.walk(root):
        # prune skip dirs in-place for speed
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for name in files:
            p = Path(r) / name
            rel = "./" + str(p.relative_to(root)).replace("\\","/")
            yield rel

def main():
    if already_running():
        emit("⚠️ Watcher already running (lock present). Exiting.")
        sys.exit(0)
    take_lock()
    emit("👁️ Watchdog стартиран... quiet + filtered + single-instance.")
    while True:
        added, skipped = [], 0
        for rel in list_files(ROOT):
            if rel in SEEN: continue
            why = reason(rel)
            if why == "" and should_process(rel):
                added.append(rel)
            else:
                skipped += 1
            SEEN.add(rel)
        if added:
            added.sort()
            view = added[:SHOW_MAX]
            more = len(added) - len(view)
            emit(f"🆕 Нови (филтрирани): {len(added)} | пропуснати: {skipped}")
            emit(f"   → {view}" + (f" …(+{more} още)" if more>0 else ""))
        time.sleep(SCAN_EVERY_SEC)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
