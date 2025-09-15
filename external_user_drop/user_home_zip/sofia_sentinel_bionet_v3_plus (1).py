
import os, sys, json, hashlib, shutil, zipfile, re
from datetime import datetime

WATCH_EXT = (".py", ".json", ".md", ".txt", ".cfg", ".ini", ".yaml", ".yml")
extra = os.environ.get("BIONET_EXTRA_EXT", "").strip()
if extra:
    EXTRA = tuple([x if x.startswith(".") else "."+x for x in extra.split(",") if x])
    WATCH_EXT = WATCH_EXT + EXTRA

SUSPICIOUS_TOKENS = ["eval(", "exec(", "base64", "subprocess", "socket", "os.system", "pickle.loads", "marshal.loads"]
SUSPICIOUS_REGEXES = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"AIza[0-9A-Za-z\-_]{35}"),
    re.compile(r"-----BEGIN( RSA)? PRIVATE KEY-----"),
]

def ts():
    return datetime.utcnow().strftime("%Y%m%d-%H%M%S")

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for ch in iter(lambda: f.read(8192), b""):
            h.update(ch)
    return h.hexdigest()

def ensure(root):
    os.makedirs(os.path.join(root, ".bionet", "mailboxes"), exist_ok=True)
    os.makedirs(os.path.join(root, ".bionet", "bone_repo"), exist_ok=True)
    os.makedirs(os.path.join(root, ".bionet", "quarantine"), exist_ok=True)
    os.makedirs(os.path.join(root, ".bionet", "backups"), exist_ok=True)

def reg_path(root): return os.path.join(root, ".bionet", "registry.json")
def report_path(root): return os.path.join(root, ".bionet", "last_scan.json")
def bones_dir(root): return os.path.join(root, ".bionet", "bone_repo")
def quarantine_dir(root): return os.path.join(root, ".bionet", "quarantine")
def mailbox(root, rel): return os.path.join(root, ".bionet", "mailboxes", rel.replace(os.sep,"__") + ".jsonl")

def load_reg(root):
    p = reg_path(root)
    if os.path.isfile(p):
        try: return json.load(open(p, "r", encoding="utf-8"))
        except: return {"nodes": {}}
    return {"nodes": {}}

