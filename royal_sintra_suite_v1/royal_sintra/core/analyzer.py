import re, json
from pathlib import Path
import yaml

def load_rules(yaml_path: Path):
    text = yaml_path.read_text(encoding="utf-8")
    rules = []
    current = None
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("- id:"):
            if current: rules.append(current)
            current = {"id": line.split(":")[1].strip(), "pattern":"", "severity":"MEDIUM"}
        elif line.startswith("pattern:"):
            pat = line.split(":",1)[1].strip()
            pat = pat.strip("'").strip('"')
            current["pattern"] = pat
        elif line.startswith("severity:"):
            current["severity"] = line.split(":",1)[1].strip()
    if current: rules.append(current)
    return rules

def analyze(ev_dir: Path, rules_path: Path) -> (Path, Path):
    norm = ev_dir / "normalized.jsonl"
    anomalies_path = ev_dir / "anomalies.json"
    summary_md = ev_dir / "summary.md"

    rules = load_rules(rules_path)
    comp = [(r["id"], re.compile(r["pattern"], re.IGNORECASE), r["severity"]) for r in rules]

    matches = []
    counts = {}
    total = 0
    if not norm.exists():
        raise FileNotFoundError(f"Missing normalized.jsonl: {norm}")

    with norm.open("r", encoding="utf-8") as f:
        for line in f:
            total += 1
            try:
                rec = json.loads(line)
            except Exception:
                continue
            msg = rec.get("msg","")
            for rid, rx, sev in comp:
                if rx.search(msg):
                    out = {
                        "rule": rid,
                        "severity": sev,
                        "ts": rec.get("ts"),
                        "level": rec.get("level"),
                        "source": rec.get("source"),
                        "lineno": rec.get("lineno"),
                        "msg": msg
                    }
                    matches.append(out)
                    counts[rid] = counts.get(rid, 0) + 1

    anomalies_path.write_text(json.dumps({"matches": matches, "counts": counts}, ensure_ascii=False, indent=2), encoding="utf-8")
    with summary_md.open("w", encoding="utf-8") as out:
        out.write(f"# Anomaly Summary\n\n")
        out.write(f"- Total records scanned: ~{total}\n")
        out.write(f"- Total matches: {len(matches)}\n\n")
        if counts:
            out.write("## Matches by rule\n")
            for rid, c in sorted(counts.items(), key=lambda x: x[1], reverse=True):
                out.write(f"- {rid}: {c}\n")
        out.write("\n## Notes\n- Rules are heuristic; verify in source context.\n")

    return anomalies_path, summary_md
