#!/usr/bin/env python3
# join_heart_node_v2.py — Heart node helper with auto-discovery.
import os, sys, json, time
from datetime import datetime

BASE = os.getcwd()
BIONET_DIR = os.path.join(BASE, ".bionet")
REG_PATH   = os.path.join(BIONET_DIR, "registry.json")
HEART_PATH = os.path.join(BIONET_DIR, "heart.json")
SIG_PATH   = os.path.join(BIONET_DIR, "signals.jsonl")
SEARCH_CACHE = os.path.join(BIONET_DIR, "search_candidates.json")
DEFAULT_TOKENS = ["sofia_sentinel", "sentinel", "heart", ".py"]

def ts(): return datetime.utcnow().isoformat()+"Z"
def ensure():
    os.makedirs(BIONET_DIR, exist_ok=True)
    if not os.path.isfile(REG_PATH):
        with open(REG_PATH, "w", encoding="utf-8") as f:
            json.dump({"nodes": {}, "created": ts(), "version": 1}, f)

def load_json(p, default):
    try:
        with open(p, "r", encoding="utf-8") as f: return json.load(f)
    except Exception: return default

def save_json(p, data):
    with open(p, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)

def write_signal(topic, message):
    line = json.dumps({"ts": ts(), "topic": topic, "message": message}, ensure_ascii=False)
    with open(SIG_PATH, "a", encoding="utf-8") as f: f.write(line + "\n")

def set_heart(abs_path):
    ensure()
    if not os.path.exists(abs_path): print("❌ Path not found:", abs_path); sys.exit(1)
    rel = os.path.relpath(abs_path, BASE)
    reg = load_json(REG_PATH, {"nodes": {}})
    node = reg["nodes"].get(rel, {"rel": rel, "organ": "Heart", "risk": 4, "checksum": "", "last_seen": ts(), "signals": 0, "weak_points": []})
    node["organ"] = "Heart"; node["risk"] = 4; node["last_seen"] = ts()
    reg["nodes"][rel] = node
    save_json(REG_PATH, reg)
    save_json(HEART_PATH, {"rel": rel, "abs": abs_path, "joined_ts": ts(),"notes": "Designated BioNet Heart node (central timing/signals)."})
    write_signal("heart.join", f"Heart node set to: {rel}")
    print("✅ Heart node joined:", rel)
    print("ℹ️ Registry:", REG_PATH); print("ℹ️ Heart meta:", HEART_PATH); print("ℹ️ Signal appended to:", SIG_PATH)

def score_candidate(path, tokens):
    name = os.path.basename(path).lower(); s = 0
    for t in tokens:
        t = t.strip().lower(); 
        if not t: continue
        if t in name: s += 10
        if name.startswith(t): s += 5
        if name.endswith(t): s += 3
    try:
        age_hours = max(1.0, (time.time() - os.path.getmtime(path))/3600.0); s += 5.0/age_hours
    except Exception: pass
    return s

def find_candidates(tokens, limit=12):
    cands = []
    for dirpath, _, files in os.walk(BASE):
        if "/.bionet" in dirpath or "/.titan" in dirpath: continue
        for fn in files:
            if not fn.lower().endswith((".py",".json",".yaml",".yml",".ini",".cfg",".md",".txt")): continue
            full = os.path.join(dirpath, fn)
            score = score_candidate(full, tokens)
            if score > 0: cands.append((score, full))
    cands.sort(key=lambda x: -x[0]); cands = cands[:limit]
    out = [{"rank": i+1, "path": p, "score": round(s,2)} for i,(s,p) in enumerate(cands)]
    save_json(SEARCH_CACHE, {"base": BASE, "tokens": tokens, "candidates": out, "ts": datetime.utcnow().isoformat()+"Z"})
    return out

def main(argv):
    args = argv[1:]; pick=None; set_dir=None; pattern=None; limit=12; target=None
    i=0
    while i < len(args):
        a=args[i]
        if a=="--pick": pick=int(args[i+1]); i+=2; continue
        if a=="--set-dir": set_dir=args[i+1]; i+=2; continue
        if a=="--pattern": pattern=args[i+1]; i+=2; continue
        if a=="--max": limit=int(args[i+1]); i+=2; continue
        target=a; i+=1
    if set_dir:
        absd=os.path.abspath(set_dir)
        if not os.path.isdir(absd): print("❌ Not a directory:", absd); sys.exit(1)
        return set_heart(absd)
    if pick is not None:
        cache = load_json(SEARCH_CACHE, {}); cand=None
        for c in cache.get("candidates", []):
            if c.get("rank")==pick: cand=c["path"]; break
        if not cand: print("❌ No candidate with that index. Run search again."); sys.exit(1)
        return set_heart(os.path.abspath(cand))
    if target:
        abst=os.path.abspath(target)
        if os.path.exists(abst): return set_heart(abst)
        else: print("ℹ️ Target not found, running discovery…")
    tokens = ["sofia_sentinel","sentinel","heart",".py"]
    if pattern: tokens=[t.strip() for t in pattern.split(",") if t.strip()]
    cands = find_candidates(tokens, limit=limit)
    if not cands:
        print("❌ No candidates found. Try --pattern \"keyword1,keyword2\" or give exact path.")
        sys.exit(1)
    print("🔎 Candidates:")
    for c in cands: print(f"  {c['rank']:>2}. {c['path']}   (score={c['score']})")
    print("\nSelect with:  python3 join_heart_node_v2.py --pick <N>")
    print("or provide an exact path to file/directory.")
if __name__ == "__main__":
    main(sys.argv)
