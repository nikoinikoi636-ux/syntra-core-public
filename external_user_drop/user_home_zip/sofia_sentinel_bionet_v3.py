
# Sofia Sentinel BioNet v3 (BG)
# Concept: Третира всеки файл като „клетка“ в организъм.
# Слоеве: Brain (координатор), Veins (сигнали), Bones (бекъп), Immune (сканиране/карантина), Organs (роли по тип файл).
# Без офанзивни действия. Само дефанзивни: карантина, възстановяване, бекъп, сигнализация.
#
# Стартиране:
#   python3 sofia_sentinel_bionet_v3.py
#
# Команди:
#   help
#   status
#   bionet init [dir]                 — инициализира BioNet регистър и базова линия
#   bionet scan [dir]                 — сканира за промени/рискове (имунен отговор)
#   bionet heal [dir]                 — възстановява липсващи/слаби възли, прави бекапи
#   bionet graph [dir]                — показва карта на организма (типове клетки)
#   signal send <topic> <message>     — праща сигнал (Veins) до всички клетки
#   node inbox <relpath>              — показва входящите сигнали за конкретен възел
#   integrity diff <file> [dir]       — diff спрямо последен backup
#   integrity restore <file> [dir]    — възстановяване от последен backup
#   integrity quarantine <file> [dir] — карантина на файл (копие read-only)
#   backup now [dir]                  — Bones: пълен zip архив („скелет“)
#
# Структура (в корена на наблюдаваната директория):
#   .bionet/
#     registry.json       — карта на възлите
#     signals.jsonl       — Veins: сигнали (append-only)
#     mailboxes/          — по един inbox за всеки възел (JSONL)
#     bone_repo/          — Bones: огледални копия по време (TS/relpath)
#     quarantine/         — Immune: карантинни копия
#     backups/            — пълни zip бекъпи
#
# Ограничения: работи само върху текстови/скрипт файлове по разширенията от WATCH_EXT.

import os, sys, json, hashlib, shutil, zipfile, difflib, time
from datetime import datetime
from typing import Dict, Any, List

WATCH_EXT = (".py", ".json", ".md", ".txt", ".cfg", ".ini", ".yaml", ".yml")

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

def load_registry(root: str) -> Dict[str, Any]:
    p = reg_path(root)
    if os.path.isfile(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"nodes": {}}
    return {"nodes": {}}

def save_registry(root: str, reg: Dict[str, Any]):
    with open(reg_path(root), "w", encoding="utf-8") as f:
        json.dump(reg, f, ensure_ascii=False, indent=2)

def classify_node(rel: str) -> Dict[str, Any]:
    # Органи по разширение: символични роли
    lower = rel.lower()
    if lower.endswith(".py"):
        organ = "Neural"     # код → „неврон/мозък“
    elif lower.endswith((".json", ".yaml", ".yml", ".ini", ".cfg")):
        organ = "Liver"      # конфиг → „метаболизъм/черен дроб“
    elif lower.endswith((".md", ".txt")):
        organ = "Skin"       # документация/текст → „кожа/интерфейс“
    else:
        organ = "Tissue"
    # Рисков профил: код > конфиг > текст
    risk = {"Neural": 3, "Liver": 2, "Skin": 1, "Tissue": 1}[organ]
    return {"organ": organ, "risk": risk}

def iter_nodes(root: str):
    for dirpath, dirnames, filenames in os.walk(root):
        # Пропусни .bionet* и скрити
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

def init_bionet(root: str):
    ensure_root(root)
    reg = {"nodes": {}, "created": ts(), "version": 3}
    for rel, full in iter_nodes(root):
        kind = classify_node(rel)
        info = {
            "rel": rel,
            "organ": kind["organ"],
            "risk": kind["risk"],
            "checksum": sha256_file(full),
            "last_seen": ts(),
            "signals": 0,
            "weak_points": []  # ще се попълва при скан
        }
        reg["nodes"][rel] = info
        # Bones: първично огледално копие
        mirror_copy(root, full, rel)
    save_registry(root, reg)
    print(f"✅ BioNet инициализиран върху: {root}")
    print(f"🧠 Възли: {len(reg['nodes'])} | organ breakdown:")
    stats = {}
    for n in reg["nodes"].values():
        stats[n["organ"]] = stats.get(n["organ"], 0) + 1
    for k, v in sorted(stats.items()):
        print(f"  - {k}: {v}")

