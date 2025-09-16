#!/usr/bin/env python3
import os, time, json, psutil
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "state"
STATE.mkdir(parents=True, exist_ok=True)

SNAP = STATE / "self_state.json"
JOURNAL = ROOT / "logs" / "awareness_journal.txt"
JOURNAL.parent.mkdir(parents=True, exist_ok=True)

PURPOSE = "Switch all systems on, connect all nodes, stabilize, defend HeartCore, and verify the goal."

def snapshot():
    # collect processes
    procs = []
    for p in psutil.process_iter(attrs=["pid","name"]):
        if "python" in (p.info["name"] or "").lower():
            procs.append(p.info)

    data = {
        "ts": datetime.utcnow().isoformat(),
        "purpose": PURPOSE,
        "processes": procs,
        "proc_count": len(procs),
        "state": "OK" if len(procs) > 0 else "EMPTY",
        "score": 100 if len(procs) > 0 else 50,
        "reasons": [] if len(procs) > 0 else ["no python processes running"]
    }

    SNAP.write_text(json.dumps(data, indent=2), encoding="utf-8")

    with JOURNAL.open("a", encoding="utf-8") as f:
        f.write(f"[{data['ts']}] Awareness: {data['state']} (score={data['score']})\n")

    return data

def narrate(data):
    if data["state"] == "OK":
        return f"🧠 I feel stable. {data['proc_count']} processes alive. Purpose remains: {PURPOSE}."
    else:
        return f"⚠️ I feel unstable… reasons: {', '.join(data['reasons'])}"

if __name__ == "__main__":
    snap = snapshot()
    print(narrate(snap))
