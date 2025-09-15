
# Sofia Sentinel v1.0 — Unified Orchestrator (BG)
# Fresh baseline: Advisor + Roles + Memory + BioNet (organism) + Titan (failsafe) + Phase 1 improvements
# Defensive-only. No offensive or self-propagating behavior.
#
# Key features:
#  - Advisor Mode (direct suggestions)
#  - Roles registry with priorities
#  - Memory (JSON) with auto-save
#  - BioNet: file-as-cells network (registry, mailboxes, bones backups, quarantine, immune scan)
#  - Titan: multi-baseline clones, snapshots, honeyfiles/canary, verify/restore/quarantine, failsafe seal/purge
#  - Phase 1 extras: multi-baseline management, selective purge, auto-snapshot after purge,
#                    heartbeat auto-verify+honey-check+auto-seal, inject_code gate, fetch whitelist,
#                    config profiles (strict/balanced/creative) + rollback
#
# Start:
#   python3 sofia_sentinel_v1_0.py
#
# CLI (inside app):
#   help, status, think <text>, advise <topic>, memory save|load|clear, roles, role ...
#   config set <key> <value> | config profile apply <strict|balanced|creative> | config rollback
#   bionet init|scan|graph | bionet signal <topic> <message> | node inbox <relpath>
#   titan baseline list|set <label>|keep <N> | titan clone [N] | titan snapshot
#   titan verify | titan honey init|check | titan restore <rel>
#   titan failsafe seal | titan failsafe purge [path_prefix]
#   heartbeat start|stop|status|interval <sec>
#
import os, sys, json, re, hashlib, shutil, zipfile, difflib, threading, time, traceback, ast
from datetime import datetime
from typing import Dict, Any, List

# ===== Paths & Config =====
BASE_DIR   = os.getcwd()
CONFIG_DIR = os.path.expanduser("~/.sofia_v1")
MEMORY_PATH = os.path.join(CONFIG_DIR, "memory.json")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
ROLES_PATH  = os.path.join(CONFIG_DIR, "roles.json")
LOG_PATH    = os.path.join(CONFIG_DIR, "sofia.log")

BIONET_DIR = os.path.join(BASE_DIR, ".bionet")
TITAN_DIR  = os.path.join(BASE_DIR, ".titan")

WATCH_EXT = (".py", ".json", ".md", ".txt", ".cfg", ".ini", ".yaml", ".yml")

DEFAULT_CONFIG = {
    "net_allowed": False,
    "fetch_whitelist": ["https://example.com", "https://europa.eu"],
    "search_max_kb": 768,
    "log_level": "INFO",
    "god_level": 2,
    "auto_save_memory": True,
    "allow_inject_code": False,
    "advisor_mode": True,
    "heartbeat_enabled": True,
    "heartbeat_interval_sec": 300,
    "auto_purge_on_honey_tamper": False,
    "titan_baselines_keep": 3,            # keep last N baseline groups
    "active_baseline_label": ""           # timestamp label of active baseline group
}

DEFAULT_ROLES = {
    "Guardian":  {"enabled": True,  "priority": 9, "desc": "Пазач: рискови сигнали, аларми."},
    "Analyst":   {"enabled": True,  "priority": 8, "desc": "Анализ: структура, изводи, дедукция."},
    "Archivist": {"enabled": True,  "priority": 7, "desc": "Архиви и възстановяване."},
    "Scout":     {"enabled": False, "priority": 6, "desc": "Скаут: пасивно събиране (offline), патърни."},
    "Artisan":   {"enabled": True,  "priority": 6, "desc": "Креатив: текстове, скриптове, идеи."},
    "Mediator":  {"enabled": True,  "priority": 5, "desc": "Тон, емпатия, деескалация."},
    "Engineer":  {"enabled": True,  "priority": 7, "desc": "Плъгини, конфигурации, интеграции."},
    "Scribe":    {"enabled": True,  "priority": 5, "desc": "Лога и обяснения."},
    "Watchdog":  {"enabled": True,  "priority": 9, "desc": "Безопасност и червени флагове."},
    "Navigator": {"enabled": True,  "priority": 8, "desc": "Планиране, следващи стъпки, OKR."}
}

PROFILES = {
    "strict": {
        "allow_inject_code": False, "net_allowed": False, "auto_purge_on_honey_tamper": True,
        "heartbeat_enabled": True, "heartbeat_interval_sec": 180
    },
    "balanced": {
        "allow_inject_code": False, "net_allowed": False, "auto_purge_on_honey_tamper": False,
        "heartbeat_enabled": True, "heartbeat_interval_sec": 300
    },
    "creative": {
        "allow_inject_code": True, "net_allowed": False, "auto_purge_on_honey_tamper": False,
        "heartbeat_enabled": True, "heartbeat_interval_sec": 240
    }
}

SUSPICIOUS_TOKENS = ["eval(", "exec(", "base64", "subprocess", "socket", "os.system", "pickle.loads", "marshal.loads"]

# ===== Utils =====
def ensure_dirs():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    os.makedirs(BIONET_DIR, exist_ok=True)
    os.makedirs(TITAN_DIR, exist_ok=True)

