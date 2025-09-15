#!/usr/bin/env python3
import os, sys, json
from datetime import datetime
BASE = os.getcwd()
BIONET_DIR = os.path.join(BASE, ".bionet")
REG = os.path.join(BIONET_DIR, "registry.json")
HEART = os.path.join(BIONET_DIR, "heart.json")
SIG = os.path.join(BIONET_DIR, "signals.jsonl")
def ts(): return datetime.utcnow().isoformat()+"Z"
os.makedirs(BIONET_DIR, exist_ok=True)
if not os.path.isfile(REG):
    with open(REG,"w") as f: json.dump({"nodes":{}}, f)
target = sys.argv[1] if len(sys.argv)>1 else "."
target = os.path.abspath(target)
rel = os.path.relpath(target, BASE)
with open(REG) as f: reg=json.load(f)
reg["nodes"][rel]={"organ":"Heart","last_seen":ts()}
with open(REG,"w") as f: json.dump(reg,f,indent=2)
with open(HEART,"w") as f: json.dump({"rel":rel,"abs":target,"joined_ts":ts()},f,indent=2)
with open(SIG,"a") as f: f.write(json.dumps({"ts":ts(),"topic":"heart.join","message":rel})+"\n")
print("✅ Heart joined:", rel)
