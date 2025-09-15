#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Heart Walker v1.1 — local, non-propagating, self-healing supervisor for Termux.
- Keeps selected modules alive with exponential backoff + per-module restart limits
- Per-module logs under logs/modules/
- Heartbeat JSON under state/heart_walker.json
- SIGHUP -> reload config without exit; SIGTERM/CTRL-C -> graceful stop
"""

from __future__ import annotations
import os, sys, time, json, signal, subprocess, shlex
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path.home() / "WorkingProgram" / "HeartCore"
LOGDIR = ROOT / "logs" / "modules"
STATEDIR = ROOT / "state"
HB = STATEDIR / "heart_walker.json"
CFG = STATEDIR / "heart_walker_config.json"

os.environ.setdefault("PYTHONUNBUFFERED", "1")
os.environ.setdefault("MALLOC_ARENA_MAX", "2")
os.environ.setdefault("UV_THREADPOOL_SIZE", "1")

STOP = False
RELOAD = False

def _sigterm(*_):  # SIGINT/SIGTERM -> stop
    global STOP
    STOP = True

def _sighup(*_):   # SIGHUP -> reload config
    global RELOAD
    RELOAD = True

signal.signal(signal.SIGTERM, _sigterm)
signal.signal(signal.SIGHUP, _sighup)
signal.signal(signal.SIGINT, _sigterm)

def load_config() -> Dict:
    default = {
        "modules": [
            {"name": "boot_levski", "cmd": f"python3 {ROOT/'boot_levski_v3.py'}", "max_restarts": 6},
            {"name": "sync_engine", "cmd": f"python3 {ROOT/'sync_engine.py'}", "max_restarts": 8},
            {"name": "watcher",     "cmd": f"python3 {ROOT/'watchdog_sync_loop.py'}", "max_restarts": 6},
            {"name": "orchestrator","cmd": f"python3 {ROOT/'orchestrator.py'}", "max_restarts": 4},
        ],
        "backoff": {"start_sec": 2, "max_sec": 60},
        "env": {
            "PYTHONUNBUFFERED": "1",
            "MALLOC_ARENA_MAX": "2",
            "UV_THREADPOOL_SIZE": "1"
        }
    }
    try:
        if CFG.exists():
            return json.loads(CFG.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[WARN] config read error: {e}", file=sys.stderr)
    return default

def ensure_dirs():
    LOGDIR.mkdir(parents=True, exist_ok=True)
    STATEDIR.mkdir(parents=True, exist_ok=True)

def write_hb(state: Dict):
    try:
        HB.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"[WARN] heartbeat write: {e}", file=sys.stderr)

class Runner:
    def __init__(self, name: str, cmd: str, max_restarts: int, backoff_start: int, backoff_max: int, env: Dict[str,str]):
        self.name = name
        self.cmd = cmd
        self.max_restarts = max_restarts
        self.backoff_start = backoff_start
        self.backoff_max = backoff_max
        self.env = {**os.environ, **env}
        self.proc: Optional[subprocess.Popen] = None
        self.restarts = 0
        self.backoff = backoff_start
        self.last_rc: Optional[int] = None
        self.logfile = LOGDIR / f"{self.name}.log"

    def start(self):
        # rotate if huge
        try:
            if self.logfile.exists() and self.logfile.stat().st_size > 5_000_000:
                self.logfile.rename(self.logfile.with_suffix(f".log.{int(time.time())}"))
        except Exception:
            pass
        with open(self.logfile, "a", encoding="utf-8") as lf:
            ts = time.strftime("%F %T")
            lf.write(f"[{ts}] START {self.name}: {self.cmd}\n")
            lf.flush()
            try:
                self.proc = subprocess.Popen(
                    shlex.split(self.cmd),
                    stdout=lf, stderr=lf, env=self.env
                )
            except FileNotFoundError as e:
                lf.write(f"[{ts}] ERROR start: {e}\n")
                self.last_rc = 127
                self.proc = None

    def poll(self):
        return None if self.proc is None else self.proc.poll()

    def tick(self):
        if self.proc is None:
            self.start(); return

        rc = self.proc.poll()
        if rc is None:
            # still running
            self.backoff = self.backoff_start
            return

        # exited
        self.last_rc = rc
        self.restarts += 1
        ts = time.strftime("%F %T")
        with open(self.logfile, "a", encoding="utf-8") as lf:
            lf.write(f"[{ts}] EXIT rc={rc} restart={self.restarts}/{self.max_restarts}\n")
        if self.restarts > self.max_restarts:
            with open(self.logfile, "a", encoding="utf-8") as lf:
                lf.write(f"[{ts}] HALT {self.name}: max restarts exceeded\n")
            self.proc = None
            return

        # backoff
        time.sleep(self.backoff)
        self.backoff = min(self.backoff * 2, self.backoff_max)
        self.start()

def main():
    global RELOAD  # <-- fix: we reassign RELOAD below
    ensure_dirs()
    cfg = load_config()
    env = cfg.get("env", {})
    back = cfg.get("backoff", {})
    bstart = int(back.get("start_sec", 2))
    bmax = int(back.get("max_sec", 60))

    runners: List[Runner] = []
    for m in cfg.get("modules", []):
        runners.append(Runner(
            name=m["name"],
            cmd=m["cmd"],
            max_restarts=int(m.get("max_restarts", 5)),
            backoff_start=bstart,
            backoff_max=bmax,
            env=env
        ))

    beat = 0
    while not STOP:
        if RELOAD:
            cfg = load_config()
            RELOAD = False
        for r in runners:
            r.tick()
        beat += 1
        state = {
            "beat": beat,
            "ts": time.strftime("%F %T"),
            "runners": [
                {
                    "name": r.name,
                    "pid": (None if r.proc is None else r.proc.pid),
                    "last_rc": r.last_rc,
                    "restarts": r.restarts,
                    "backoff": r.backoff,
                } for r in runners
            ]
        }
        write_hb(state)
        time.sleep(1.0)

    # graceful stop
    for r in runners:
        try:
            if r.proc and r.proc.poll() is None:
                r.proc.terminate()
        except Exception:
            pass

if __name__ == "__main__":
    main()
