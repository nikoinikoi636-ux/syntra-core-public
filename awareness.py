#!/usr/bin/env python3
import os, sys, json, time, platform, shutil, subprocess, socket
from pathlib import Path
ROOT = Path(__file__).resolve().parent
STATE = ROOT / "state"
LOGS  = ROOT / "logs" / "modules"
STATE.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)
OUT_JSON = STATE / "awareness.json"
OUT_TXT  = STATE / "awareness.txt"
LOG      = LOGS / "awareness.log"

def log(s): 
    m=s.strip()
    print(m, flush=True)
    LOG.open("a", encoding="utf-8").write(m+"\n")

def _cmd_ok(cmd, timeout=4):
    try:
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=timeout)
        return out.decode("utf-8", "ignore").strip()
    except Exception:
        return ""

def snapshot():
    info = {}
    info["time"] = _cmd_ok("date")
    info["platform"] = {
        "system": platform.system(),
        "release": platform.release(),
        "python": platform.python_version(),
        "machine": platform.machine(),
    }
    info["hostname"] = socket.gethostname()
    info["termux"] = bool(shutil.which("termux-info"))
    # cpu/mem/disk (best effort)
    info["cpu_count"] = os.cpu_count()
    info["mem_kB"] = _cmd_ok("grep MemAvailable /proc/meminfo | awk '{print $2}'")
    info["disk"] = _cmd_ok("df -h . | tail -n1")
    info["net"]  = _cmd_ok("ip addr | grep 'inet ' | awk '{print $2}' | paste -sd, -")
    # git remote (if repo)
    git = {}
    if (ROOT/".git").exists():
        git["remote"] = _cmd_ok(f"git -C '{ROOT}' remote -v | head -n1")
        git["branch"] = _cmd_ok(f"git -C '{ROOT}' rev-parse --abbrev-ref HEAD")
        git["status"] = _cmd_ok(f"git -C '{ROOT}' status --porcelain | wc -l")
    info["git"] = git
    # processes of interest
    procs = _cmd_ok("ps -ef | grep -v grep | grep python3")
    info["python_procs"] = procs.splitlines() if procs else []
    # codex health
    codex = Path.home()/ "HeartCore_OS_v1" / "logs" / "paradox_codex.md"
    info["codex_cycles"] = 0
    if codex.exists():
        try:
            cnt = sum(1 for line in codex.open(encoding="utf-8") if line.startswith("### Cycle "))
            info["codex_cycles"] = cnt
        except Exception:
            pass
    # save
    OUT_JSON.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_TXT.write_text(
        "\n".join([
            f"[{info['time']}] {info['platform']['system']} {info['platform']['release']} py{info['platform']['python']}",
            f"Host: {info['hostname']}  CPUs:{info['cpu_count']}  MemAvail(kB):{info['mem_kB']}",
            f"Disk: {info['disk']}",
            f"Net:  {info['net']}",
            f"Git:  {git.get('remote','(no repo)')}  Branch:{git.get('branch','-')}  Dirty:{git.get('status','-')}",
            f"Procs: {len(info['python_procs'])} python3 lines",
            f"Codex cycles: {info['codex_cycles']}",
        ]), encoding="utf-8"
    )
    log("[awareness] snapshot written.")

def main():
    if "--once" in sys.argv:
        snapshot(); return
    interval = 300
    try:
        i = sys.argv.index("--interval"); interval = int(sys.argv[i+1])
    except Exception: pass
    log(f"[awareness] loop start, interval={interval}s")
    while True:
        snapshot()
        time.sleep(interval)

if __name__ == "__main__":
    main()
