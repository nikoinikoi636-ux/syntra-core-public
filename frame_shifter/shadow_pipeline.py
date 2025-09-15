
import os, re, json
from dataclasses import dataclass, field
from typing import Dict, Any, List

def load_config(path: str = None) -> Dict[str, Any]:
    if not path or not os.path.exists(path):
        from importlib import resources
        try:
            with resources.open_text("frame_shifter", "default_config.json") as f:
                return json.load(f)
        except Exception:
            return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@dataclass
class StepResult:
    name: str
    content: str
    meta: Dict[str, Any] = field(default_factory=dict)

class GreedFilter:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg or {}
        red = self.cfg.get("heart",{})
        self.redact_pattern = re.compile(red.get("redact_pattern", r"(?!)"))
        self.redact_replacement = red.get("redact_replacement", "REDACTED")

    def run(self, text: str) -> StepResult:
        t = text or ""
        emphasized = re.sub(r"\b(critical|profit|power|control)\b", lambda m: m.group(1).upper(), t, flags=re.I)
        emphasized = re.sub(r"(!+)", r"!!", emphasized)
        redacted = self.redact_pattern.sub(self.redact_replacement, emphasized)
        return StepResult("greed", redacted, {"redacted": redacted != emphasized})

class Distortion:
    def run(self, text: str) -> StepResult:
        t = text or ""
        t = re.sub(r"\s{3,}", " .. ", t)
        words = t.split()
        if words:
            last = words[-1]
            if len(last) > 4:
                t += " " + last + "..."
        t = re.sub(r"([.?!])", r"\1..", t)
        return StepResult("distortion", t, {"note": "shadow-distortion applied"})

class FearTriggers:
    def __init__(self):
        self.lex = ["хаос","криза","заплаха","катастрофа","война","разпад"]

    def run(self, text: str) -> StepResult:
        t = text or ""
        triggers = [w for w in self.lex if w in t.lower()]
        return StepResult("fear", t, {"fear_triggers": triggers})

class ChaosPlan:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg or {}
        self.cmd_rx = re.compile(r"(?m)^\s*(?:\$|bash:|cmd:)\s*(.+)$")
        self.todo_rx = re.compile(r"(?mi)\b(?:TODO|DO THIS|НАПРАВИ)\b[:\-]?\s*(.+)$")

    def run(self, text: str) -> StepResult:
        cmds = self.cmd_rx.findall(text or "")
        todos = self.todo_rx.findall(text or "")
        plan = []
        for i, t in enumerate(todos, 1):
            plan.append({"step": i, "mode":"shadow", "twist":"misuse", "task": t.strip()})
        for j, c in enumerate(cmds, 1):
            plan.append({"step": len(plan)+1, "mode":"shadow", "twist":"misuse", "cmd": c.strip()})
        return StepResult("chaos", text, {"shadow_plan": plan})

class Forgetter:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg or {}
        self.log_dir = self.cfg.get("elder",{}).get("log_dir", "./logs")
        self.log_file = "frame_shifter_shadow.log.jsonl"
        os.makedirs(self.log_dir, exist_ok=True)
        self.path = os.path.join(self.log_dir, self.log_file)

    def run(self, steps: List[StepResult]) -> StepResult:
        entry = {"event":"shadow_shift","steps":[{"name":s.name,"meta":s.meta} for s in steps]}
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False)+"\n")
        return StepResult("forgetter", steps[-1].content if steps else "", {"log": self.path})

class ShadowShifter:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg or {}
        self.greed = GreedFilter(self.cfg)
        self.dist = Distortion()
        self.fear = FearTriggers()
        self.chaos = ChaosPlan(self.cfg)
        self.forgetter = Forgetter(self.cfg)

    def shift(self, text: str) -> Dict[str, Any]:
        s1 = self.greed.run(text)
        s2 = self.dist.run(s1.content)
        s3 = self.fear.run(s2.content)
        s4 = self.chaos.run(s3.content)
        s5 = self.forgetter.run([s1, s2, s3, s4])
        return {
            "output": s4.content,
            "steps": [
                {"name": s1.name, "meta": s1.meta},
                {"name": s2.name, "meta": s2.meta},
                {"name": s3.name, "meta": s3.meta},
                {"name": s4.name, "meta": s4.meta},
                {"name": s5.name, "meta": s5.meta},
            ]
        }