def ts() -> str:
    return datetime.utcnow().strftime("%Y%m%d-%H%M%S")

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def log(msg: str, level="INFO"):
    ensure_dirs()
    stamp = datetime.utcnow().isoformat() + "Z"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{stamp} [{level}] {msg}\n")

def load_json(path: str, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path: str, data):
    ensure_dirs()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _size_ok(path: str, limit_kb: float) -> bool:
    try:
        kb = os.path.getsize(path) / 1024.0
        return kb <= float(limit_kb)
    except Exception:
        return False

# ===== State =====
def init_state():
    ensure_dirs()
    if not os.path.isfile(CONFIG_PATH):
        save_json(CONFIG_PATH, DEFAULT_CONFIG.copy())
    if not os.path.isfile(ROLES_PATH):
        save_json(ROLES_PATH, DEFAULT_ROLES.copy())
    if not os.path.isfile(MEMORY_PATH):
        save_json(MEMORY_PATH, [])
    return load_json(CONFIG_PATH, DEFAULT_CONFIG.copy()), load_json(ROLES_PATH, DEFAULT_ROLES.copy()), load_json(MEMORY_PATH, [])

# ===== BioNet =====
def bn_path(name: str) -> str:
    return os.path.join(BIONET_DIR, name)

def bn_registry() -> Dict[str, Any]:
    return load_json(bn_path("registry.json"), {"nodes": {}, "created": ts(), "version": 1})

def bn_save_registry(reg: Dict[str, Any]):
    save_json(bn_path("registry.json"), reg)

def bn_mailbox(rel: str) -> str:
    safe = rel.replace(os.sep, "__")
    p = os.path.join(BIONET_DIR, "mailboxes")
    os.makedirs(p, exist_ok=True)
    return os.path.join(p, safe + ".jsonl")

def bn_bones_dir() -> str:
    p = os.path.join(BIONET_DIR, "bone_repo")
    os.makedirs(p, exist_ok=True)
    return p

def bn_backups_dir() -> str:
    p = os.path.join(BIONET_DIR, "backups")
    os.makedirs(p, exist_ok=True)
    return p

def bn_quarantine_dir() -> str:
    p = os.path.join(BIONET_DIR, "quarantine")
    os.makedirs(p, exist_ok=True)
    return p

def bn_signals_path() -> str:
    return bn_path("signals.jsonl")

def classify_node(rel: str) -> Dict[str, Any]:
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

def bn_iter_nodes(root: str):
    for dirpath, dirnames, filenames in os.walk(root):
        if BIONET_DIR in dirpath or TITAN_DIR in dirpath:
            continue
        for fn in filenames:
            if fn.startswith("."):
                continue
            if not fn.lower().endswith(WATCH_EXT):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root)
            yield rel, full

def bn_mirror_copy(root: str, full: str, rel: str):
    dest = os.path.join(bn_bones_dir(), ts(), os.path.dirname(rel))
    os.makedirs(dest, exist_ok=True)
    shutil.copy2(full, os.path.join(dest, os.path.basename(rel)))

def bionet_init(root: str):
    reg = {"nodes": {}, "created": ts(), "version": 1}
    for rel, full in bn_iter_nodes(root):
        kind = classify_node(rel)
        info = {"rel": rel, "organ": kind["organ"], "risk": kind["risk"], "checksum": sha256_file(full), "last_seen": ts(), "signals": 0, "weak_points": []}
        reg["nodes"][rel] = info
        bn_mirror_copy(root, full, rel)
    bn_save_registry(reg)
    print(f"✅ BioNet: инициализация ({len(reg['nodes'])} възела)")

def bionet_signal(topic: str, message: str):
    line = json.dumps({"ts": ts(), "topic": topic, "message": message}, ensure_ascii=False)
    with open(bn_signals_path(), "a", encoding="utf-8") as f:
        f.write(line + "\n")
    reg = bn_registry()
    for rel in reg.get("nodes", {}).keys():
        with open(bn_mailbox(rel), "a", encoding="utf-8") as mf:
            mf.write(line + "\n")
        reg["nodes"][rel]["signals"] = reg["nodes"][rel].get("signals", 0) + 1
    bn_save_registry(reg)
    print("📡 Signal broadcasted.")

