#!/usr/bin/env python3
import json, datetime
from pathlib import Path

DEFAULT_MATRIX = {
    "data_analysis": {"current": 75, "target": 100},
    "code_generation": {"current": 70, "target": 100},
    "system_architecture": {"current": 80, "target": 100},
    "multi_language": {"current": 65, "target": 95},
    "creative_reasoning": {"current": 60, "target": 98},
    "autonomous_learning": {"current": 0, "target": 0},
    "cross_domain_synthesis": {"current": 60, "target": 90}
}

class TranscendenceEngine:
    def __init__(self, state_dir: Path):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.state_dir / "state.json"
        if self.state_path.exists():
            self.state = json.loads(self.state_path.read_text(encoding="utf-8"))
        else:
            self.state = {
                "level": "Toolkit_v1",
                "created_at": datetime.datetime.utcnow().isoformat() + "Z",
                "capabilities": DEFAULT_MATRIX,
                "history": [],
                "feedback": []
            }
            self._save()

    def _save(self):
        self.state_path.write_text(json.dumps(self.state, indent=2, ensure_ascii=False), encoding="utf-8")

    def _gap(self, cur, tgt):
        try:
            return max(0, int(tgt) - int(cur))
        except Exception:
            return 0

    def propose_plan(self):
        caps = self.state["capabilities"]
        gaps = sorted(((k, self._gap(v["current"], v["target"])) for k, v in caps.items()), key=lambda x: -x[1])
        top = [k for k, g in gaps[:3] if g > 0]
        plan = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "focus": top,
            "actions": [
                "Collect human feedback on recent outputs (1-5 rating)",
                "Add test cases/examples for weak areas",
                "Refactor templates to cover missing patterns",
                "Run evaluate cycle and re-rank gaps"
            ]
        }
        self.state["history"].append({"event": "plan", "data": plan})
        self._save()
        return plan

    def evaluate_once(self):
        caps = self.state["capabilities"]
        gaps = sorted(((k, self._gap(v["current"], v["target"])) for k, v in caps.items()), key=lambda x: -x[1])
        improved = []
        for k, g in gaps[:2]:
            if g > 0:
                caps[k]["current"] = min(caps[k]["current"] + 1, caps[k]["target"])
                improved.append(k)
        snap = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "improved": improved,
            "capabilities": caps
        }
        self.state["history"].append({"event": "evaluate", "data": snap})
        self._save()
        return snap

    def record_feedback(self, fb: dict):
        self.state["feedback"].append(fb)
        ratings = [x.get("rating", 0) for x in self.state["feedback"] if isinstance(x.get("rating", 0), int)]
        if ratings:
            avg = sum(ratings) / max(1, len(ratings))
            if avg >= 4:
                cap = self.state["capabilities"]["creative_reasoning"]
                cap["current"] = min(cap["current"] + 1, cap["target"])
        self._save()
