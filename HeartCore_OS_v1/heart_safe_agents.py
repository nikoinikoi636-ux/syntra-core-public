#!/usr/bin/env python3
# file: heart_safe_agents.py
import argparse, csv, hashlib, json, os, re, sys, time
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

VERSION = "1.0.0"

def eprint(*a, **k): print(*a, file=sys.stderr, **k)

def iter_files(root: Path):
    for p in root.rglob("*"):
        if p.is_file():
            yield p

def sha256_file(p: Path, buf_size=1024*1024):
    h = hashlib.sha256()
    with p.open("rb") as f:
        while True:
            b = f.read(buf_size)
            if not b: break
            h.update(b)
    return h.hexdigest()

def sniff_delimiter(sample_path: Path):
    try:
        with sample_path.open("r", encoding="utf-8", errors="replace") as f:
            sample = f.read(4096)
        return csv.Sniffer().sniff(sample).delimiter
    except Exception:
        return ","

# Agent: TRUTH
def agent_truth(args):
    # Scan text/CSV for duplicate lines, numeric jumps, date anomalies
    path = Path(args.path)
    if not path.exists():
        eprint("Файлът/папката не съществува."); sys.exit(2)

    reports = []

    def analyze_text_file(p: Path):
        try:
            lines = [ln.strip() for ln in p.read_text(encoding="utf-8", errors="replace").splitlines()]
        except Exception as ex:
            return {"file": str(p), "error": str(ex)}

        dup_lines = [ln for ln, cnt in Counter(lines).items() if ln and cnt > 1]
        numbers = []
        dates = []
        num_re = re.compile(r"(-?\d+(?:[\.,]\d+)*)")
        date_re = re.compile(r"\b(20\d{2}|19\d{2})[-/\.]([01]?\d|1[0-2])[-/\.]([0-3]?\d)\b")
        for i, ln in enumerate(lines, 1):
            for m in num_re.findall(ln):
                try:
                    n = float(m.replace(",", "."))
                    numbers.append((i, n))
                except: pass
            for m in date_re.findall(ln):
                try:
                    y, mo, da = int(m[0]), int(m[1]), int(m[2])
                    dates.append((i, datetime(y, mo, da)))
                except: pass

        suspicious_jumps = []
        if len(numbers) >= 2:
            last = numbers[0][1]
            for (lineno, n) in numbers[1:]:
                if last != 0 and abs(n-last)/max(1.0, abs(last)) > 5:
                    suspicious_jumps.append({"line": lineno, "prev": last, "curr": n})
                last = n

        date_order = "unknown"
        if len(dates) >= 2:
            asc = all(dates[i][1] <= dates[i+1][1] for i in range(len(dates)-1))
            desc = all(dates[i][1] >= dates[i+1][1] for i in range(len(dates)-1))
            date_order = "ascending" if asc else ("descending" if desc else "mixed")

        return {
            "file": str(p),
            "duplicate_lines_count": len(dup_lines),
            "duplicate_lines_sample": dup_lines[:10],
            "suspicious_numeric_jumps": suspicious_jumps[:20],
            "date_sequence": date_order,
            "lines": len(lines)
        }

    def analyze_csv_file(p: Path):
        delim = sniff_delimiter(p)
        rows = []
        with p.open("r", encoding="utf-8", errors="replace") as f:
            r = csv.reader(f, delimiter=delim)
            for row in r:
                if row: rows.append(row)
        if not rows:
            return {"file": str(p), "type":"csv", "rows": 0}

        cols = list(zip(*rows)) if rows else []
        numeric_cols = []
        outliers = []
        for idx, col in enumerate(cols):
            values = []
            for v in col[1:]:
                try:
                    values.append(float(v.replace(",", ".").strip()))
                except: pass
            if len(values) >= 5:
                numeric_cols.append(idx)
                mean = sum(values)/len(values)
                var = sum((x-mean)**2 for x in values)/len(values)
                sd = var**0.5
                flagged = []
                if sd > 0:
                    for i, v in enumerate(values, start=2):
                        if abs(v-mean) > 4*sd:
                            flagged.append({"row": i, "value": v, "mean": mean, "sd": sd})
                if flagged:
                    outliers.append({"column_index": idx, "count": len(flagged), "samples": flagged[:10]})

        dupe_rows = [tuple(r) for r, c in Counter(tuple(r) for r in rows).items() if c > 1]

        return {
            "file": str(p), "type":"csv", "rows": len(rows),
            "numeric_columns": numeric_cols,
            "outliers": outliers[:10],
            "duplicate_rows_count": len(dupe_rows),
            "duplicate_rows_sample": dupe_rows[:5]
        }

    targets = []
    if path.is_dir():
        for p in iter_files(path):
            targets.append(p)
    else:
        targets = [path]

    for p in targets:
        low = p.suffix.lower()
        if low in {".csv"}:
            reports.append(analyze_csv_file(p))
        elif low in {".txt", ".md", ".log", ".json"}:
            reports.append(analyze_text_file(p))
        else:
            try:
                if p.stat().st_size < 2_000_000:
                    reports.append(analyze_text_file(p))
            except: pass

    print(json.dumps({"agent":"truth","version":VERSION,"reports":reports}, ensure_ascii=False, indent=2))

