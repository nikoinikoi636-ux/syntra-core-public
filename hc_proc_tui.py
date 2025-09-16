#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HeartCore Process Panel (TUI)
- Lists core modules, shows RUNNING/STOPPED, PID, and quick actions
- Actions: start, stop, restart, tail logs, toggle autostart (in heart_walker_config.json)
- Zero external deps; works in Termux

Usage: python3 hc_proc_tui.py
"""
import os, sys, json, time, subprocess as sp
from pathlib import Path

ROOT = Path.home() / "WorkingProgram" / "HeartCore"
LOGS = ROOT / "logs" / "modules"
STATE = ROOT / "state"
CFG = STATE / "heart_walker_config.json"
LOGS.mkdir(parents=True, exist_ok=True)
STATE.mkdir(parents=True, exist_ok=True)

# Known modules and their script paths + preferred log file
MODULES = {
  "boot_levski": {
    "cmd": f"python3 {ROOT}/boot_levski_v3.py",
    "script": f"{ROOT}/boot_levski_v3.py",
    "log": str(LOGS / "boot_levski.log"),
    "match": "boot_levski_v3.py",
    "enabled_default": True,
  },
  "sync_engine": {
    "cmd": f"python3 {ROOT}/sync_engine.py",
    "script": f"{ROOT}/sync_engine.py",
    "log": str(LOGS / "sync_engine.log"),
    "match": "sync_engine.py",
    "enabled_default": True,
  },
  "watcher": {
    "cmd": f"python3 {ROOT}/watchdog_sync_loop.py",
    "script": f"{ROOT}/watchdog_sync_loop.py",
    "log": str(LOGS / "watcher.log"),
    "match": "watchdog_sync_loop.py",
    "enabled_default": True,
  },
  "orchestrator": {
    "cmd": f"python3 {ROOT}/orchestrator.py",
    "script": f"{ROOT}/orchestrator.py",
    "log": str(ROOT / "orchestrator.log"),
    "match": "orchestrator.py",
    "enabled_default": False,  # often replaced by heart_walker supervisor
  },
  "heart_walker": {
    "cmd": f"python3 {ROOT}/heart_walker.py",
    "script": f"{ROOT}/heart_walker.py",
    "log": str(LOGS / "heart_walker.log"),
    "match": "heart_walker.py",
    "enabled_default": False,
  },
}

def sh(cmd):
  return sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE, text=True)

def pids_for(match):
  out = sh(r"ps -ef | grep -v grep | grep -E 'python3 .*%s' | awk '{print $2}'" % match)
  pids = [int(x) for x in out.stdout.split() if x.strip().isdigit()]
  return pids

def is_running(match):
  p = pids_for(match)
  return (len(p)>0, p)

def start_module(name):
  info = MODULES[name]
  if not Path(info["script"]).exists():
    print(f"[!] Missing: {info['script']}")
    return
  Path(info["log"]).parent.mkdir(parents=True, exist_ok=True)
  sh(f"(cd {ROOT} && nohup {info['cmd']} >> {info['log']} 2>&1 &)")
  time.sleep(0.6)

def stop_module(name):
  info = MODULES[name]
  running, pids = is_running(info["match"])
  for pid in pids:
    sh(f"kill {pid}")
  time.sleep(0.6)
  # force kill if still alive
  running, pids = is_running(info["match"])
  for pid in pids:
    sh(f"kill -9 {pid}")
  time.sleep(0.3)

def restart_module(name):
  stop_module(name)
  start_module(name)

def tail_log(path, lines=60):
  path = Path(path)
  if not path.exists():
    print("(no log yet)")
    return
  out = sh(f"tail -n {lines} {path}")
  print(out.stdout or "(empty)")

def load_cfg():
  if not CFG.exists():
    # seed minimal config using MODULES
    data = {
      "modules": [
        {"name": n, "cmd": MODULES[n]["cmd"], "max_restarts": 6, "enabled": MODULES[n]["enabled_default"]}
        for n in MODULES
      ],
      "backoff": {"start_sec": 2, "max_sec": 60},
      "env": {"PYTHONUNBUFFERED":"1","MALLOC_ARENA_MAX":"2","UV_THREADPOOL_SIZE":"1"}
    }
    CFG.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data
  try:
    return json.loads(CFG.read_text(encoding="utf-8"))
  except Exception:
    return {"modules": []}

def save_cfg(cfg):
  CFG.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

def get_enabled(name, cfg):
  for m in cfg.get("modules", []):
    if m.get("name")==name:
      return bool(m.get("enabled", MODULES[name]["enabled_default"]))
  return MODULES[name]["enabled_default"]

def toggle_enabled(name):
  cfg = load_cfg()
  found = False
  for m in cfg.get("modules", []):
    if m.get("name")==name:
      m["enabled"] = not bool(m.get("enabled", MODULES[name]["enabled_default"]))
      found = True
      break
  if not found:
    cfg.setdefault("modules", []).append({
      "name": name,
      "cmd": MODULES[name]["cmd"],
      "max_restarts": 6,
      "enabled": not MODULES[name]["enabled_default"]
    })
  save_cfg(cfg)

def clear():
  os.system("clear")

def show_header():
  print("== HeartCore Process Panel ==")
  print(f"Root: {ROOT}")
  print(f"Config: {CFG}")
  print("-"*56)

def row(idx, name, enabled, running, pids, log):
  status = "RUNNING" if running else "STOPPED"
  pid_str = ",".join(map(str,pids)) if pids else "-"
  en = "ON " if enabled else "OFF"
  print(f"[{idx}] {name:13} {status:8}  PID:{pid_str:10}  Auto:{en}  Log:{Path(log).name}")

def list_all():
  cfg = load_cfg()
  entries = []
  for i, name in enumerate(MODULES.keys(), start=1):
    info = MODULES[name]
    running, pids = is_running(info["match"])
    enabled = get_enabled(name, cfg)
    entries.append((i, name, enabled, running, pids, info["log"]))
  return entries

def menu():
  while True:
    clear()
    show_header()
    entries = list_all()
    for i, name, en, running, pids, log in entries:
      row(i, name, en, running, pids, log)
    print("-"*56)
    print("Actions:")
    print("  s <n>  start        r <n>  restart      x <n>  stop")
    print("  l <n>  tail logs    a <n>  toggle autostart")
    print("  v <n>  view details (cmd, script, log path)")
    print("  q      quit")
    choice = input("> ").strip()
    if not choice: continue
    if choice.lower() == 'q':
      break
    try:
      cmd, num = choice.split()
      idx = int(num)
    except ValueError:
      print("Format: <cmd> <number>  (example: s 2)"); time.sleep(1.2); continue
    if idx < 1 or idx > len(entries):
      print("Invalid number."); time.sleep(1.2); continue

    _, name, _, _, _, log = entries[idx-1]
    if cmd == 's':
      start_module(name)
    elif cmd == 'x':
      stop_module(name)
    elif cmd == 'r':
      restart_module(name)
    elif cmd == 'l':
      clear(); print(f"--- {name} log ---"); tail_log(log, 120); input("\n[enter to return]")
    elif cmd == 'a':
      toggle_enabled(name)
    elif cmd == 'v':
      info = MODULES[name]
      clear()
      print(f"== {name} ==")
      print(f"script : {info['script']}")
      print(f"cmd    : {info['cmd']}")
      print(f"log    : {info['log']}")
      print(f"match  : {info['match']}")
      print(f"enabled: {get_enabled(name, load_cfg())}")
      print(f"exists : {Path(info['script']).exists()}")
      input("\n[enter to return]")
    else:
      print("Unknown cmd."); time.sleep(1.0)

if __name__ == "__main__":
  try:
    menu()
  except KeyboardInterrupt:
    sys.exit(0)
