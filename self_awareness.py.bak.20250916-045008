#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧠 Self-Awareness v4 — interactive dashboard (Termux/tmux friendly)

• Live status every 10s (modules up/down, CPU/MEM, purpose)
• Key commands (press a key then Enter):
    h  help (show menu)           q  quit this dashboard
    1  restart orchestrator       2  restart boot_levski
    3  restart sync_engine        4  restart watcher
    5  restart heart_walker       a  restart ALL core modules
    c  rebuild Sintra Codex       l  show last 50 lines of orchestrator.log
    L  show last 50 lines of watcher.log
"""

import os, sys, time, json, subprocess, threading, queue
from pathlib import Path
from datetime import datetime, UTC

try:
    import psutil
except Exception:
    psutil=None

ROOT     = Path(__file__).resolve().parent
STATE    = ROOT / "state"; STATE.mkdir(parents=True, exist_ok=True)
PIDDIR   = STATE / "pids"; PIDDIR.mkdir(parents=True, exist_ok=True)
LOGDIR   = ROOT / "logs"; LOGDIR.mkdir(parents=True, exist_ok=True)
MODLOG   = LOGDIR / "modules"; MODLOG.mkdir(parents=True, exist_ok=True)
DASHLOG  = LOGDIR / "self_awareness.log"
OBJFILE  = STATE / "objective_core.json"

# module definitions
MODULES = {
  "orchestrator": dict(path=ROOT/"orchestrator.py",      cmd=["python3", str(ROOT/"orchestrator.py")]),
  "boot_levski":  dict(path=ROOT/"boot_levski_v3.py",    cmd=["python3", str(ROOT/"boot_levski_v3.py")]),
  "sync_engine":  dict(path=ROOT/"sync_engine.py",       cmd=["python3", str(ROOT/"sync_engine.py")]),
  "watcher":      dict(path=ROOT/"watchdog_sync_loop.py",cmd=["python3", str(ROOT/"watchdog_sync_loop.py")]),
  "heart_walker": dict(path=ROOT/"heart_walker.py",      cmd=["python3", str(ROOT/"heart_walker.py")]),
}

CODEX_MD  = Path("~/HeartCore_OS_v1/logs/paradox_codex.md").expanduser()
CODEX_CLI = Path("~/HeartCore_OS_v1/sintra/sintra_codex_cli.py").expanduser()

HISTORY = {"cpu":[], "mem":[]}; MAXHIST=30
CMDQ = queue.Queue()

def now(): return datetime.now(UTC).isoformat(timespec="seconds")

def log(line:str):
    line=line.rstrip()
    print(line, flush=True)
    with DASHLOG.open("a", encoding="utf-8") as f: f.write(line+"\n")

def pid_file(name:str)->Path: return PIDDIR / f"{name}.pid"
def mod_log(name:str)->Path:   return MODLOG / f"{name}.log"

def pid_alive(pid:int)->bool:
    if pid<=0: return False
    if Path(f"/proc/{pid}").exists(): return True
    if psutil:
        try:
            p=psutil.Process(pid)
            return p.is_running() and p.status()!=psutil.STATUS_ZOMBIE
        except: return False
    return False

def read_pid(name:str)->int:
    f=pid_file(name)
    try: return int(f.read_text().strip()) if f.exists() else 0
    except: return 0

def write_pid(name:str, pid:int):
    pid_file(name).write_text(str(pid))

def start_module(name:str)->str:
    info = MODULES[name]
    if not info["path"].exists():
        return f"[warn] {name}: missing file {info['path']}"
    # already running?
    cur=read_pid(name)
    if pid_alive(cur): return f"[ok] {name} already running (pid={cur})"
    # spawn
    with mod_log(name).open("a", encoding="utf-8") as lf:
        proc = subprocess.Popen(info["cmd"], stdout=lf, stderr=lf, cwd=str(ROOT))
    write_pid(name, proc.pid)
    return f"[ok] started {name} (pid={proc.pid})"

def stop_module(name:str)->str:
    pid=read_pid(name)
    if not pid_alive(pid): return f"[ok] {name} not running"
    try:
        os.kill(pid, 15) # SIGTERM
        time.sleep(0.5)
        if pid_alive(pid):
            os.kill(pid, 9) # SIGKILL
        return f"[ok] stopped {name} (pid={pid})"
    except Exception as e:
        return f"[warn] stop {name} failed: {e}"

def restart_module(name:str)->str:
    s1=stop_module(name); s2=start_module(name)
    return s1+"\n"+s2

def system_snapshot():
    alive, dead = [], []
    for name in MODULES:
        pid=read_pid(name)
        (alive if pid_alive(pid) else dead).append(name)
    cpu=mem=None
    if psutil:
        try:
            cpu=psutil.cpu_percent(0.05)
            mem=psutil.virtual_memory().percent
            HISTORY["cpu"].append(cpu); HISTORY["mem"].append(mem)
            if len(HISTORY["cpu"])>MAXHIST: HISTORY["cpu"].pop(0); HISTORY["mem"].pop(0)
        except: pass
    return dict(ts=now(), alive=alive, dead=dead, cpu=cpu, mem=mem)

def read_purpose()->str:
    if not OBJFILE.exists(): return "(none)"
    try:
        return json.loads(OBJFILE.read_text()).get("purpose","(none)")
    except: return "(none)"

def rebuild_codex()->str:
    if not CODEX_CLI.exists(): return f"[warn] Codex CLI not found at {CODEX_CLI}"
    cmd=["python3", str(CODEX_CLI), "rebuild", "--backup"]
    try:
        out=subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
        return "[codex]\n"+out.strip()
    except subprocess.CalledProcessError as e:
        return f"[codex] failed (rc={e.returncode})\n{e.output}"

def tail_file(p:Path, n:int=50)->str:
    if not p.exists(): return f"(no file: {p})"
    try:
        lines=p.read_text(errors="replace").splitlines()
        return "\n".join(lines[-n:]) if lines else "(empty)"
    except Exception as e:
        return f"(cannot read {p}: {e})"

def show_menu():
    log("─── MENU ─────────────────────────────────────────────")
    log(" h help   q quit   a restart ALL   c rebuild Codex   ")
    log(" 1 restart orchestrator   2 boot_levski   3 sync_engine")
    log(" 4 watcher   5 heart_walker   l tail orch.log   L tail watcher.log")
    log("──────────────────────────────────────────────────────")

def input_worker():
    # read full lines so it works well inside tmux
    while True:
        try:
            line=sys.stdin.readline()
            if not line: break
            CMDQ.put(line.strip())
        except Exception:
            break

def handle_cmd(cmd:str):
    if cmd=="":
        return
    if cmd in ("h","help","?"): show_menu(); return
    if cmd=="q": log("[exit] dashboard requested"); sys.exit(0)
    if cmd=="1": log(restart_module("orchestrator")); return
    if cmd=="2": log(restart_module("boot_levski")); return
    if cmd=="3": log(restart_module("sync_engine")); return
    if cmd=="4": log(restart_module("watcher")); return
    if cmd=="5": log(restart_module("heart_walker")); return
    if cmd=="a":
        for m in ("boot_levski","sync_engine","watcher","heart_walker","orchestrator"):
            log(restart_module(m))
        return
    if cmd=="c": log(rebuild_codex()); return
    if cmd=="l": log("─ tail orchestrator.log ─"); log(tail_file(ROOT/"orchestrator.log", 50)); return
    if cmd=="L": log("─ tail watcher.log ─");      log(tail_file(MODLOG/"watcher.log", 50)); return
    log(f"[info] unknown command: {cmd} (press h for help)")

def main():
    log("🧠 self-awareness v4 (interactive) online.")
    show_menu()
    t=threading.Thread(target=input_worker, daemon=True); t.start()
    while True:
        snap=system_snapshot()
        status="OK" if "orchestrator" in snap["alive"] else ("DEGRADED" if snap["alive"] else "DOWN")
        log(f"🧭 {snap['ts']} | status={status} | alive={snap['alive']} | dead={snap['dead']} | cpu={snap['cpu']}% | mem={snap['mem']}%")
        log(f"🎯 Purpose: {read_purpose()}")
        if HISTORY["cpu"]:
            log(f"📈 CPU trend: {HISTORY['cpu']}")
            log(f"📊 MEM trend: {HISTORY['mem']}")
        # drain commands quickly before next tick
        started=time.time()
        while time.time()-started<10:
            try:
                handle_cmd(CMDQ.get(timeout=0.5))
            except queue.Empty:
                pass

if __name__=="__main__":
    try: main()
    except KeyboardInterrupt: pass