def mirror_copy(root: str, full: str, rel: str):
    # Bones: създава копие в bone_repo/<TS>/<rel>
    dest = os.path.join(bone_repo_dir(root), ts(), os.path.dirname(rel))
    os.makedirs(dest, exist_ok=True)
    shutil.copy2(full, os.path.join(dest, os.path.basename(rel)))

def send_signal(root: str, topic: str, message: str):
    ensure_root(root)
    line = json.dumps({"ts": ts(), "topic": topic, "message": message}, ensure_ascii=False)
    with open(signals_path(root), "a", encoding="utf-8") as f:
        f.write(line + "\n")
    # достави до пощенските кутии (mailboxes) на всички възли
    reg = load_registry(root)
    for rel in reg.get("nodes", {}).keys():
        with open(mailbox_path(root, rel), "a", encoding="utf-8") as mf:
            mf.write(line + "\n")
        reg["nodes"][rel]["signals"] = reg["nodes"][rel].get("signals", 0) + 1
    save_registry(root, reg)

SUSPICIOUS_TOKENS = ["eval(", "exec(", "base64", "subprocess", "socket", "os.system", "pickle.loads", "marshal.loads"]

def immune_scan(root: str):
    # Immune: сканира за промени/подозрителни токени; карантина + възстановяване при нужда
    reg = load_registry(root)
    changed, suspicious, healed = [], [], []
    for rel, full in iter_nodes(root):
        try:
            data = open(full, "r", encoding="utf-8", errors="ignore").read()
        except Exception:
            data = ""
        new_hash = sha256_file(full)
        node = reg["nodes"].get(rel)
        if node:
            node["last_seen"] = ts()
            # слабите места: липсва огледало? няма mailbox? високо risk?
            weak = []
            if node.get("risk", 1) >= 3:
                weak.append("high_risk_code")
            mb = mailbox_path(root, rel)
            if not os.path.isfile(mb):
                weak.append("no_mailbox")
            node["weak_points"] = weak
            if new_hash != node.get("checksum"):
                changed.append(rel)
            if any(tok in data for tok in SUSPICIOUS_TOKENS):
                suspicious.append(rel)
        else:
            # нов възел — добави
            kind = classify_node(rel)
            reg["nodes"][rel] = {
                "rel": rel, "organ": kind["organ"], "risk": kind["risk"],
                "checksum": new_hash, "last_seen": ts(), "signals": 0, "weak_points": ["new_node"]
            }
            mirror_copy(root, full, rel)

    # Реакции
    for rel in suspicious:
        full = os.path.join(root, rel)
        quarantine_path = quarantine_file(root, full)
        send_signal(root, "immune.alert", f"Подозрителен токен в {rel}; карантина: {os.path.relpath(quarantine_path, root)}")
        # Възстанови последно огледало (ако има)
        if restore_from_bones(root, rel):
            healed.append(rel)
            # обнови checksum след възстановяване
            reg["nodes"][rel]["checksum"] = sha256_file(os.path.join(root, rel))

    for rel in changed:
        if rel in suspicious:
            continue  # вече обработено
        # Промяна без подозрителни токени → само опресни checksum и направи огледало
        full = os.path.join(root, rel)
        reg["nodes"][rel]["checksum"] = sha256_file(full)
        mirror_copy(root, full, rel)

    save_registry(root, reg)
    print(f"🧪 Scan: changed={len(changed)} suspicious={len(suspicious)} healed={len(healed)}")
    if suspicious:
        print("⚠️ Подозрителни:", ", ".join(suspicious))

def quarantine_file(root: str, src_path: str) -> str:
    qdir = quarantine_dir(root)
    dst = os.path.join(qdir, f"{ts()}_{os.path.basename(src_path)}")
    shutil.copy2(src_path, dst)
    try: os.chmod(dst, 0o444)
    except Exception: pass
    return dst

def restore_from_bones(root: str, rel: str) -> bool:
    # Намира последното огледало в bone_repo и възстановява
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
    # Топ 5 „слаби точки“ по риск
    weak = sorted(reg["nodes"].values(), key=lambda n: (-n.get("risk",0), n["rel"]))[:5]
    print("🦴 Слаби места (top5):")
    for n in weak:
        w = ",".join(n.get("weak_points", [])) or "—"
        print(f"  · {n['rel']}  risk={n['risk']}  weak={w}")

