import json
from pathlib import Path
from .utils import ts, load_json, save_json

def join_heart(base: Path, name: str, tags: str = ""):
    bionet = base / ".bionet"
    reg = bionet / "registry.json"
    sig = bionet / "signals.jsonl"
    bionet.mkdir(parents=True, exist_ok=True)

    reg_data = load_json(reg, {"nodes": {}, "created": ts(), "version": 2})
    node = {
        "name": name,
        "tags": [t.strip() for t in tags.split(",") if t.strip()],
        "joined": ts()
    }
    reg_data["nodes"][name] = node
    save_json(reg, reg_data)

    with sig.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": ts(), "topic": "join", "node": name, "tags": node["tags"]}, ensure_ascii=False) + "\n")

    return reg, sig
