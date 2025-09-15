#!/usr/bin/env python3
# honeypot_guard.py — monitors ./wormlab for changes and raises bionet signals (polling, safe).
import os, json, time
from datetime import datetime

SANDBOX = os.path.abspath("./wormlab")
BIONET  = os.path.abspath("./.bionet")
SIG     = os.path.join(BIONET, "signals.jsonl")
STATE   = os.path.join(SANDBOX, "_guard_state.json")

def ts(): return datetime.utcnow().isoformat()+"Z"

def write_signal(topic, message, extra=None):
    os.makedirs(BIONET, exist_ok=True)
    rec={"ts":ts(),"topic":topic,"message":message}
    if extra: rec.update(extra)
    with open(SIG,"a",encoding="utf-8") as f: f.write(json.dumps(rec,ensure_ascii=False)+"\n")

def snapshot():
    view = {}
    for dirpath, _, files in os.walk(SANDBOX):
        for fn in files:
            full=os.path.join(dirpath,fn)
            try:
                st=os.stat(full)
                view[os.path.relpath(full,SANDBOX)] = {"size": st.st_size, "mtime": st.st_mtime}
            except Exception:
                pass
    return view

def main():
    if not os.path.isdir(SANDBOX):
        print("No sandbox; run wormlab_sim.py init first."); return
    prev = snapshot()
    json.dump({"ts":ts(),"view":prev}, open(STATE,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
    write_signal("honeypot.guard","started", extra={"files": len(prev)})
    print("🛡️ guard started; watching", SANDBOX)
    while True:
        time.sleep(1.0)
        cur = snapshot()
        # additions / modifications
        for rel, meta in cur.items():
            if rel not in prev:
                write_signal("honeypot.alert","file added", extra={"file": rel, **meta})
                print("➕", rel)
            else:
                if meta["mtime"] != prev[rel]["mtime"] or meta["size"] != prev[rel]["size"]:
                    write_signal("honeypot.alert","file modified", extra={"file": rel, **meta})
                    print("✏️ ", rel)
        # deletions
        for rel in set(prev.keys())-set(cur.keys()):
            write_signal("honeypot.alert","file removed", extra={"file": rel})
            print("➖", rel)
        prev = cur
        json.dump({"ts":ts(),"view":prev}, open(STATE,"w",encoding="utf-8"), ensure_ascii=False, indent=2)

if __name__=="__main__":
    main()
