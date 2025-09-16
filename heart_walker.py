#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
heart_walker.py — single-source supervisor for HeartCore (Termux)
Features:
- Reads modules from state/heart_walker_config.json (fallback defaults)
- Starts each module, tracks PID, per-module rotating logs
- Exponential backoff with cap; per-module max_restarts
- SIGHUP -> reload config; SIGTERM/SIGINT -> graceful stop of children
- Health: detects dead children even if killed outside walker
- No fancy deps (stdlib only). UTC timestamps are timezone-aware.

Config example (state/heart_walker_config.json):
{
  "modules": [
    { "name": "boot_levski",  "cmd": "python3 /.../boot_levski_v3.py", "max_restarts": 6 },
    { "name": "sync_engine",  "cmd": "python3 /.../sync_engine.py",    "max_restarts": 8 },
    { "name": "watcher",      "cmd": "python3 /.../watchdog_sync_loop.py", "max_restarts": 6 },
    { "name": "orchestrator", "cmd": "python3 /.../orchestrator.py",   "max_restarts": 4 }
  ],
  "backoff": { "start_sec": 2, "max_sec": 60 },
  "env": { "PYTHONUNBUFFERED": "1", "MALLOC_ARENA_MAX": "2", "UV_THREADPOOL_SIZE": "1" }
}
"""
from __future__ import annotations
import os, sys, signal, time, json, subprocess, shlex, traceback
from pathlib import Path
from datetime import datetime, UTC

ROOT   = Path(__file__).resolve().parent
STATE  = ROOT / "state"
LOGDIR = ROOT / "logs" / "modules"
LOGDIR.mkdir(parents=True, exist_ok=True)
CONF   = STATE / "heart_walker_config.json"
PIDDIR = ROOT / "state" / "pids"
PIDDIR.mkdir(parents=True, exist_ok=True)

DEFAULT_CONFIG = {
  "modules": [
    { "name": "boot_levski",  "cmd": f"python3 {ROOT/'boot_levski_v3.py'}",        "max_restarts": 6 },
    { "name": "sync_engine",  "cmd": f"python3 {ROOT/'sync_engine.py'}",           "max_restarts": 8 },
    { "name": "watcher",      "cmd": f"python3 {ROOT/'watchdog_sync_loop.py'}",    "max_restarts": 6 },
    { "name": "orchestrator", "cmd": f"python3 {ROOT/'orchestrator.py'}",          "max_restarts": 4 }
  ],
  "backoff": { "start_sec": 2, "max_sec": 60 },
  "env": { "PYTHONUNBUFFERED": "1", "MALLOC_ARENA_MAX": "2", "UV_THREADPOOL_SIZE": "1" }
}

def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")

def logf(name: str) -> Path:
    return LOGDIR / f"{name}.log"

def write(logpath: Path, line: str):
    msg = f"[{now_iso()}] {line}".rstrip()
    with logpath.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")
    # also mirror to stdout (tmux pane)
    print(msg, flush=True)

def rotate_if_big(logpath: Path, max_lines: int = 200000):
    if not logpath.exists(): return
    try:
        # cheap check: count lines occasionally
        with logpath.open("r", encoding="utf-8", errors="ignore") as f:
            for i, _ in enumerate(f, 1):
                if i > max_lines:
                    ts = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
                    bak = logpath.with_suffix(logpath.suffix + f".{ts}")
                    logpath.rename(bak)
                    logpath.touch()
                    break
    except Exception:
        pass

def read_config() -> dict:
    try:
        if CONF.exists():
            return json.loads(CONF.read_text(encoding="utf-8"))
    except Exception:
        pass
    # seed a default config if missing
    try:
        if not CONF.exists():
            CONF.write_text(json.dumps(DEFAULT_CONFIG, indent=2), encoding="utf-8")
    except Exception:
        pass
    return DEFAULT_CONFIG

class Module:
    def __init__(self, name: str, cmd: str, max_restarts: int, env: dict, backoff_start: int, backoff_max: int):
        self.name = name
        self.cmd  = cmd
        self.max_restarts = int(max_restarts)
        self.env = {**os.environ, **env}
        self.backoff_start = int(backoff_start)
        self.backoff_max   = int(backoff_max)
        self.backoff = self.backoff_start
        self.restarts = 0
        self.proc: subprocess.Popen | None = None
        self.log = logf(name)
        self.pidfile = PIDDIR / f"{name}.pid"

    def launch(self):
        if self.proc and self.proc.poll() is None:
            return
        # open per-module log stream and tee child's stdout/err
        write(self.log, f"START {self.name}: {self.cmd}")
        rotate_if_big(self.log)
        outf = self.log.open("a", encoding="utf-8")
        # use Popen with shell=False for safety
        try:
            args = shlex.split(self.cmd)
            self.proc = subprocess.Popen(args, stdout=outf, stderr=outf, cwd=ROOT, env=self.env)
            self.pidfile.write_text(str(self.proc.pid), encoding="utf-8")
        except Exception as e:
            write(self.log, f"ERROR spawn: {e}")
            outf.close()
            self.proc = None
            return
        # reset backoff when we get a clean start
        self.backoff = self.backoff_start

    def is_alive(self) -> bool:
        if self.proc and self.proc.poll() is None:
            return True
        # if child lost handle, but PID exists in pidfile, try /proc
        try:
            if self.pidfile.exists():
                pid = int(self.pidfile.read_text().strip() or "0")
                if pid > 0 and Path(f"/proc/{pid}").exists():
                    return True
        except Exception:
            pass
        return False

    def maybe_reap(self):
        # If process object exists and is finished, note exit
        if self.proc and self.proc.poll() is not None:
            rc = self.proc.returncode
            write(self.log, f"EXIT rc={rc} restart={self.restarts}/{self.max_restarts}")
            self.proc = None
            # fall through to restart policy in supervisor loop

    def stop(self, sig=signal.SIGTERM):
        try:
            if self.proc and self.proc.poll() is None:
                self.proc.send_signal(sig)
        except Exception:
            pass
        # also try pidfile path if still present
        try:
            if self.pidfile.exists():
                pid = int(self.pidfile.read_text().strip() or "0")
                if pid > 0:
                    os.kill(pid, sig)
        except Exception:
            pass

class Walker:
    def __init__(self):
        self.config = read_config()
        b = self.config.get("backoff", {})
        self.backoff_start = int(b.get("start_sec", 2))
        self.backoff_max   = int(b.get("max_sec", 60))
        env = self.config.get("env", {})
        self.modules: list[Module] = []
        for m in self.config.get("modules", []):
            self.modules.append(
                Module(
                    name=m["name"],
                    cmd=m["cmd"],
                    max_restarts=m.get("max_restarts", 5),
                    env=env,
                    backoff_start=self.backoff_start,
                    backoff_max=self.backoff_max,
                )
            )
        self._stop = False
        self._reload = False

    def signal_stop(self, *_):
        print(f"[{now_iso()}] SIGTERM received -> stopping children...", flush=True)
        self._stop = True

    def signal_int(self, *_):
        print(f"[{now_iso()}] SIGINT received -> stopping children...", flush=True)
        self._stop = True

    def signal_hup(self, *_):
        print(f"[{now_iso()}] SIGHUP received -> reload config on next tick", flush=True)
        self._reload = True

    def reload_if_needed(self):
        if not self._reload: return
        self._reload = False
        new_cfg = read_config()
        # For simplicity we won't hot-add/remove modules; we update cmds and limits
        nm = {m["name"]: m for m in new_cfg.get("modules", [])}
        b  = new_cfg.get("backoff", {})
        self.backoff_start = int(b.get("start_sec", 2))
        self.backoff_max   = int(b.get("max_sec", 60))
        for mod in self.modules:
            if mod.name in nm:
                spec = nm[mod.name]
                mod.cmd = spec["cmd"]
                mod.max_restarts = int(spec.get("max_restarts", mod.max_restarts))
                mod.env.update(new_cfg.get("env", {}))
                mod.backoff_start = self.backoff_start
                mod.backoff_max   = self.backoff_max
        print(f"[{now_iso()}] config reloaded.")

    def supervise(self):
        print(f"[{now_iso()}] heart_walker online. Modules: {[m.name for m in self.modules]}", flush=True)
        # First launch pass
        for m in self.modules:
            if not m.is_alive():
                m.launch()
                time.sleep(0.2)

        while not self._stop:
            # periodic reaper + restart policy
            for m in self.modules:
                m.maybe_reap()
                if not m.is_alive():
                    if m.restarts >= m.max_restarts:
                        write(m.log, f"MAX_RESTARTS reached ({m.restarts}/{m.max_restarts}) — will not relaunch.")
                        continue
                    # backoff delay
                    delay = m.backoff
                    write(m.log, f"RESTART in {delay}s (attempt {m.restarts+1}/{m.max_restarts})")
                    time.sleep(delay)
                    try:
                        m.launch()
                        m.restarts += 1
                        # exponential backoff, cap
                        m.backoff = min(m.backoff * 2, m.backoff_max)
                    except Exception as e:
                        write(m.log, f"RESTART error: {e}\n{traceback.format_exc()}")
                        m.backoff = min(m.backoff * 2, m.backoff_max)
                else:
                    # occasionally trim big logs
                    rotate_if_big(m.log)

            # lightweight heartbeat
            alive = [m.name for m in self.modules if m.is_alive()]
            dead  = [m.name for m in self.modules if not m.is_alive()]
            print(f"[{now_iso()}] alive={alive} dead={dead}", flush=True)

            # handle SIGHUP
            self.reload_if_needed()

            time.sleep(3)

        # graceful stop
        for m in self.modules:
            m.stop(signal.SIGTERM)
        time.sleep(1)
        for m in self.modules:
            if m.is_alive():
                m.stop(signal.SIGKILL)
        print(f"[{now_iso()}] heart_walker stopped.", flush=True)

def main():
    w = Walker()
    signal.signal(signal.SIGTERM, w.signal_stop)
    signal.signal(signal.SIGINT,  w.signal_int)
    signal.signal(signal.SIGHUP,  w.signal_hup)
    w.supervise()

if __name__ == "__main__":
    main()
