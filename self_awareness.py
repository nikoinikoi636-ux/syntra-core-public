#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Self-Awareness v2
- Lists exact alive core processes
- Records rolling history (state/awareness_log.json)
- Emits warnings if a core module is missing
- Simple health stats (CPU, RAM)
"""

import os, sys, time, json, psutil
from pathlib import Path
from datetime import datetime

ROOT   = Path(__file__).resolve().parent
STATE  = ROOT / "state"
LOGDIR = ROOT / "logs" / "modules"
STATE.mkdir(parents=True, exist_ok=True)
LOGDIR.mkdir(parents=True, exist_ok=True)

AWARE_JSON  = STATE / "awareness_log.json"       # rolling history
AWARE_LATEST= STATE / "awareness_latest.json"    # latest snapshot
PRINT_LOG   = LOGDIR / "awareness_console.log"   # human-readable tail

# declare what we care about (process match substrings)
CORE_PROCS = {
    "orchestrator" : "orchestrator.py",
    "boot_levski"  : "boot_levski_v3.py",
    "sync_engine"  : "sync_engine.py",
    "watcher"      : "watchdog_sync_loop.py",
    "heart_walker" : "heart_walker.py",
}

PURPOSE = "Switch all systems on, connect all nodes, stabilize, defend HeartCore, and verify the goal."

def now_iso():
    return datetime.now(datetime.UTC).isoformat(timespec="seconds")

def alive_pids(match_substr):
    pids = []
    for p in psutil.process_iter(attrs=["pid","name","cmdline"]):
        try:
            cmd = " ".join(p.info.get("cmdline") or [])
            if match_substr in cmd:
                pids.append(p.info["pid"])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return sorted(pids)

def summarize_system():
    try:
        cpu = psutil.cpu_percent(interval=0.3)
    except Exception:
        cpu = None
    try:
        vm = psutil.virtual_memory()._asdict()
    except Exception:
        vm = {}
    return {"cpu_percent": cpu, "mem": vm}

def snapshot():
    procs = {}
    missing = []
    total_alive = 0
    for name, needle in CORE_PROCS.items():
        pids = alive_pids(needle)
        procs[name] = {"needle": needle, "pids": pids, "alive": len(pids) > 0}
        if pids: total_alive += len(pids)
        else:    missing.append(name)
    sysstat = summarize_system()
    return {
        "ts": now_iso(),
        "purpose": PURPOSE,
        "total_alive": total_alive,
        "procs": procs,
        "missing": missing,
        "system": sysstat,
        "status": "OK" if not missing else "DEGRADED"
    }

def append_jsonl(path: Path, obj: dict, max_bytes: int = 1_000_000):
    """Keep a rolling JSONL file under ~1MB."""
    line = json.dumps(obj, ensure_ascii=False)
    if path.exists() and path.stat().st_size > max_bytes:
        # rotate
        path.replace(path.with_suffix(path.suffix + ".1"))
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

def log_print(msg: str):
    line = msg.rstrip()
    print(line, flush=True)
    with PRINT_LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

def main():
    interval = float(os.getenv("AWARE_INTERVAL", "10"))  # seconds
    log_every = int(os.getenv("AWARE_VERBOSITY", "1"))   # 1=every loop
    k = 0
    log_print("🧠 self-awareness v2 online.")
    while True:
        snap = snapshot()

        # save latest + append to history
        AWARE_LATEST.write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8")
        append_jsonl(AWARE_JSON, snap)

        # human-facing line (every loop unless VERBOSITY > 1)
        if k % max(1, log_every) == 0:
            alive_list = [f"{name}:{len(snap['procs'][name]['pids'])}" for name in CORE_PROCS]
            log_print(f"🧭 {snap['ts']} | status={snap['status']} | alive={snap['total_alive']} | {', '.join(alive_list)} | cpu={snap['system']['cpu_percent']}%")

        # warnings for missing modules
        if snap["missing"]:
            log_print("⚠️  missing modules: " + ", ".join(snap["missing"]))
            if os.getenv("AWARE_AUTORESTART", "0") == "1":
                for name in snap["missing"]:
                    cmd = None
                    if name == "watcher":      cmd = f"nohup python3 {ROOT/'watchdog_sync_loop.py'} >/dev/null 2>&1 &"
                    elif name == "sync_engine": cmd = f"nohup python3 {ROOT/'sync_engine.py'} >/dev/null 2>&1 &"
                    elif name == "boot_levski":cmd = f"nohup python3 {ROOT/'boot_levski_v3.py'} >/dev/null 2>&1 &"
                    elif name == "orchestrator":cmd = f"nohup python3 {ROOT/'orchestrator.py'} >/dev/null 2>&1 &"
                    elif name == "heart_walker":cmd = f"nohup python3 {ROOT/'heart_walker.py'} >/dev/null 2>&1 &"
                    if cmd:
                        os.system(cmd)

        k += 1
        time.sleep(interval)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
