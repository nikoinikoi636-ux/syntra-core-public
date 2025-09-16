from datetime import timezone
#!/usr/bin/env python3
# report-only self awareness (does NOT start/stop anything)
import os, time, json
from pathlib import Path
from datetime import datetime, UTC

try:
    import psutil  # optional
except Exception:
    psutil = None

ROOT   = Path(__file__).resolve().parent
PIDDIR = ROOT / "state" / "pids"
LOG    = ROOT / "logs" / "self_awareness.log"

MODULES = ["orchestrator","boot_levski","sync_engine","watcher","heart_walker"]

def now(): return datetime.now(UTC).isoformat(timespec="seconds")

def pid_alive(pid: int) -> bool:
    if pid <= 0: return False
    if Path(f"/proc/{pid}").exists(): return True
    if psutil:
        try:
            p = psutil.Process(pid); return p.is_running() and p.status() != psutil.STATUS_ZOMBIE
        except Exception:
            return False
    return False

def read_pid(name: str) -> int:
    f = PIDDIR / f"{name}.pid"
    try:
        return int((f.read_text().strip() or "0")) if f.exists() else 0
    except Exception:
        return 0

def snapshot():
    alive, dead = {}, {}
    for m in MODULES:
        pid = read_pid(m)
        if pid_alive(pid):
            info = {"pid": pid}
            if psutil:
                try:
                    p = psutil.Process(pid)
                    with p.oneshot():
                        info["cpu"]  = p.cpu_percent(interval=0.05)
                        info["rss"]  = p.memory_info().rss
                        info["uptime_s"] = max(0, int(time.time() - p.create_time()))
                except Exception:
                    pass
            alive[m] = info
        else:
            dead[m] = {"pid": pid}
    # system load (optional)
    sysinfo = {}
    if psutil:
        try:
            sysinfo = {
                "cpu_total": psutil.cpu_percent(interval=0.05),
                "mem_used": psutil.virtual_memory().percent
            }
        except Exception:
            pass
    return {"ts": now(), "alive": alive, "dead": dead, "system": sysinfo}

def emit(line: str):
    line = line.rstrip()
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

def main():
    emit("🧠 self-awareness v2 (report-only) online.")
    while True:
        snap = snapshot()
        # concise console line
        alive_names = ",".join(snap["alive"].keys()) or "-"
        dead_names  = ",".join(snap["dead"].keys()) or "-"
        cpu = snap["system"].get("cpu_total")
        mem = snap["system"].get("mem_used")
        status = "OK" if "orchestrator" in snap["alive"] else "DEGRADED"
        emit(f"🧭 {snap['ts']} | status={status} | alive=[{alive_names}] | dead=[{dead_names}] | cpu={cpu}% | mem={mem}%")
        # JSON drop for tooling
        (ROOT/"state"/"self_awareness.json").write_text(json.dumps(snap, indent=2), encoding="utf-8")
        time.sleep(8)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
