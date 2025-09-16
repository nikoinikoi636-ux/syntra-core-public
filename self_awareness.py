#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Self-awareness v2 — Termux-friendly, PID-file based.
- Defaults PID dir to: ~/WorkingProgram/HeartCore/state/pids
- Respects env HEARTCORE_PID_DIR if provided
- No crashes if psutil missing; falls back to None metrics
"""
from __future__ import annotations
import os, time, json, signal
from pathlib import Path
from datetime import datetime, timezone

# Optional psutil (nice to have)
try:
    import psutil  # type: ignore
except Exception:
    psutil = None

HC = Path.home() / "WorkingProgram" / "HeartCore"
DEFAULT_PID_DIR = HC / "state" / "pids"
PID_DIR = Path(os.environ.get("HEARTCORE_PID_DIR", str(DEFAULT_PID_DIR))).expanduser()

LOG_DIR = HC / "logs" / "modules"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG = LOG_DIR / "self_awareness.log"

SERVICES = {
    "orchestrator":    "orchestrator.pid",
    "boot_levski":     "boot_levski.pid",
    "sync_engine":     "sync_engine.pid",
    "watcher":         "watcher.pid",
    "heart_walker":    "heart_walker.pid",
}

INTERVAL_SEC = int(os.environ.get("AWARENESS_INTERVAL", "15"))

def now_utc():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def pid_alive(pid:int) -> bool:
    try:
        # Fast check: signal 0
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except Exception:
        return False

def read_pid(path: Path) -> int | None:
    try:
        txt = path.read_text(encoding="utf-8").strip()
        if not txt:
            return None
        return int(txt)
    except Exception:
        return None

def cpu_mem():
    if psutil is None:
        return None, None
    try:
        c = psutil.cpu_percent(interval=None)
        m = psutil.virtual_memory().percent
        return c, m
    except Exception:
        return None, None

def emit(line: str):
    msg = line.rstrip()
    print(msg, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")

def snapshot():
    alive = []
    dead  = []
    for name, pidfile in SERVICES.items():
        p = PID_DIR / pidfile
        pid = read_pid(p)
        if pid is None:
            dead.append(name)
            continue
        if pid_alive(pid):
            alive.append(name)
        else:
            dead.append(name)
    cpu, mem = cpu_mem()
    status = "OK" if len(alive) == len(SERVICES) else ("DEGRADED" if alive else "DOWN")
    return {
        "ts": now_utc(),
        "status": status,
        "alive": alive,
        "dead": dead,
        "cpu": cpu,
        "mem": mem,
        "pid_dir": str(PID_DIR),
    }

def main():
    emit(f"🧠 self-awareness v2 online. PID_DIR={PID_DIR}")
    while True:
        s = snapshot()
        line = (f"🧭 {s['ts']} | status={s['status']} | "
                f"alive={s['alive']} | dead={s['dead']} | "
                f"cpu={s['cpu']}% | mem={s['mem']}%")
        emit(line)
        time.sleep(INTERVAL_SEC)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass

# --- Purpose Loader for Self-Awareness ---
PURPOSE_FILE = HC / "state" / "purpose.json"

def current_purpose():
    try:
        if PURPOSE_FILE.exists():
            data = json.loads(PURPOSE_FILE.read_text(encoding="utf-8"))
            return data.get("purpose", "(none)")
    except Exception:
        pass
    return "(none)"
# --- End Purpose Loader ---

# inject into main log loop
old_main = main
def main():
    while True:
        s = snapshot()
        purpose = current_purpose()
        line = (f"🧭 {s['ts']} | status={s['status']} | "
                f"alive={s['alive']} | dead={s['dead']} | "
                f"cpu={s['cpu']}% | mem={s['mem']}% | 🎯 purpose={purpose}")
        print(line, flush=True)
        with LOG.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        time.sleep(10)
