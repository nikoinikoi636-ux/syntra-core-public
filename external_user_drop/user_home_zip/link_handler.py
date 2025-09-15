#!/usr/bin/env python3
import os, json, time
from datetime import datetime
SIG = ".bionet/signals.jsonl"
MEM = ".bionet/memory_link.json"
def ts(): return datetime.utcnow().isoformat()+"Z"
def append(event):
    rec = {"ts": ts(), "event": event}
    with open(MEM, "a", encoding="utf-8") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")
pos = 0
while True:
    if not os.path.isfile(SIG): time.sleep(2); continue
    with open(SIG, "r", encoding="utf-8") as f:
        f.seek(pos)
        line = f.readline()
        while line:
            pos = f.tell()
            try: ev = json.loads(line)
            except Exception: line = f.readline(); continue
            if ev.get("topic") == "sentinel.link":
                append(ev); print("🔗 Link signal captured")
            line = f.readline()
    time.sleep(2)
