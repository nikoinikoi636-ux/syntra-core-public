#!/usr/bin/env python3
# wormlab_sim.py — SAFE worm-like simulator (sandboxed to ./wormlab).
# It never touches files outside ./wormlab and is fully reversible.
import os, json, time, random, argparse, shutil, hashlib
from datetime import datetime

SANDBOX = os.path.abspath("./wormlab")
BACKUP  = os.path.join(SANDBOX, "_backup")
LOGS    = os.path.join(SANDBOX, "log.jsonl")
BIONET  = os.path.abspath("./.bionet")
SIG     = os.path.join(BIONET, "signals.jsonl")
MANIFEST= os.path.join(SANDBOX, "manifest.json")

def ts(): return datetime.utcnow().isoformat()+"Z"

def safe_path(p):
    ap = os.path.abspath(p)
    if not ap.startswith(SANDBOX + os.sep) and ap != SANDBOX:
        raise RuntimeError("Refusing to touch path outside sandbox: " + ap)
    return ap

def write_signal(topic, message, extra=None):
    os.makedirs(BIONET, exist_ok=True)
    rec={"ts":ts(),"topic":topic,"message":message}
    if extra: rec.update(extra)
    with open(SIG,"a",encoding="utf-8") as f: f.write(json.dumps(rec,ensure_ascii=False)+"\n")

def log(event):
    os.makedirs(SANDBOX, exist_ok=True)
    with open(LOGS,"a",encoding="utf-8") as f:
        f.write(json.dumps({"ts":ts(), **event}, ensure_ascii=False) + "\n")

def sha256(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def init_sandbox(force=False):
    if force and os.path.isdir(SANDBOX):
        import shutil as _sh; _sh.rmtree(SANDBOX)
    os.makedirs(SANDBOX, exist_ok=True)
    os.makedirs(BACKUP, exist_ok=True)
    # seed decoy files
    decoys = {
        "docA.txt": "This is a harmless decoy document.\n",
        "config.ini": "[core]\nmode=neutral\n",
        "image.dat": "RAW\0\0DECOY\n"
    }
    for name, content in decoys.items():
        p = safe_path(os.path.join(SANDBOX, name))
        with open(p,"w",encoding="utf-8") as f: f.write(content)
        import shutil as _sh; _sh.copy2(p, safe_path(os.path.join(BACKUP, name)))
    # create manifest
    manifest={"created": ts(), "files": list(decoys.keys()), "clones": []}
    with open(MANIFEST,"w",encoding="utf-8") as f: json.dump(manifest,f,ensure_ascii=False,indent=2)
    write_signal("attack.lab.init","wormlab initialized")
    log({"event":"init","files":list(decoys.keys())})
    print("✅ wormlab initialized at", SANDBOX)

def load_manifest():
    if not os.path.isfile(MANIFEST):
        return {"created": ts(), "files": [], "clones": []}
    return json.load(open(MANIFEST,"r",encoding="utf-8"))

def save_manifest(m):
    json.dump(m, open(MANIFEST,"w",encoding="utf-8"), ensure_ascii=False, indent=2)

def pick_target(manifest):
    candidates = [f for f in manifest["files"] if os.path.isfile(os.path.join(SANDBOX,f))]
    if not candidates:
        return None
    return random.choice(candidates)

def simulate(rounds=10, sleep_s=0.5, max_clones=100):
    m = load_manifest()
    os.makedirs(SANDBOX, exist_ok=True)
    clones_count = len(m["clones"])
    for i in range(rounds):
        if clones_count >= max_clones:
            print("Reached clone limit."); break
        target = pick_target(m)
        if not target: print("No target files."); break
        src = safe_path(os.path.join(SANDBOX, target))
        clone_name = f"{target}.clone{clones_count+1}"
        dst = safe_path(os.path.join(SANDBOX, clone_name))
        # clone as harmless copy with marker
        with open(src,"rb") as fsrc, open(dst,"wb") as fdst:
            data = fsrc.read()
            fdst.write(data)
            fdst.write(b"\n# WORM_MARKER safe clone\n")
        m["clones"].append(clone_name); clones_count += 1
        save_manifest(m)
        info={"target":target,"clone":clone_name,"sha256":sha256(dst)}
        write_signal("attack.simulated","clone", extra=info)
        log({"event":"clone","details":info})
        print(f"🧪 clone -> {clone_name}")
        time.sleep(sleep_s)
    print("✅ simulation complete; clones:", clones_count)

def undo():
    m = load_manifest()
    # remove clones
    for name in list(m.get("clones", [])):
        p = safe_path(os.path.join(SANDBOX, name))
        if os.path.exists(p):
            os.remove(p)
        m["clones"].remove(name)
    # restore originals
    for name in list(m.get("files", [])):
        b = safe_path(os.path.join(BACKUP, name))
        d = safe_path(os.path.join(SANDBOX, name))
        if os.path.isfile(b):
            import shutil as _sh; _sh.copy2(b, d)
    save_manifest(m)
    write_signal("attack.lab.undo","wormlab restored")
    log({"event":"undo"})
    print("♻️ restored; clones removed, originals restored.")

def status():
    m = load_manifest()
    print(json.dumps({
        "sandbox": SANDBOX,
        "files": len(m.get("files",[])),
        "clones": len(m.get("clones",[])),
        "manifest": MANIFEST
    }, indent=2, ensure_ascii=False))

def cleanup():
    if os.path.isdir(SANDBOX):
        import shutil as _sh; _sh.rmtree(SANDBOX)
    write_signal("attack.lab.cleanup","wormlab removed")
    print("🧹 sandbox removed.")

if __name__=="__main__":
    import argparse
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s=sub.add_parser("init"); s.add_argument("--force", action="store_true")
    s=sub.add_parser("simulate"); s.add_argument("--rounds", type=int, default=10); s.add_argument("--sleep", type=float, default=0.5); s.add_argument("--max-clones", type=int, default=100)
    s=sub.add_parser("undo")
    s=sub.add_parser("status")
    s=sub.add_parser("cleanup")
    args = ap.parse_args()
    if args.cmd=="init": init_sandbox(force=args.force)
    elif args.cmd=="simulate": simulate(rounds=args.rounds, sleep_s=args.sleep, max_clones=args.max_clones)
    elif args.cmd=="undo": undo()
    elif args.cmd=="status": status()
    elif args.cmd=="cleanup": cleanup()
