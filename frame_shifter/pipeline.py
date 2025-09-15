
import os, re, json, datetime
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

class HeartFilter:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg or {}
        self.block_phrases = [re.compile(p) for p in self.cfg.get("block_phrases", [])]
        self.redact_pattern = re.compile(self.cfg.get("redact_pattern", r"(?!)"))
        self.redact_replacement = self.cfg.get("redact_replacement", "REDACTED")

    def run(self, text: str) -> StepResult:
        blocked = []
        for rx in self.block_phrases:
            if rx.search(text or ""):
                blocked.append(rx.pattern)
        redacted = self.redact_pattern.sub(self.redact_replacement, text or "")
        return StepResult("heart", redacted, {"blocked_patterns": blocked, "redacted": redacted != text})

class MirrorLogic:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg or {}

    def _normalize(self, s: str) -> str:
        out = s or ""
        if self.cfg.get("strip_surrounding_quotes", True):
            if (out.startswith('"') and out.endswith('"')) or (out.startswith("'") and out.endswith("'")):
                out = out[1:-1]
        if self.cfg.get("normalize_whitespace", True):
            out = re.sub(r"[ \t]+", " ", out)
            out = re.sub(r"\s+\n", "\n", out)
            out = re.sub(r"\n{3,}", "\n\n", out).strip()
        if self.cfg.get("collapse_punctuation", True):
            out = re.sub(r"([!?.,]){3,}", r"\1\1", out)
        max_len = int(self.cfg.get("max_len", 20000))
        if len(out) > max_len:
            out = out[:max_len] + "\n...[truncated]"
        return out

    def run(self, text: str) -> StepResult:
        normalized = self._normalize(text or "")
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', normalized) if s.strip()]
        hints = []
        if len(sentences) > 3 and any(len(s) > 200 for s in sentences):
            hints.append("Consider shorter sentences for readability.")
        if normalized.count("\n") == 0 and len(normalized) > 200:
            hints.append("Consider splitting paragraphs with newlines.")
        return StepResult("mirror", normalized, {"hints": hints, "len": len(normalized)})

class SymbolicCore:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg or {}
        self.triggers = self.cfg.get("triggers", {})

    def run(self, text: str) -> StepResult:
        fired = []
        for key, tags in (self.triggers or {}).items():
            if key in (text or ""):
                fired.append({"key": key, "tags": tags})
        return StepResult("symbolic", text, {"triggers": fired})

class EntityCore:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg or {}
        self.todo_rx = re.compile(self.cfg.get("todo_pattern", r"(?!)"))
        self.cmd_rx = re.compile(self.cfg.get("command_pattern", r"(?!)"))

    def run(self, text: str) -> StepResult:
        todos = self.todo_rx.findall(text or "") if self.cfg.get("extract_todos", True) else []
        cmds = self.cmd_rx.findall(text or "") if self.cfg.get("extract_commands", True) else []
        plan = []
        for i, t in enumerate(todos, 1):
            plan.append({"step": i, "type":"TODO", "task": t.strip()})
        for j, c in enumerate(cmds, 1):
            plan.append({"step": len(plan)+1, "type":"CMD", "cmd": c.strip()})
        return StepResult("entity", text, {"plan": plan, "todos": todos, "commands": cmds})

class ElderCore:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg or {}
        self.log_dir = self.cfg.get("log_dir", "./logs")
        self.log_file = self.cfg.get("log_file", "frame_shifter.log.jsonl")
        os.makedirs(self.log_dir, exist_ok=True)
        self.path = os.path.join(self.log_dir, self.log_file)

    def record(self, payload: dict):
        payload = dict(payload)
        payload["timestamp"] = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def run(self, steps: List[StepResult]) -> StepResult:
        entry = {"event": "frame_shift", "steps": [{ "name": s.name, "meta": s.meta } for s in steps]}
        self.record(entry)
        return StepResult("elder", steps[-1].content if steps else "", {"log": self.path})

class FrameShifter:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg or {}
        self.heart = HeartFilter(self.cfg.get("heart", {}))
        self.mirror = MirrorLogic(self.cfg.get("mirror", {}))
        self.symbolic = SymbolicCore(self.cfg.get("symbolic", {}))
        self.entity = EntityCore(self.cfg.get("entity", {}))
        self.elder = ElderCore(self.cfg.get("elder", {}))

    def shift(self, text: str) -> Dict[str, Any]:
        s1 = self.heart.run(text)
        s2 = self.mirror.run(s1.content)
        s3 = self.symbolic.run(s2.content)
        s4 = self.entity.run(s3.content)
        s5 = self.elder.run([s1, s2, s3, s4])
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
