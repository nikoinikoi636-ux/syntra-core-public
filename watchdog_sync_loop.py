#!/usr/bin/env python3
import os, time, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOGDIR = ROOT / "logs" / "modules"
LOGDIR.mkdir(parents=True, exist_ok=True)
LOG = LOGDIR / "watcher.log"

# Filter
try:
    from filter_guard import should_process, reason
except Exception:
    def should_process(p:str)->bool: return True
    def reason(p:str)->str: return ""

SCAN_EVERY_SEC = 15  # throttle
SHOW_MAX = 24        # max items to show in "new files" list
SEEN = set()

def emit(line: str):
    msg = line.rstrip()
    print(msg, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")

def list_files(root: Path):
    for r, _dirs, files in os.walk(root):
        # skip heavy/hidden trees early
        parts = Path(r).parts
        if any(x in (".git","__pycache__","node_modules","downloads","logs","sentinel-lab",
                     "bionet_collected_code","syntra-core-private_temp",".sofia",".sofia_v1") for x in parts):
            continue
        for name in files:
            p = Path(r) / name
            # produce POSIX-like relative path starting with "./"
            rel = "./" + str(p.relative_to(ROOT)).replace("\\","/")
            yield rel, p

def main():
    emit("👁️ Watchdog стартиран... следи за НУКЛЕАРНИ файлове (quiet).")
    while True:
        added, skipped = [], 0
        for rel, p in list_files(ROOT):
            if rel in SEEN: continue
            why = reason(rel)
            if why == "" and should_process(rel):
                added.append(rel)
            else:
                skipped += 1
            SEEN.add(rel)

        if added:
            added_sorted = sorted(added)
            view = added_sorted[:SHOW_MAX]
            more = len(added_sorted) - len(view)
            emit(f"🆕 Нови (филтрирани): {len(added_sorted)}  | пропуснати: {skipped}")
            emit(f"   → {view}" + (f" …(+{more} още)" if more>0 else ""))

        time.sleep(SCAN_EVERY_SEC)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
