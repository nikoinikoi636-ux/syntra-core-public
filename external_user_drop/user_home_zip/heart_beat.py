#!/usr/bin/env python3
import os, json, time
from datetime import datetime
SIG = ".bionet/signals.jsonl"
def ts(): return datetime.utcnow().isoformat()+"Z"
INTERVAL = 60
while True:
    os.makedirs(".bionet", exist_ok=True)
    with open(SIG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": ts(), "topic": "heart.beat", "message": "tick"}) + "\n")
    print("💓 beat")
    time.sleep(INTERVAL)