def save_reg(root, reg):
    json.dump(reg, open(reg_path(root), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def classify(rel):
    lower = rel.lower()
    if lower.endswith(".py"): organ, risk = "Neural", 3
    elif lower.endswith((".json",".yaml",".yml",".ini",".cfg")): organ, risk = "Liver", 2
    elif lower.endswith((".md",".txt")): organ, risk = "Skin", 1
    else: organ, risk = "Tissue", 1
    return organ, risk

def iter_nodes(root):
    for dp, dn, fn in os.walk(root):
        if ".bionet" in dp: continue
        for f in fn:
            if f.startswith("."): continue
            if not f.lower().endswith(WATCH_EXT): continue
            full = os.path.join(dp, f)
            rel = os.path.relpath(full, root)
            yield rel, full

def mirror_copy(root, full, rel):
    dst = os.path.join(bones_dir(root), ts(), os.path.dirname(rel))
    os.makedirs(dst, exist_ok=True)
    shutil.copy2(full, os.path.join(dst, os.path.basename(rel)))

def send_signal(root, topic, msg):
    p = os.path.join(root, ".bionet", "signals.jsonl")
    line = json.dumps({"ts": ts(), "topic": topic, "message": msg}, ensure_ascii=False)
    with open(p, "a", encoding="utf-8") as f: f.write(line+"\n")
    reg = load_reg(root)
    for rel in reg.get("nodes", {}).keys():
        with open(mailbox(root, rel), "a", encoding="utf-8") as mf:
            mf.write(line+"\n")
        reg["nodes"][rel]["signals"] = reg["nodes"][rel].get("signals", 0) + 1
    save_reg(root, reg)

# ---- HEART NODE ----
def heart_enabled(): return os.environ.get("HEART_NODE","0") in ("1","true","on")
def heart_load_rules():
    path = os.environ.get("HEART_RULES","")
    if not path or not os.path.isfile(path): return {}
    try: return json.load(open(path,"r",encoding="utf-8"))
    except: return {}
def heart_policy(data, rules):
    if not rules: return {"mult":1.0,"allow":False,"hard_quarantine":False,"hits":[]}
    hits=[]; allow=False; hard=False; mult=1.0
    for pat in rules.get("allow_patterns", []):
        if re.search(pat, data): allow=True; hits.append(f"allow:{pat}")
    for pat in rules.get("deny_patterns", []):
        if re.search(pat, data): hits.append(f"deny:{pat}")
    for it in rules.get("risk_multipliers", []):
        pat=it.get("pattern",""); m=float(it.get("mult",1.0))
        if pat and re.search(pat, data): mult*=m; hits.append(f"mult:{pat}x{m}")
    for it in rules.get("hard_quarantine", []):
        pat=it.get("pattern","")
        if pat and re.search(pat, data):
            hard=True
            hits.append(f"hard:{pat}")
    return {"mult":mult,"allow":allow,"hard_quarantine":hard,"hits":hits}
# --------------------

def quarantine(root, src):
    qd = quarantine_dir(root); os.makedirs(qd, exist_ok=True)
    dst = os.path.join(qd, f"{ts()}_{os.path.basename(src)}")
    shutil.copy2(src, dst)
    try: os.chmod(dst, 0o444)
    except: pass
    return dst

def restore_from_bones(root, rel):
    bd = bones_dir(root)
    if not os.path.isdir(bd): return False
    cands=[]
    for snap in sorted(os.listdir(bd)):
        cand = os.path.join(bd, snap, rel)
        if os.path.isfile(cand): cands.append(cand)
    if not cands: return False
    src=cands[-1]; dst=os.path.join(root, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst); return True

def immune_scan(root):
    ensure(root)
    reg = load_reg(root)
    changed=[]; suspicious=[]; healed=[]
    sus_hits={}
    rules = heart_load_rules() if heart_enabled() else {}

    for rel, full in iter_nodes(root):
        try: data=open(full,"r",encoding="utf-8",errors="ignore").read()
        except: data=""
        h = sha256_file(full)
        node = reg["nodes"].get(rel)
        # baseline
        if not node:
            organ, risk = classify(rel)
            reg["nodes"][rel]={"rel":rel,"organ":organ,"risk":risk,"checksum":h,"last_seen":ts(),"signals":0,"weak_points":["new_node"]}
            mirror_copy(root, full, rel)
            node = reg["nodes"][rel]
        else:
            node["last_seen"]=ts()
            if h != node.get("checksum"): changed.append(rel)

        # reasons
        reasons=[]
        if any(tok in data for tok in SUSPICIOUS_TOKENS): reasons.append("token")
        for rx in SUSPICIOUS_REGEXES:
            if rx.search(data): reasons.append(f"regex:{rx.pattern[:12]}")

        # heart overlay
        pol = heart_policy(data, rules) if rules else {"mult":1.0,"allow":False,"hard_quarantine":False,"hits":[]}
        if pol["allow"] and reasons:
            reasons=[r+"|heart:allow" for r in reasons]
        elif pol["hard_quarantine"]:
            reasons.append("heart:hard_quarantine")
        if pol["hits"]: reasons.extend(pol["hits"])

        if reasons:
            suspicious.append(rel)
            sus_hits[rel]=reasons

    # actions
    for rel in suspicious:
        allow = any("heart:allow" in r for r in sus_hits.get(rel, []))
        hardq = any("heart:hard_quarantine" in r for r in sus_hits.get(rel, []))
        full = os.path.join(root, rel)
        if allow and not hardq:
            send_signal(root, "immune.info", f"Heart allow → без карантина: {rel}")
        else:
            q = quarantine(root, full)
            send_signal(root, "immune.alert", f"{rel} → карантина @ {os.path.relpath(q, root)} | {','.join(sus_hits.get(rel,[]))}")
            if restore_from_bones(root, rel):
                healed.append(rel)
                reg["nodes"][rel]["checksum"]=sha256_file(os.path.join(root, rel))

    save_reg(root, reg)
    payload={"ts":ts(),"changed":changed,"suspicious":suspicious,"healed":healed,"count":len(reg.get("nodes",{}))}
    json.dump(payload, open(report_path(root),"w",encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"🧪 Scan+: changed={len(changed)} suspicious={len(suspicious)} healed={len(healed)}")

def init(root):
    ensure(root)
    reg={"nodes":{},"created":ts(),"version":3.2}
    for rel, full in iter_nodes(root):
        organ, risk = classify(rel)
        reg["nodes"][rel]={"rel":rel,"organ":organ,"risk":risk,"checksum":sha256_file(full),"last_seen":ts(),"signals":0,"weak_points":[]}
        mirror_copy(root, full, rel)
    save_reg(root, reg)
    print(f"✅ BioNet инициализиран върху: {root}\n🧠 Възли: {len(reg['nodes'])}")

def graph(root):
    reg=load_reg(root); stats={}
    for n in reg.get("nodes",{}).values():
        stats[n["organ"]]=stats.get(n["organ"],0)+1
    print(f"🗺️ Организъм: {len(reg.get('nodes',{}))} възела")
    for k,v in sorted(stats.items(), key=lambda kv:(-kv[1],kv[0])):
        print(f"  - {k:7}: {v}")

def report_last(root):
    p = report_path(root)
    if os.path.isfile(p):
        print(open(p,"r",encoding="utf-8").read())
    else:
        print("(няма наличен отчет)")

def main():
    args=sys.argv[1:]
    if not args: 
        print("help: bionet init|scan|graph [dir]; report last [dir]"); return
    if args[0]=="bionet" and len(args)>=2:
        sub=args[1]; tgt=args[2] if len(args)>=3 else os.getcwd()
        if sub=="init": init(tgt); return
        if sub=="scan": immune_scan(tgt); return
        if sub=="graph": graph(tgt); return
    if args[0]=="report" and len(args)>=2 and args[1]=="last":
        tgt=args[2] if len(args)>=3 else os.getcwd(); report_last(tgt); return
    print("❓ Непозната команда")
if __name__=="__main__": main()
