
import os, sys, json, hashlib, shutil, zipfile, difflib, re
from datetime import datetime

WATCH_EXT = (".py", ".json", ".md", ".txt", ".cfg", ".ini", ".yaml", ".yml")
extra = os.environ.get("BIONET_EXTRA_EXT", "").strip()
if extra:
    EXTRA = tuple([x if x.startswith(".") else "."+x for x in extra.split(",") if x])
    WATCH_EXT = WATCH_EXT + EXTRA

def ts() -> str:
    return datetime.utcnow().strftime("%Y%m%d-%H%M%S")

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def ensure_root(root: str):
    os.makedirs(os.path.join(root, ".bionet"), exist_ok=True)
    os.makedirs(os.path.join(root, ".bionet", "mailboxes"), exist_ok=True)
    os.makedirs(os.path.join(root, ".bionet", "bone_repo"), exist_ok=True)
    os.makedirs(os.path.join(root, ".bionet", "quarantine"), exist_ok=True)
    os.makedirs(os.path.join(root, ".bionet", "backups"), exist_ok=True)

def reg_path(root: str) -> str:
    return os.path.join(root, ".bionet", "registry.json")

def report_path(root: str) -> str:
    return os.path.join(root, ".bionet", "last_scan.json")

def signals_path(root: str) -> str:
    return os.path.join(root, ".bionet", "signals.jsonl")

def mailbox_path(root: str, relpath: str) -> str:
    safe = relpath.replace(os.sep, "__")
    return os.path.join(root, ".bionet", "mailboxes", safe + ".jsonl")

def quarantine_dir(root: str) -> str:
    return os.path.join(root, ".bionet", "quarantine")

def bone_repo_dir(root: str) -> str:
    return os.path.join(root, ".bionet", "bone_repo")

def backups_dir(root: str) -> str:
    return os.path.join(root, ".bionet", "backups")

def load_registry(root: str):
    p = reg_path(root)
    if os.path.isfile(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"nodes": {}}
    return {"nodes": {}}

def save_registry(root: str, reg):
    with open(reg_path(root), "w", encoding="utf-8") as f:
        json.dump(reg, f, ensure_ascii=False, indent=2)

def classify_node(rel: str):
    lower = rel.lower()
    if lower.endswith(".py"):
        organ = "Neural"
    elif lower.endswith((".json", ".yaml", ".yml", ".ini", ".cfg")):
        organ = "Liver"
    elif lower.endswith((".md", ".txt")):
        organ = "Skin"
    else:
        organ = "Tissue"
    risk = {"Neural": 3, "Liver": 2, "Skin": 1, "Tissue": 1}[organ]
    return {"organ": organ, "risk": risk}

def iter_nodes(root: str):
    for dirpath, dirnames, filenames in os.walk(root):
        if ".bionet" in dirpath:
            continue
        for fn in filenames:
            if fn.startswith("."):
                continue
            if not fn.lower().endswith(WATCH_EXT):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root)
            yield rel, full

def mirror_copy(root: str, full: str, rel: str):
    dest = os.path.join(bone_repo_dir(root), ts(), os.path.dirname(rel))
    os.makedirs(dest, exist_ok=True)
    shutil.copy2(full, os.path.join(dest, os.path.basename(rel)))

def send_signal(root: str, topic: str, message: str):
    ensure_root(root)
    line = json.dumps({"ts": ts(), "topic": topic, "message": message}, ensure_ascii=False)
    with open(signals_path(root), "a", encoding="utf-8") as f:
        f.write(line + "\n")
    reg = load_registry(root)
    for rel in reg.get("nodes", {}).keys():
        with open(mailbox_path(root, rel), "a", encoding="utf-8") as mf:
            mf.write(line + "\n")
        reg["nodes"][rel]["signals"] = reg["nodes"][rel].get("signals", 0) + 1
    save_registry(root, reg)