# Agent: INTEGRITY
def agent_integrity(args):
    root = Path(args.path)
    manifest_path = Path(args.manifest)
    if args.command == "build":
        entries = []
        for f in iter_files(root):
            rel = str(f.relative_to(root))
            entries.append({"path": rel, "sha256": sha256_file(f), "size": f.stat().st_size})
        data = {"version": VERSION, "root": str(root), "created": int(time.time()), "entries": entries}
        manifest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Манифест записан: {manifest_path}")
    elif args.command == "verify":
        if not manifest_path.exists():
            eprint("Липсва manifest."); sys.exit(2)
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        missing = []
        changed = []
        for ent in data.get("entries", []):
            p = root / ent["path"]
            if not p.exists():
                missing.append(ent["path"])
                continue
            h = sha256_file(p)
            if h != ent["sha256"]:
                changed.append(ent["path"])
        result = {"missing": missing, "changed": changed, "ok": not missing and not changed}
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        eprint("Невалидна команда за integrity."); sys.exit(2)

# Agent: HONOR (git hygiene)
def agent_honor(args):
    from subprocess import run, PIPE
    repo = Path(args.repo)
    if not (repo / ".git").exists():
        eprint("Не е Git repo."); sys.exit(2)
    r = run(["git","-C",str(repo),"status","--porcelain","-b"], stdout=PIPE, stderr=PIPE, text=True)
    if r.returncode != 0:
        eprint(r.stderr.strip()); sys.exit(2)
    lines = r.stdout.strip().splitlines()
    branch = lines[0].replace("## ","") if lines else "unknown"
    changes = [ln for ln in lines[1:] if ln.strip()]
    advice = []
    if changes:
        advice.append("ИМА неприбрани промени. Помисли: git add/commit/push.")
    if "ahead" in branch and "behind" in branch:
        advice.append("Разминаване с remote – помисли за rebase/merge.")
    elif "ahead" in branch:
        advice.append("Локални комити не са пушнати – направи git push.")
    elif "behind" in branch:
        advice.append("Изоставаш от remote – git pull --rebase.")
    print(json.dumps({"agent":"honor","branch":branch,"changes":changes,"advice":advice}, ensure_ascii=False, indent=2))

