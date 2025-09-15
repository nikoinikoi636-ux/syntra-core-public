import json, re, shutil
from pathlib import Path
from .utils import ts, load_json, save_json

def load_policy(path: Path):
    return load_json(path, {"deny_patterns":[], "allow_patterns":[], "hard_quarantine":[]})

def check_text(text: str, policy: dict) -> dict:
    allows = [re.compile(p, re.IGNORECASE) for p in policy.get("allow_patterns",[])]
    denys  = [re.compile(p, re.IGNORECASE) for p in policy.get("deny_patterns",[])]
    hards  = [re.compile(item.get("pattern",""), re.IGNORECASE) for item in policy.get("hard_quarantine",[])]

    allowed = any(rx.search(text) for rx in allows) if allows else False
    hits_deny = [p.pattern for p in denys if p.search(text)]
    hits_hard = [p.pattern for p in hards if p.search(text)]

    verdict = "OK"
    if hits_hard:
        verdict = "HARD_QUARANTINE"
    elif hits_deny and not allowed:
        verdict = "DENY"
    return {"verdict": verdict, "deny_hits": hits_deny, "hard_hits": hits_hard, "allowed": allowed}

def scan_tree(src: Path, out_dir: Path, policy_path: Path) -> Path:
    policy = load_policy(policy_path)
    report = {"ts": ts(), "policy": str(policy_path), "files": []}
    qdir = out_dir / "quarantine"
    qdir.mkdir(parents=True, exist_ok=True)

    for f in src.rglob("*"):
        if not f.is_file():
            continue
        try:
            data = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            # binary or unreadable
            data = ""
        res = check_text(data, policy)
        item = {"file": str(f), **res}
        report["files"].append(item)
        if res["verdict"] == "HARD_QUARANTINE":
            dest = qdir / f.name
            try:
                shutil.copy2(str(f), str(dest))
            except Exception:
                pass

    out_path = out_dir / "policy_report.json"
    save_json(out_path, report)
    return out_path
