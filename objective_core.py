#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Objective Core — single source of truth for the system's Main Objective.

Main Objective (default):
  "Switch all systems on, connect all nodes, stabilize, defend HeartCore, and verify the goal."

CLI: set | get | status | activate
"""
from __future__ import annotations
import argparse, json, os, re, subprocess, sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Optional, Tuple

HOME = Path("~").expanduser()
CENTRAL = HOME / "central_core"
STORE = CENTRAL / "objective.json"
LOGS = HOME / "HeartCore_OS_v1" / "logs"
CODEX = LOGS / "paradox_codex.md"
HEART_ROOT = HOME / "WorkingProgram" / "HeartCore"

DEFAULT_OBJECTIVE = (
    "Switch all systems on, connect all nodes, stabilize, defend HeartCore, and verify the goal."
)

@dataclass
class ObjectiveState:
    purpose: str = DEFAULT_OBJECTIVE
    active: bool = False
    last_status: str = "unknown"

class ObjectiveManager:
    def __init__(self, store: Path = STORE) -> None:
        self.store = store
        self.state = self._load()

    def _load(self) -> ObjectiveState:
        try:
            return ObjectiveState(**json.loads(self.store.read_text(encoding="utf-8")))
        except Exception:
            return ObjectiveState()

    def _save(self) -> None:
        self.store.parent.mkdir(parents=True, exist_ok=True)
        self.store.write_text(json.dumps(asdict(self.state), ensure_ascii=False, indent=2), encoding="utf-8")

    def set_purpose(self, text: str) -> None:
        self.state.purpose = (text or DEFAULT_OBJECTIVE).strip()
        self._save()

    def get_purpose(self) -> str:
        return self.state.purpose

    def ensure_systems_on(self) -> Dict[str, str]:
        results: Dict[str, str] = {}
        results["heart_root"] = "OK" if HEART_ROOT.exists() else "MISSING"
        def _launch(label: str, rel: str) -> None:
            path = HEART_ROOT / rel
            if path.exists():
                try:
                    subprocess.Popen(("python3", str(path)), cwd=str(HEART_ROOT),
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    results[label] = "LAUNCHED"
                except Exception as e:
                    results[label] = f"SKIP:{e.__class__.__name__}"
            else:
                results[label] = "MISSING"
        # bring up core helpers (best-effort)
        _launch("speech", "speech_script.py")
        _launch("boot_levski", "boot_levski_v3.py")
        _launch("sync_engine", "sync_engine.py")
        _launch("watchdog", "watchdog_sync_loop.py")
        return results

    def check_goal(self) -> Dict[str, str]:
        report: Dict[str, str] = {}
        manifest = HEART_ROOT / "Prime_Heart_Vault_Beacon.manifest"
        report["manifest"] = "OK" if manifest.exists() else "MISSING"
        if CODEX.exists():
            t = CODEX.read_text(encoding="utf-8")
            cnt = t.count("### Cycle ")
            report["codex_cycles"] = str(cnt)
            report["codex_ok"] = "OK" if cnt == 1000 else "ISSUES"
        else:
            report["codex_cycles"] = "N/A"
            report["codex_ok"] = "SKIP"
        orch = HEART_ROOT / "orchestrator.py"
        report["orchestrator"] = "OK" if orch.exists() else "MISSING"
        try:
            ps = subprocess.check_output(["ps"], text=True)
            report["orchestrator_running"] = "YES" if re.search(r"python3 .*orchestrator\.py", ps) else "NO"
        except Exception:
            report["orchestrator_running"] = "UNKNOWN"
        ok = (report.get("manifest")=="OK" and report.get("codex_ok") in ("OK","SKIP") and report.get("orchestrator")=="OK")
        self.state.last_status = "OK" if ok else "ISSUES"
        self._save()
        return report

    def activate(self, purpose: Optional[str] = None):
        if purpose:
            self.set_purpose(purpose)
        self.state.active = True
        self._save()
        bringup = self.ensure_systems_on()
        checks = self.check_goal()
        return {"purpose": self.state.purpose, "bringup": bringup, "checks": checks, "status": self.state.last_status}

def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Objective Core CLI")
    p.add_argument("cmd", choices=["set","get","status","activate"])
    p.add_argument("--purpose", type=str, default="")
    return p

def main(argv=None) -> int:
    args = _parser().parse_args(argv)
    om = ObjectiveManager()
    if args.cmd == "set":
        om.set_purpose(args.purpose or DEFAULT_OBJECTIVE)
        print("[OK] purpose set"); print(om.get_purpose()); return 0
    if args.cmd == "get":
        print(om.get_purpose()); return 0
    if args.cmd == "status":
        print(json.dumps(asdict(om.state), ensure_ascii=False, indent=2)); return 0
    if args.cmd == "activate":
        out = om.activate(purpose=args.purpose or DEFAULT_OBJECTIVE)
        print(json.dumps(out, ensure_ascii=False, indent=2)); return 0
    return 1

if __name__ == "__main__":
    raise SystemExit(main())

# --- HeartCore Purpose Writer ---
from pathlib import Path
import json
try:
    PURPOSE_TEXT = PURPOSE if "PURPOSE" in globals() else purpose if "purpose" in locals() else "(none)"
    state_dir = Path.home() / "WorkingProgram" / "HeartCore" / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    purpose_file = state_dir / "purpose.json"
    purpose_file.write_text(json.dumps({"purpose": PURPOSE_TEXT}, indent=2), encoding="utf-8")
except Exception as e:
    print(f"[warn] could not write purpose.json: {e}")
# --- End HeartCore Purpose Writer ---