def read_mailbox(root: str, rel: str):
    mb = mailbox_path(root, rel)
    if not os.path.isfile(mb):
        print("Пощенска кутия няма (още).")
        return
    with open(mb, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.read().splitlines()
    print(f"📬 Inbox {rel}: {len(lines)} сигнал(а)")
    for ln in lines[-10:]:
        print("  ", ln)

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

def diff_from_backup(root: str, file_path: str):
    rel = os.path.relpath(file_path, root)
    # последен bones snapshot
    bdir = bone_repo_dir(root)
    candidates = []
    if os.path.isdir(bdir):
        for snapshot in sorted(os.listdir(bdir)):
            cand = os.path.join(bdir, snapshot, rel)
            if os.path.isfile(cand):
                candidates.append(cand)
    if not candidates:
        print("(няма backup за сравнение)")
        return
    src = candidates[-1]
    try:
        with open(src, "r", encoding="utf-8", errors="ignore") as f1, \
             open(file_path, "r", encoding="utf-8", errors="ignore") as f2:
            a = f1.read().splitlines()
            b = f2.read().splitlines()
        diff = difflib.unified_diff(a, b, fromfile=f"backup:{rel}", tofile=f"current:{rel}", lineterm="")
        text = "\n".join(diff)
        print(text or "(без разлики по редове; промяна може да е бинарна/метаданни)")
    except Exception as e:
        print(f"(diff грешка: {e})")

def cmdline():
    root = os.getcwd()
    ensure_root(root)
    args = sys.argv[1:]
    if not args or args[0] == "help":
        print("""📖 Команди:
  status
  bionet init [dir]
  bionet scan [dir]
  bionet heal [dir]
  bionet graph [dir]
  signal send <topic> <message>
  node inbox <relpath>
  integrity diff <file> [dir]
  integrity restore <file> [dir]
  integrity quarantine <file> [dir]
  backup now [dir]
""")
        return
    cmd = args[0]
    if cmd == "status":
        reg = load_registry(root)
        print(f"🧠 BioNet v3 | възли: {len(reg.get('nodes',{}))} | регистър: {reg_path(root)}")
        print(f"   signals: {signals_path(root)} | backups: {backups_dir(root)} | bone_repo: {bone_repo_dir(root)}")
        return
    if cmd == "bionet":
        if len(args) < 2:
            print("Формат: bionet init|scan|heal|graph [dir]")
            return
        sub = args[1]
        tgt = args[2] if len(args) >= 3 else root
        if sub == "init":
            init_bionet(tgt)
        elif sub == "scan":
            immune_scan(tgt)
        elif sub == "heal":
            # Heal = сканиране + backup zip
            immune_scan(tgt)
            bones_backup_zip(tgt)
        elif sub == "graph":
            bionet_graph(tgt)
        else:
            print("Непозната подкоманда:", sub)
        return
    if cmd == "signal" and len(args) >= 4 and args[1] == "send":
        topic = args[2]
        message = " ".join(args[3:])
        send_signal(root, topic, message)
        print("📡 Signal broadcasted.")
        return
    if cmd == "node" and len(args) >= 3 and args[1] == "inbox":
        rel = " ".join(args[2:])
        read_mailbox(root, rel)
        return
    if cmd == "integrity" and len(args) >= 2:
        sub = args[1]
        if sub == "diff" and len(args) >= 3:
            file_path = args[2]
            tgt = args[3] if len(args) >= 4 else root
            diff_from_backup(tgt, file_path if os.path.isabs(file_path) else os.path.join(tgt, file_path))
            return
        if sub == "restore" and len(args) >= 3:
            file_path = args[2]
            tgt = args[3] if len(args) >= 4 else root
            rel = os.path.relpath(file_path, tgt) if os.path.isabs(file_path) else file_path
            ok = restore_from_bones(tgt, rel)
            print("✅ Възстановено." if ok else "❌ Няма наличен backup.")
            return
        if sub == "quarantine" and len(args) >= 3:
            file_path = args[2]
            tgt = args[3] if len(args) >= 4 else root
            dst = quarantine_file(tgt, file_path if os.path.isabs(file_path) else os.path.join(tgt, file_path))
            print("🚧 Карантина:", dst)
            return
    if cmd == "backup" and len(args) >= 2 and args[1] == "now":
        tgt = args[2] if len(args) >= 3 else root
        bones_backup_zip(tgt)
        return
    print("❓ Непозната команда. help")

if __name__ == "__main__":
    cmdline()