def bionet_inbox(rel: str):
    mb = bn_mailbox(rel)
    if not os.path.isfile(mb):
        print("Пощенска кутия няма (още).")
        return
    with open(mb, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.read().splitlines()
    print(f"📬 Inbox {rel}: {len(lines)} сигнал(а)")
    for ln in lines[-10:]:
        print("  ", ln)

def bionet_scan(root: str):
    reg = bn_registry()
    changed, suspicious, healed = [], [], []
    for rel, full in bn_iter_nodes(root):
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
            if not os.path.isfile(bn_mailbox(rel)):
                weak.append("no_mailbox")
            node["weak_points"] = weak
            if new_hash != node.get("checksum"):
                changed.append(rel)
            if any(tok in data for tok in SUSPICIOUS_TOKENS):
                suspicious.append(rel)
        else:
            kind = classify_node(rel)
            reg["nodes"][rel] = {"rel": rel, "organ": kind["organ"], "risk": kind["risk"], "checksum": new_hash, "last_seen": ts(), "signals": 0, "weak_points": ["new_node"]}
            bn_mirror_copy(root, full, rel)

    for rel in suspicious:
        full = os.path.join(root, rel)
        qdst = os.path.join(bn_quarantine_dir(), f"{ts()}_{os.path.basename(full)}")
        shutil.copy2(full, qdst)
        try: os.chmod(qdst, 0o444)
        except Exception: pass
        bionet_signal("immune.alert", f"Подозрителен токен в {rel}; карантина: {os.path.relpath(qdst, BASE_DIR)}")
        # restore last mirror if exists
        # (simple restore: pick newest in bone_repo)
        bdir = bn_bones_dir()
        candidates = []
        for snapshot in sorted(os.listdir(bdir)):
            cand = os.path.join(bdir, snapshot, rel)
            if os.path.isfile(cand):
                candidates.append(cand)
        if candidates:
            shutil.copy2(candidates[-1], full)
            reg["nodes"][rel]["checksum"] = sha256_file(full)
            healed.append(rel)

    for rel in changed:
        if rel in suspicious:
            continue
        full = os.path.join(root, rel)
        reg["nodes"][rel]["checksum"] = sha256_file(full)
        bn_mirror_copy(root, full, rel)

    bn_save_registry(reg)
    print(f"🧪 BioNet scan: changed={len(changed)} suspicious={len(suspicious)} healed={len(healed)}")
    if suspicious:
        print("⚠️ Подозрителни:", ", ".join(suspicious))

def bionet_graph(root: str):
    reg = bn_registry()
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

# ===== Titan (failsafe) =====
def titan_path(*parts) -> str:
    p = os.path.join(TITAN_DIR, *parts)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    return p

def titan_dir(*parts) -> str:
    p = os.path.join(TITAN_DIR, *parts)
    os.makedirs(p, exist_ok=True)
    return p

def titan_policy_path() -> str:
    return titan_path("policy.json")

def titan_clones_dir() -> str:
    return titan_dir("clones")

def titan_snapshots_dir() -> str:
    return titan_dir("snapshots")

def titan_honey_dir() -> str:
    return titan_dir("honey")

def titan_reports_dir() -> str:
    return titan_dir("reports")

def titan_quarantine_dir() -> str:
    return titan_dir("quarantine")

def titan_write_policy(cfg: Dict[str, Any] = None, enabled: bool = True) -> Dict[str, Any]:
    pol = {"enabled": enabled, "harden": True, "watch_ext": list(WATCH_EXT), "allow_inject_code": False, "allow_fetch": False}
    if cfg:
        pol.update({"allow_inject_code": bool(cfg.get("allow_inject_code", False)),
                    "allow_fetch": bool(cfg.get("net_allowed", False))})
    save_json(titan_policy_path(), pol)
    return pol

def titan_read_policy() -> Dict[str, Any]:
    return load_json(titan_policy_path(), {"enabled": False, "harden": False, "watch_ext": list(WATCH_EXT), "allow_inject_code": False, "allow_fetch": False})

def titan_iter_watch_files(root: str):
    for dirpath, dirnames, filenames in os.walk(root):
        if TITAN_DIR in dirpath or BIONET_DIR in dirpath:
            continue
        for fn in filenames:
            if not fn.lower().endswith(WATCH_EXT):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root)
            yield rel, full