SUSPICIOUS_TOKENS = ["eval(", "exec(", "base64", "subprocess", "socket", "os.system", "pickle.loads", "marshal.loads"]
SUSPICIOUS_REGEXES = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"AIza[0-9A-Za-z\-_]{35}"),
    re.compile(r"-----BEGIN( RSA)? PRIVATE KEY-----"),
]

def write_report(root: str, payload: dict):
    with open(report_path(root), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

def immune_scan(root: str):
    reg = load_registry(root)
    changed, suspicious, healed = [], [], []
    sus_hits = {}
    for rel, full in iter_nodes(root):
        try:
            data = open(full, "r", encoding="utf-8", errors="ignore").read()
        except Exception:
            data = ""
        new_hash = sha256_file(full)
        node = reg["nodes"].get(rel)
        if node:
            node["last_seen"] = ts()
            weak = []
            if node.get("risk", 1) >= 3:
                weak.append("high_risk_code")
            mb = mailbox_path(root, rel)
            if not os.path.isfile(mb):
                weak.append("no_mailbox")
            node["weak_points"] = weak
            if new_hash != node.get("checksum"):
                changed.append(rel)
            reasons = []
            if any(tok in data for tok in SUSPICIOUS_TOKENS):
                reasons.append("token")
            for rx in SUSPICIOUS_REGEXES:
                if rx.search(data):
                    reasons.append(f"regex:{rx.pattern[:12]}")
            if reasons:
                sus_hits[rel] = reasons
                suspicious.append(rel)
        else:
            kind = classify_node(rel)
            reg["nodes"][rel] = {
                "rel": rel, "organ": kind["organ"], "risk": kind["risk"],
                "checksum": new_hash, "last_seen": ts(), "signals": 0, "weak_points": ["new_node"]
            }
            mirror_copy(root, full, rel)

    for rel in suspicious:
        full = os.path.join(root, rel)
        quarantine_path = quarantine_file(root, full)
        send_signal(root, "immune.alert", f"Подозрителен ({','.join(sus_hits.get(rel, []))}) в {rel}; карантина: {os.path.relpath(quarantine_path, root)}")
        if restore_from_bones(root, rel):
            healed.append(rel)
            reg["nodes"][rel]["checksum"] = sha256_file(os.path.join(root, rel))

    for rel in changed:
        if rel in suspicious:
            continue
        full = os.path.join(root, rel)
        reg["nodes"][rel]["checksum"] = sha256_file(full)
        mirror_copy(root, full, rel)

    save_registry(root, reg)
    payload = {"ts": ts(), "changed": changed, "suspicious": suspicious, "healed": healed, "count": len(reg.get("nodes",{}))}
    write_report(root, payload)
    print(f"🧪 Scan+: changed={len(changed)} suspicious={len(suspicious)} healed={len(healed)}")

def quarantine_file(root: str, src_path: str) -> str:
    qdir = quarantine_dir(root)
    os.makedirs(qdir, exist_ok=True)
    dst = os.path.join(qdir, f"{ts()}_{os.path.basename(src_path)}")
    shutil.copy2(src_path, dst)
    try: os.chmod(dst, 0o444)
    except Exception: pass
    return dst

def restore_from_bones(root: str, rel: str) -> bool:
    bdir = bone_repo_dir(root)
    if not os.path.isdir(bdir):
        return False
    candidates = []
    for snapshot in sorted(os.listdir(bdir)):
        cand = os.path.join(bdir, snapshot, rel)
        if os.path.isfile(cand):
            candidates.append(cand)
    if not candidates:
        return False
    src = candidates[-1]
    dst = os.path.join(root, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    return True

def bionet_graph(root: str):
    reg = load_registry(root)
    total = len(reg.get("nodes", {}))
    stats = {}
    for n in reg["nodes"].values():
        stats[n["organ"]] = stats.get(n["organ"], 0) + 1
    print(f"🗺️ Организъм: {total} възела")
    for k, v in sorted(stats.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  - {k:7} : {v}")
    weak = sorted(reg["nodes"].values(), key=lambda n: (-n.get("risk",0), n["rel"]))[:5]
    print("🦴 Слаби места (top5):")
    for n in weak:
        w = ",".join(n.get("weak_points", [])) or "—"
        print(f"  · {n['rel']}  risk={n['risk']}  weak={w}")

def bones_backup_zip(root: str):
    out = os.path.join(backups_dir(root), f"skeleton_{ts()}.zip")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for dirpath, dirnames, filenames in os.walk(root):
            if ".bionet" in dirpath:
                continue
            for fn in filenames:
                if not fn.lower().endswith(WATCH_EXT):
                    continue
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, root)
                z.write(full, arcname=rel)
    print(f"🦴 Skeleton backup: {out}")
    return out

def cmdline():
    root = os.getcwd()
    ensure_root(root)
    args = sys.argv[1:]
    if not args or args[0] == "help":
        print("""📖 Команди:
  status
  bionet init [dir]
  bionet scan [dir]
  bionet graph [dir]
  backup now [dir]
  signal send <topic> <message>
  node inbox <relpath>
  report last [dir]
""")
        return
    cmd = args[0]
    if cmd == "bionet":
        if len(args) < 2:
            print("Формат: bionet init|scan|graph [dir]")
            return
        sub = args[1]
        tgt = args[2] if len(args) >= 3 else root
        if sub == "scan":
            immune_scan(tgt); return
        if sub == "graph":
            bionet_graph(tgt); return
        if sub == "init":
            reg = {"nodes": {}, "created": ts(), "version": 3.1}
            for dirpath, dirnames, filenames in os.walk(tgt):
                if ".bionet" in dirpath:
                    continue
                for fn in filenames:
                    if fn.startswith(".") or not fn.lower().endswith(WATCH_EXT):
                        continue
                    full = os.path.join(dirpath, fn)
                    rel = os.path.relpath(full, tgt)
                    kind = classify_node(rel)
                    info = {"rel": rel, "organ": kind["organ"], "risk": kind["risk"],
                            "checksum": sha256_file(full), "last_seen": ts(), "signals": 0, "weak_points": []}
                    reg["nodes"][rel] = info
                    dest = os.path.join(bone_repo_dir(tgt), ts(), os.path.dirname(rel))
                    os.makedirs(dest, exist_ok=True)
                    shutil.copy2(full, os.path.join(dest, os.path.basename(rel)))
            save_registry(tgt, reg)
            print(f"✅ BioNet инициализиран върху: {tgt} | възли: {len(reg['nodes'])}")
            return
    if cmd == "report" and len(args) >= 2 and args[1] == "last":
        tgt = args[2] if len(args) >= 3 else root
        rp = report_path(tgt)
        if os.path.isfile(rp):
            with open(rp, "r", encoding="utf-8") as f:
                print(f.read())
        else:
            print("(няма наличен отчет)")
        return
    if cmd == "signal" and len(args) >= 4 and args[1] == "send":
        topic = args[2]; message = " ".join(args[3:])
        send_signal(root, topic, message); print("📡 Signal broadcasted."); return
    if cmd == "node" and len(args) >= 3 and args[1] == "inbox":
        rel = " ".join(args[2:])
        mb = os.path.join(root, ".bionet", "mailboxes", rel.replace(os.sep,"__") + ".jsonl")
        if not os.path.isfile(mb):
            print("Пощенска кутия няма (още).")
        else:
            with open(mb, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.read().splitlines()
            print(f"📬 Inbox {rel}: {len(lines)} сигнал(а)")
            for ln in lines[-10:]: print("  ", ln)
        return
    if cmd == "backup" and len(args) >= 2 and args[1] == "now":
        tgt = args[2] if len(args) >= 3 else root
        bones_backup_zip(tgt); return
    print("❓ Непозната команда. help")

if __name__ == "__main__":
    cmdline()