# Agent: BALANCE (budget CSV)
def agent_balance(args):
    path = Path(args.csv)
    if not path.exists():
        eprint("Няма такъв CSV."); sys.exit(2)
    delim = sniff_delimiter(path)
    rows = []
    with path.open("r", encoding="utf-8", errors="replace") as f:
        r = csv.DictReader(f, delimiter=delim)
        rows = list(r)
    if not rows:
        print(json.dumps({"agent":"balance","rows":0}, ensure_ascii=False)); return
    total = 0.0
    by_cat = defaultdict(float)
    outliers = []
    amounts = []
    for i, row in enumerate(rows, start=2):
        try:
            amt = float(str(row.get("amount","0")).replace(",", "."))
        except:
            continue
        total += amt
        by_cat[row.get("category","UNCAT").strip() or "UNCAT"] += amt
        amounts.append(amt)
    if amounts:
        mean = sum(amounts)/len(amounts)
        var = sum((x-mean)**2 for x in amounts)/len(amounts)
        sd = var**0.5
        for i, amt in enumerate(amounts, start=2):
            if sd>0 and abs(amt-mean)>4*sd:
                outliers.append({"row": i, "amount": amt, "mean": mean, "sd": sd})
    top = sorted(by_cat.items(), key=lambda x: -abs(x[1]))[:10]
    advice = []
    if total < 0:
        advice.append("Разходите надвишават приходите – орежи топ 1-2 категории.")
    else:
        advice.append("Приходите превишават разходите – отдели % за резерв.")
    print(json.dumps({"agent":"balance","total": total, "by_category": top, "outliers": outliers[:10], "advice": advice}, ensure_ascii=False, indent=2))

# Agent: JUSTICE (risky clauses)
RISK_TERMS = [
    r"\bнеустойк[аи]\b", r"\бедностранно прекратяване\b", r"\бтърговска тайна\b",
    r"\bбез отговорност\b", r"\bарбитраж\b", r"\bглоба\b", r"\bконфискац",
    r"\bсанкц", r"\bприхван", r"\bцесия\b", r"\bлихва\b"
]
def agent_justice(args):
    p = Path(args.path)
    text = p.read_text(encoding="utf-8", errors="replace")
    hits = []
    for term in RISK_TERMS:
        for m in re.finditer(term, text, flags=re.IGNORECASE):
            start = max(0, m.start()-40)
            end = min(len(text), m.end()+40)
            snippet = text[start:end].replace("\n"," ")
            hits.append({"term": term, "pos": m.start(), "snippet": snippet})
    print(json.dumps({"agent":"justice","file":str(p),"hits":hits[:50],"count":len(hits)}, ensure_ascii=False, indent=2))

def main():
    ap = argparse.ArgumentParser(prog="heart-safe-agents", description="Heart-Safe defensive agents CLI")
    sub = ap.add_subparsers(dest="cmd")

    t = sub.add_parser("truth", help="Анализ на текст/CSV за противоречия и аномалии")
    t.add_argument("path")
    t.set_defaults(func=agent_truth)

    ig = sub.add_parser("integrity", help="Анти-манипулация: SHA256 манифест")
    ig_sub = ig.add_subparsers(dest="command")
    ig_b = ig_sub.add_parser("build", help="Генерирай manifest.json")
    ig_b.add_argument("path")
    ig_b.add_argument("--manifest", default="manifest.json")
    ig_b.set_defaults(func=agent_integrity)
    ig_v = ig_sub.add_parser("verify", help="Провери срещу manifest.json")
    ig_v.add_argument("path")
    ig_v.add_argument("--manifest", default="manifest.json")
    ig_v.set_defaults(func=agent_integrity)

    h = sub.add_parser("honor", help="Git дисциплина/хигиена")
    h.add_argument("repo")
    h.set_defaults(func=agent_honor)

    b = sub.add_parser("balance", help="Бюджет анализ на CSV (date,category,amount)")
    b.add_argument("csv")
    b.set_defaults(func=agent_balance)

    j = sub.add_parser("justice", help="Сканирай текст/договор за рискови клаузи")
    j.add_argument("path")
    j.set_defaults(func=agent_justice)

    ap.add_argument("-v","--version", action="store_true")
    args = ap.parse_args()
    if args.version:
        print(VERSION); return
    if not hasattr(args, "func"):
        ap.print_help(); sys.exit(1)
    args.func(args)

if __name__ == "__main__":
    main()