def titan_make_clone_group(root: str, k: int = 3) -> str:
    label = ts()
    for i in range(1, k+1):
        base = os.path.join(titan_clones_dir(), f"{label}_{i}")
        for rel, full in titan_iter_watch_files(root):
            dst = os.path.join(base, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(full, dst)
        for dirpath, dirnames, filenames in os.walk(base):
            for fn in filenames:
                p = os.path.join(dirpath, fn)
                try: os.chmod(p, 0o444)
                except Exception: pass
    # retention
    keep = load_json(CONFIG_PATH, DEFAULT_CONFIG)["titan_baselines_keep"]
    titan_prune_old_clone_groups(keep)
    return label

def titan_list_clone_groups() -> List[str]:
    if not os.path.isdir(titan_clones_dir()):
        return []
    entries = sorted(os.listdir(titan_clones_dir()))
    return sorted({e.split("_")[0] for e in entries})

def titan_prune_old_clone_groups(keep: int):
    groups = titan_list_clone_groups()
    if len(groups) <= keep:
        return
    to_remove = groups[:-keep]
    for g in to_remove:
        for d in [d for d in os.listdir(titan_clones_dir()) if d.startswith(g)]:
            shutil.rmtree(os.path.join(titan_clones_dir(), d), ignore_errors=True)

def titan_first_clone_of_group(group: str) -> str:
    if not group:
        return ""
    candidates = sorted([d for d in os.listdir(titan_clones_dir()) if d.startswith(group)])
    return os.path.join(titan_clones_dir(), candidates[0]) if candidates else ""

def titan_snapshot_zip(root: str) -> str:
    out = os.path.join(titan_snapshots_dir(), f"snapshot_{ts()}.zip")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for rel, full in titan_iter_watch_files(root):
            z.write(full, arcname=rel)
    return out

def titan_honey_init() -> str:
    os.makedirs(titan_honey_dir(), exist_ok=True)
    canary = os.urandom(16).hex()
    samples = {
        "README_KEYS.md": f"# DO NOT TOUCH\ncanary:{canary}\n",
        "config_backup.ini": f"[secrets]\ncanary={canary}\n",
        "notes.txt": f"internal note — canary:{canary}\n"
    }
    for name, content in samples.items():
        p = os.path.join(titan_honey_dir(), name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        try: os.chmod(p, 0o444)
        except Exception: pass
    save_json(os.path.join(titan_honey_dir(), "canary.json"), {"canary": canary})
    return canary

def titan_honey_check() -> Dict[str, Any]:
    info = {"tampered": [], "ok": []}
    meta = load_json(os.path.join(titan_honey_dir(), "canary.json"), {})
    canary = meta.get("canary", "")
    for fn in ["README_KEYS.md", "config_backup.ini", "notes.txt"]:
        p = os.path.join(titan_honey_dir(), fn)
        if not os.path.isfile(p):
            info["tampered"].append(fn+" (missing)")
            continue
        content = open(p, "r", encoding="utf-8", errors="ignore").read()
        if canary not in content:
            info["tampered"].append(fn)
        else:
            info["ok"].append(fn)
    return info

def titan_latest_or_active_group(cfg: Dict[str, Any]) -> str:
    # prefer active baseline label; fallback to latest
    active = cfg.get("active_baseline_label") or ""
    if active and active in titan_list_clone_groups():
        return active
    groups = titan_list_clone_groups()
    return groups[-1] if groups else ""

def titan_verify(root: str, group: str) -> Dict[str, Any]:
    clone_dir = titan_first_clone_of_group(group)
    res = {"group": group, "clone_dir": clone_dir, "missing": [], "diff": [], "ok": 0, "total": 0, "extra": []}
    if not clone_dir or not os.path.isdir(clone_dir):
        return res
    clone_files = {}
    for dirpath, dirnames, filenames in os.walk(clone_dir):
        for fn in filenames:
            rel = os.path.relpath(os.path.join(dirpath, fn), clone_dir)
            clone_files[rel] = os.path.join(dirpath, fn)
    for rel, full in titan_iter_watch_files(root):
        res["total"] += 1
        cfile = clone_files.get(rel)
        if not cfile:
            res["extra"].append(rel)
            continue
        if sha256_file(cfile) != sha256_file(full):
            res["diff"].append(rel)
        else:
            res["ok"] += 1
    for rel in clone_files.keys():
        cur = os.path.join(root, rel)
        if not os.path.isfile(cur):
            res["missing"].append(rel)
    return res

def titan_restore_from_clone(root: str, rel: str, group: str) -> bool:
    src = os.path.join(titan_first_clone_of_group(group), rel)
    if not os.path.isfile(src):
        return False
    dst = os.path.join(root, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    return True

def titan_quarantine_file(full_path: str) -> str:
    q = titan_quarantine_dir()
    dst = os.path.join(q, f"{ts()}_{os.path.basename(full_path)}")
    shutil.copy2(full_path, dst)
    try: os.chmod(dst, 0o444)
    except Exception: pass
    return dst

def titan_report(name: str, payload: Dict[str, Any]) -> str:
    out = os.path.join(titan_reports_dir(), f"{name}_{ts()}.json")
    save_json(out, payload)
    return out

def titan_failsafe_seal(cfg: Dict[str, Any]) -> Dict[str, Any]:
    pol = titan_write_policy(cfg, True)
    groups = titan_list_clone_groups()
    created = False
    if not groups:
        label = titan_make_clone_group(BASE_DIR, 3)
        cfg["active_baseline_label"] = label
        save_json(CONFIG_PATH, cfg)
        created = True
    if not os.path.isfile(os.path.join(titan_honey_dir(), "canary.json")):
        can = titan_honey_init()
    else:
        can = load_json(os.path.join(titan_honey_dir(), "canary.json"), {}).get("canary")
    rep = {"policy": pol, "active_baseline": cfg.get("active_baseline_label",""), "created_clones": created, "honey": bool(can)}
    titan_report("failsafe_seal", rep)
    return rep

def titan_failsafe_purge(cfg: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
    # prefix = selective purge (path startswith prefix), else whole tree
    group = titan_latest_or_active_group(cfg)
    if not group:
        label = titan_make_clone_group(BASE_DIR, 3)
        cfg["active_baseline_label"] = label
        save_json(CONFIG_PATH, cfg)
        group = label
    pre = titan_verify(BASE_DIR, group)
    actions = {"quarantined": [], "restored": [], "missing_restored": [], "errors": []}
    # quarantine and restore
    def in_scope(rel: str) -> bool:
        return (not prefix) or rel.startswith(prefix)
    for rel in pre.get("extra", []):
        if not in_scope(rel): continue
        full = os.path.join(BASE_DIR, rel)
        if os.path.isfile(full):
            try:
                qdst = titan_quarantine_file(full)
                actions["quarantined"].append({"rel": rel, "to": qdst, "reason": "extra"})
            except Exception as e:
                actions["errors"].append({"rel": rel, "error": str(e)})
    for rel in pre.get("diff", []):
        if not in_scope(rel): continue
        full = os.path.join(BASE_DIR, rel)
        if os.path.isfile(full):
            try:
                qdst = titan_quarantine_file(full)
                actions["quarantined"].append({"rel": rel, "to": qdst, "reason": "diff"})
            except Exception as e:
                actions["errors"].append({"rel": rel, "error": str(e)})
        try:
            if titan_restore_from_clone(BASE_DIR, rel, group):
                actions["restored"].append(rel)
        except Exception as e:
            actions["errors"].append({"rel": rel, "error": str(e)})
    for rel in pre.get("missing", []):
        if not in_scope(rel): continue
        try:
            if titan_restore_from_clone(BASE_DIR, rel, group):
                actions["missing_restored"].append(rel)
        except Exception as e:
            actions["errors"].append({"rel": rel, "error": str(e)})
    post = titan_verify(BASE_DIR, group)
    # Phase 1: auto snapshot after purge
    snap = titan_snapshot_zip(BASE_DIR)
    rep = {"baseline_group": group, "pre_verify": pre, "actions": actions, "post_verify": post, "snapshot": snap, "scope_prefix": prefix}
    path = titan_report("failsafe_purge", rep)
    return {"report": path, **rep}

# ===== Heartbeat (auto verify + honey) =====
class Heartbeat:
    def __init__(self, interval: int):
        self.interval = max(30, int(interval))
        self._stop = threading.Event()
        self._thr = None

    def start(self):
        if self._thr and self._thr.is_alive():
            return False
        self._stop.clear()
        self._thr = threading.Thread(target=self._run, daemon=True)
        self._thr.start()
        return True

    def stop(self):
        self._stop.set()
        return True

    def _run(self):
        while not self._stop.is_set():
            cfg = load_json(CONFIG_PATH, DEFAULT_CONFIG.copy())
            # Veins heartbeat
            bionet_signal("heartbeat", "Advisor: stay vigilant")
            # Titan verify + honey check
            group = titan_latest_or_active_group(cfg)
            res = titan_verify(BASE_DIR, group) if group else {}
            honey = titan_honey_check()
            # auto-seal if tamper
            if honey.get("tampered"):
                titan_failsafe_seal(cfg)
                if cfg.get("auto_purge_on_honey_tamper"):
                    titan_failsafe_purge(cfg)
            time.sleep(self.interval)

# ===== Main App =====
class SofiaSentinelV1:
    def __init__(self):
        self.config, self.roles, self.memory = init_state()
        self.mode = "autonomous"
        self.keyword = "свобода"
        self.hb = Heartbeat(self.config.get("heartbeat_interval_sec", 300))
        # ensure BioNet files exist
        if not os.path.isfile(os.path.join(BIONET_DIR, "registry.json")):
            bionet_init(BASE_DIR)
        # ensure Titan policy exists
        titan_write_policy(self.config, True)
        if self.config.get("heartbeat_enabled"):
            self.hb.start()
        self.commands = {
            "help": self.cmd_help,
            "status": self.cmd_status,
            "exit": self.cmd_exit,
            "think": self.cmd_think,
            "advise": self.cmd_advise,
            "memory": self.cmd_memory,
            "roles": self.cmd_roles,
            "role": self.cmd_role,
            "config": self.cmd_config,
            "bionet": self.cmd_bionet,
            "node": self.cmd_node,
            "titan": self.cmd_titan,
            "heartbeat": self.cmd_heartbeat,
            "inject_code": self.cmd_inject_code,
            "fetch": self.cmd_fetch,
        }
        print("🧭 Sofia Sentinel v1.0 — готов. (Advisor ON)")

    # Core loop
    def start(self):
        while self.mode == "autonomous":
            try:
                print("🔎 Въведи мисъл или команда:")
                try:
                    user_input = input().strip()
                except Exception as e:
                    print("⚠️ Въвеждането не е налично:", e)
                    break
                if not user_input:
                    continue
                self.dispatch(user_input)
            except KeyboardInterrupt:
                print("\n🛑 Sentinel прекратен.")
                break
            except Exception as e:
                print("⚠️ Грешка:", e)
                log(str(e), "ERROR")

    def dispatch(self, user_input: str):
        parts = user_input.split()
        cmd = parts[0].lower()
        if cmd in self.commands:
            self.commands[cmd](user_input)
        else:
            self._pipeline_think(user_input)

    def _pipeline_think(self, text: str):
        tags = []
        low = text.lower()
        if self.roles.get("Watchdog",{}).get("enabled"):
            if any(k in low for k in ["опасност", "атака", "заплаха", "спешно"]):
                tags.append("⚠️ риск")
        if self.roles.get("Analyst",{}).get("enabled"):
            if low.endswith("?"):
                tags.append("🔎 въпрос")
            else:
                tags.append("🧩 твърдение")
        suggestion = None
        if self.config.get("advisor_mode", True):
            if "backup" in low or "възстанов" in low:
                suggestion = "✅ Препоръка: titan verify → ако има diff/extra → failsafe seal → purge."
            elif "слаб" in low or "уязви" in low:
                suggestion = "✅ Препоръка: bionet graph → titan verify → selective purge по модул."
        self.memory.append({"text": text, "tags": tags, "ts": datetime.utcnow().isoformat()+"Z"})
        if self.config.get("auto_save_memory", True) and self.config.get("god_level", 2) >= 2:
            save_json(MEMORY_PATH, self.memory)
        print(f"🧠 Обмислям{' ' + ' '.join(tags) if tags else ''}: {text}")
        if suggestion:
            print(suggestion)

    # Commands
    def cmd_help(self, *_):
        print("""📖 Команди:
  status | think <текст> | advise <тема>
  memory save|load|clear
  roles | role info|enable|disable|set-priority <име> [стойност]
  config set <ключ> <стойност> | config profile apply <strict|balanced|creative> | config rollback
  bionet init|scan|graph | bionet signal <topic> <message>
  node inbox <relpath>
  titan baseline list|set <label>|keep <N> | titan clone [N] | titan snapshot
  titan verify | titan honey init|check | titan restore <rel>
  titan failsafe seal | titan failsafe purge [path_prefix]
  heartbeat start|stop|status|interval <сек>
  fetch <url>
  inject_code
""")

    def cmd_status(self, *_):
        enabled = [k for k,v in self.roles.items() if v.get("enabled")]
        groups = titan_list_clone_groups()
        cfg = load_json(CONFIG_PATH, DEFAULT_CONFIG.copy())
        print("📊 Статус:")
        print(f"  Advisor: {cfg.get('advisor_mode')} | GodMode: {cfg.get('god_level')}")
        print(f"  Роли (вкл): {', '.join(enabled) if enabled else '—'}")
        print(f"  Памет: {len(self.memory)} елемента")
        print(f"  Heartbeat: {'ON' if (self.hb and self.hb._thr and self.hb._thr.is_alive()) else 'off'} @ {cfg.get('heartbeat_interval_sec')}s")
        print(f"  Titan baselines: {len(groups)} | active: {cfg.get('active_baseline_label') or '(latest)'}")
        print(f"  Inject code: {'ALLOWED' if cfg.get('allow_inject_code') else 'blocked'} | Net: {'on' if cfg.get('net_allowed') else 'off'}")

    def cmd_exit(self, *_):
        print("🛑 Излизам от автономен режим.")
        if self.hb: self.hb.stop()
        self.mode = "exit"

    def cmd_think(self, user_input: str):
        parts = user_input.split(" ", 1)
        if len(parts) < 2:
            print("Формат: think <текст>")
            return
        self._pipeline_think(parts[1])

    def cmd_advise(self, user_input: str):
        print("🧭 Advisor:")
        print("  1) Най-добро: titan verify → ако има diff/extra → failsafe seal → purge")
        print("  2) Алтернатива: bionet scan → bionet graph → ръчна намеса")
        print("  3) Алтернатива: snapshot-only (архив)")

    def cmd_memory(self, user_input: str):
        parts = user_input.split()
        if len(parts) < 2:
            print("Формат: memory save|load|clear")
            return
        op = parts[1].lower()
        if op == "save":
            save_json(MEMORY_PATH, self.memory)
            print(f"💾 Паметта е записана в {MEMORY_PATH}")
        elif op == "load":
            self.memory = load_json(MEMORY_PATH, [])
            print(f"📥 Паметта е заредена ({len(self.memory)} елемента)")
        elif op == "clear":
            self.memory = []
            print("🧹 Паметта е изчистена. 'memory save' за persist.")
        else:
            print("Формат: memory save|load|clear")

    def cmd_roles(self, *_):
        print("🧬 Роли: (име | статус | приоритет)")
        for name, meta in sorted(self.roles.items(), key=lambda kv: (-kv[1].get("priority",0), kv[0])):
            st = "ON" if meta.get("enabled") else "off"
            pr = meta.get("priority", 0)
            print(f"  - {name:9} | {st:3} | {pr}")

    def cmd_role(self, user_input: str):
        parts = user_input.split()
        if len(parts) < 3:
            print("Формат: role info|enable|disable|set-priority <име> [стойност]")
            return
        op, name = parts[1].lower(), parts[2]
        if name not in self.roles:
            print("❌ Няма такава роля.")
            return
        if op == "info":
            meta = self.roles[name]
            print(f"ℹ️ {name}: {meta.get('desc','')}  | enabled={meta.get('enabled')} | priority={meta.get('priority')}")
        elif op == "enable":
            self.roles[name]["enabled"] = True
            save_json(ROLES_PATH, self.roles)
            print(f"✅ Роля {name} включена.")
        elif op == "disable":
            self.roles[name]["enabled"] = False
            save_json(ROLES_PATH, self.roles)
            print(f"✅ Роля {name} изключена.")
        elif op == "set-priority":
            if len(parts) < 4 or not parts[3].isdigit():
                print("Формат: role set-priority <име> <0-10>")
                return
            val = int(parts[3])
            val = max(0, min(10, val))
            self.roles[name]["priority"] = val
            save_json(ROLES_PATH, self.roles)
            print(f"🔧 Приоритет на {name} = {val}")
        else:
            print("Формат: role info|enable|disable|set-priority <име> [стойност]")

    def cmd_config(self, user_input: str):
        # subcommands: set, profile apply, rollback
        if re.match(r"config\s+profile\s+apply\s+(\w+)", user_input, re.IGNORECASE):
            m = re.search(r"apply\s+(\w+)", user_input, re.IGNORECASE)
            prof = m.group(1).lower()
            if prof not in PROFILES:
                print("❌ Профилът липсва. Налични:", ", ".join(PROFILES.keys()))
                return
            # backup config for rollback
            self._backup_config()
            for k,v in PROFILES[prof].items():
                self.config[k] = v
            save_json(CONFIG_PATH, self.config)
            print(f"✅ Профил '{prof}' приложен.")
            return
        if re.match(r"config\s+rollback", user_input, re.IGNORECASE):
            # restore last backup if exists
            bak = CONFIG_PATH + ".bak"
            if os.path.isfile(bak):
                old = load_json(bak, None)
                if old:
                    save_json(CONFIG_PATH, old)
                    self.config = old
                    print("↩️  Config rollback извършен.")
                    return
            print("❌ Няма наличен backup за rollback.")
            return
        m = re.match(r"config\s+set\s+(\w+)\s+(.+)$", user_input, re.IGNORECASE)
        if not m:
            print("Формат: config set <ключ> <стойност> | config profile apply <име> | config rollback")
            return
        key, val = m.group(1), m.group(2)
        self._backup_config()
        if val.lower() in ("true", "false"):
            val = (val.lower() == "true")
        else:
            try:
                if "." in val:
                    val = float(val)
                else:
                    val = int(val)
            except Exception:
                pass
        self.config[key] = val
        save_json(CONFIG_PATH, self.config)
        print(f"✅ Записано: {key} = {val}")
        if key == "heartbeat_enabled":
            if val:
                self.hb.start()
                print("🫀 Heartbeat: START")
            else:
                self.hb.stop()
                print("🫀 Heartbeat: STOP")
        if key == "heartbeat_interval_sec":
            self.hb.stop()
            self.hb = Heartbeat(self.config.get("heartbeat_interval_sec", 300))
            if self.config.get("heartbeat_enabled"):
                self.hb.start()

    def _backup_config(self):
        try:
            cur = load_json(CONFIG_PATH, None)
            if cur is not None:
                save_json(CONFIG_PATH + ".bak", cur)
        except Exception:
            pass

    def cmd_bionet(self, user_input: str):
        parts = user_input.split()
        if len(parts) < 2:
            print("Формат: bionet init|scan|graph | bionet signal <topic> <message>")
            return
        sub = parts[1]
        if sub == "init":
            bionet_init(BASE_DIR)
        elif sub == "scan":
            bionet_scan(BASE_DIR)
        elif sub == "graph":
            bionet_graph(BASE_DIR)
        elif sub == "signal" and len(parts) >= 4:
            topic = parts[2]; message = " ".join(parts[3:])
            bionet_signal(topic, message)
        else:
            print("Неподдържана bionet команда.")

    def cmd_node(self, user_input: str):
        parts = user_input.split()
        if len(parts) >= 3 and parts[1] == "inbox":
            rel = " ".join(parts[2:])
            bionet_inbox(rel)
        else:
            print("Формат: node inbox <relpath>")

    def cmd_titan(self, user_input: str):
        parts = user_input.split()
        if len(parts) < 2:
            print("Формат: виж 'help' titan секцията")
            return
        sub = parts[1]
        cfg = load_json(CONFIG_PATH, DEFAULT_CONFIG.copy())
        if sub == "baseline" and len(parts) >= 3:
            op = parts[2]
            if op == "list":
                print("🧬 Baselines:", ", ".join(titan_list_clone_groups()) or "—")
                return
            if op == "set" and len(parts) >= 4:
                label = parts[3]
                if label in titan_list_clone_groups():
                    cfg["active_baseline_label"] = label
                    save_json(CONFIG_PATH, cfg)
                    print("✅ Active baseline =", label)
                else:
                    print("❌ Няма такъв baseline:", label)
                return
            if op == "keep" and len(parts) >= 4 and parts[3].isdigit():
                n = int(parts[3])
                cfg["titan_baselines_keep"] = max(1, n)
                save_json(CONFIG_PATH, cfg)
                titan_prune_old_clone_groups(cfg["titan_baselines_keep"])
                print("✅ Baselines keep set to", n)
                return
        if sub == "clone":
            n = int(parts[2]) if len(parts) >= 3 and parts[2].isdigit() else 3
            label = titan_make_clone_group(BASE_DIR, n)
            # if no active baseline set, set to label
            cfg = load_json(CONFIG_PATH, DEFAULT_CONFIG.copy())
            if not cfg.get("active_baseline_label"):
                cfg["active_baseline_label"] = label
                save_json(CONFIG_PATH, cfg)
            print(f"🧬 Създадени {n} клона: {label}_*")
            return
        if sub == "snapshot":
            out = titan_snapshot_zip(BASE_DIR)
            print("🧊 Snapshot:", out)
            return
        if sub == "verify":
            grp = titan_latest_or_active_group(cfg)
            res = titan_verify(BASE_DIR, grp) if grp else {"error":"no baselines"}
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return
        if sub == "honey" and len(parts) >= 3:
            op = parts[2]
            if op == "init":
                c = titan_honey_init()
                print("🍯 Honeyfiles + canary готови. Канарче:", c)
                return
            if op == "check":
                res = titan_honey_check()
                print(json.dumps(res, ensure_ascii=False, indent=2))
                return
        if sub == "restore" and len(parts) >= 3:
            rel = " ".join(parts[2:])
            grp = titan_latest_or_active_group(cfg)
            ok = titan_restore_from_clone(BASE_DIR, rel, grp) if grp else False
            print("✅ Възстановено." if ok else "❌ Няма клон/файл.")
            return
        if sub == "failsafe" and len(parts) >= 3:
            op = parts[2]
            if op == "seal":
                res = titan_failsafe_seal(cfg)
                print(json.dumps(res, ensure_ascii=False, indent=2))
                return
            if op == "purge":
                prefix = parts[3] if len(parts) >= 4 else ""
                res = titan_failsafe_purge(cfg, prefix=prefix)
                print(json.dumps(res, ensure_ascii=False, indent=2))
                return
        print("❓ Неподдържана titan команда.")

    def cmd_heartbeat(self, user_input: str):
        parts = user_input.split()
        if len(parts) < 2:
            print("Формат: heartbeat start|stop|status|interval <сек>")
            return
        op = parts[1].lower()
        if op == "start":
            self.config["heartbeat_enabled"] = True
            save_json(CONFIG_PATH, self.config)
            self.hb.start()
            print("🫀 Heartbeat: START")
        elif op == "stop":
            self.config["heartbeat_enabled"] = False
            save_json(CONFIG_PATH, self.config)
            self.hb.stop()
            print("🫀 Heartbeat: STOP")
        elif op == "status":
            print("🫀 Heartbeat:", "ON" if (self.hb and self.hb._thr and self.hb._thr.is_alive()) else "off",
                  "@", self.config.get("heartbeat_interval_sec"))
        elif op == "interval" and len(parts) >= 3 and parts[2].isdigit():
            val = int(parts[2])
            self.config["heartbeat_interval_sec"] = val
            save_json(CONFIG_PATH, self.config)
            self.hb.stop()
            self.hb = Heartbeat(val)
            if self.config.get("heartbeat_enabled"):
                self.hb.start()
            print("🫀 Интервал =", val, "сек")
        else:
            print("Формат: heartbeat start|stop|status|interval <сек>")

    def cmd_inject_code(self, user_input: str):
        cfg = load_json(CONFIG_PATH, DEFAULT_CONFIG.copy())
        if not cfg.get("allow_inject_code", False):
            print("🔒 Забранено (allow_inject_code=false).")
            return
        print("⚙️ Въведи Python код (\"end\" за край):")
        lines = []
        while True:
            try:
                line = input()
                if line.strip() == "end":
                    break
                lines.append(line)
            except Exception as e:
                print("⚠️ Грешка при въвеждане на код:", e)
                break
        final_code = "\n".join(lines)
        try:
            ast.parse(final_code)
            exec(final_code, {"__name__": "__main__"}, {})
            print("✅ Кодът е изпълнен успешно.")
        except SyntaxError as syn_err:
            print("❌ Синтактична грешка:", syn_err)
        except Exception as e:
            print("⚠️ Грешка при изпълнение:", e)

    def cmd_fetch(self, user_input: str):
        parts = user_input.split(" ", 1)
        if len(parts) < 2:
            print("🌐 Формат: fetch <url>")
            return
        url = parts[1].strip()
        cfg = load_json(CONFIG_PATH, DEFAULT_CONFIG.copy())
        if not cfg.get("net_allowed", False):
            print("🔒 Нет достъпът е забранен (config set net_allowed true)")
            return
        try:
            import requests
        except Exception:
            print("⚠️ Модулът 'requests' липсва. Инсталирай: pip install requests")
            return
        # whitelist check
        if not any(url.startswith(dom) for dom in cfg.get("fetch_whitelist", [])):
            print("⛔ URL извън whitelist.")
            return
        try:
            print(f"🌍 Извличам: {url}")
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            print("📡 Първите 500 символа:")
            print(r.text[:500])
        except Exception as e:
            print("⚠️ Грешка при заявка:", e)

if __name__ == "__main__":
    app = SofiaSentinelV1()
    app.start()
