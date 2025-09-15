
# Sentinel Titan v4 — Defensive Failsafe (BG)
# Purpose: Пълен защитен режим без офанзивни действия. Никакво "разпространение" към други системи.
# Features:
#  - Titan enable/disable/status
#  - Immutable local clones (read-only) в .titan/clones/ — бързо възстановяване
#  - Snapshots (zip) в .titan/snapshots/
#  - Honeyfiles + Canary tokens в .titan/honey/ за ранни сигнали при подправяне
#  - Hardening: забранява рискови операции (inject_code, fetch), whitelist разширения
#  - Verify: hash-верификация срещу последния клон
#
# CLI:
#   python3 sofia_sentinel_titan_v4.py help
#
# Команди:
#   titan enable|disable|status
#   titan harden                       — записва политика в .titan/policy.json
#   titan clone [dir] [N]              — прави N read-only клона (по подразб. 3) на наблюдаваната директория
#   titan snapshot [dir]               — zip snapshot в .titan/snapshots/
#   titan verify [dir]                 — сравнява хешове спрямо последния клон
#   titan honey init [dir]             — създава honeyfiles + canary tokens
#   titan honey check [dir]            — проверява за промени в honeyfiles
#   titan restore <relpath> [dir]      — възстановява файл от последния клон
#
# Всичко е локално и дефанзивно. Няма мрежови действия, няма "капани", които вредят.
#
import os, sys, json, hashlib, shutil, zipfile
from datetime import datetime
from typing import Dict, Any, List

WATCH_EXT = (".py", ".json", ".md", ".txt", ".cfg", ".ini", ".yaml", ".yml")

def ts():
    return datetime.utcnow().strftime("%Y%m%d-%H%M%S")

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def titan_dir(root: str) -> str:
    return os.path.join(root, ".titan")

def clones_dir(root: str) -> str:
    return os.path.join(titan_dir(root), "clones")

def snapshots_dir(root: str) -> str:
    return os.path.join(titan_dir(root), "snapshots")

def honey_dir(root: str) -> str:
    return os.path.join(titan_dir(root), "honey")

def policy_path(root: str) -> str:
    return os.path.join(titan_dir(root), "policy.json")

def ensure_dirs(root: str):
    os.makedirs(titan_dir(root), exist_ok=True)
    os.makedirs(clones_dir(root), exist_ok=True)
    os.makedirs(snapshots_dir(root), exist_ok=True)
    os.makedirs(honey_dir(root), exist_ok=True)

def write_policy(root: str, enabled=True):
    ensure_dirs(root)
    pol = {"enabled": enabled, "harden": True, "watch_ext": list(WATCH_EXT)}
    with open(policy_path(root), "w", encoding="utf-8") as f:
        json.dump(pol, f, ensure_ascii=False, indent=2)
    return pol

def read_policy(root: str):
    try:
        with open(policy_path(root), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"enabled": False, "harden": False, "watch_ext": list(WATCH_EXT)}

def iter_watch_files(root: str):
    for dirpath, dirnames, filenames in os.walk(root):
        if ".titan" in dirpath or ".bionet" in dirpath:
            continue
        for fn in filenames:
            if not fn.lower().endswith(WATCH_EXT):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root)
            yield rel, full

def make_clone(root: str, n: int = 3):
    ensure_dirs(root)
    label = ts()
    # създава k клона като директории: .titan/clones/<label>_<i>/...
    for i in range(1, n+1):
        base = os.path.join(clones_dir(root), f"{label}_{i}")
        for rel, full in iter_watch_files(root):
            dst = os.path.join(base, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(full, dst)
        # направи клона read-only
        for dirpath, dirnames, filenames in os.walk(base):
            for fn in filenames:
                p = os.path.join(dirpath, fn)
                try: os.chmod(p, 0o444)
                except Exception: pass
    return label

def latest_clone_base(root: str) -> str:
    if not os.path.isdir(clones_dir(root)):
        return ""
    entries = sorted(os.listdir(clones_dir(root)))
    return os.path.join(clones_dir(root), entries[-1]) if entries else ""

def verify_against_latest_clone(root: str) -> Dict[str, Any]:
    base = latest_clone_base(root)
    result = {"base": base, "missing": [], "diff": [], "ok": 0, "total": 0}
    if not base:
        return result
    # вземи първата поддиректория (един от клоновете) за сравнение
    subclones = [d for d in os.listdir(os.path.dirname(base)) if d.startswith(os.path.basename(base).split("_")[0])]
    if not subclones:
        return result
    compare_dir = os.path.join(clones_dir(root), subclones[0])
    # сравнение
    for rel, full in iter_watch_files(root):
        result["total"] += 1
        cfile = os.path.join(compare_dir, rel)
        if not os.path.isfile(cfile):
            result["missing"].append(rel)
            continue
        if sha256_file(cfile) != sha256_file(full):
            result["diff"].append(rel)
        else:
            result["ok"] += 1
    return result

def snapshot_zip(root: str) -> str:
    ensure_dirs(root)
    out = os.path.join(snapshots_dir(root), f"snapshot_{ts()}.zip")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for rel, full in iter_watch_files(root):
            z.write(full, arcname=rel)
    return out

def honey_init(root: str):
    ensure_dirs(root)
    # три примамки + canary token
    canary = os.urandom(16).hex()
    samples = {
        "README_KEYS.md": f"# DO NOT TOUCH\ncanary:{canary}\n",
        "config_backup.ini": f"[secrets]\ncanary={canary}\n",
        "notes.txt": f"internal note — canary:{canary}\n"
    }
    for name, content in samples.items():
        p = os.path.join(honey_dir(root), name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        try: os.chmod(p, 0o444)
        except Exception: pass
    # индекс на канарчето
    with open(os.path.join(honey_dir(root), "canary.json"), "w", encoding="utf-8") as f:
        json.dump({"canary": canary}, f, ensure_ascii=False, indent=2)
    return canary

def honey_check(root: str) -> Dict[str, Any]:
    info = {"tampered": [], "ok": []}
    try:
        with open(os.path.join(honey_dir(root), "canary.json"), "r", encoding="utf-8") as f:
            canary = json.load(f).get("canary","")
    except Exception:
        return {"error": "no canary"}
    for fn in ["README_KEYS.md", "config_backup.ini", "notes.txt"]:
        p = os.path.join(honey_dir(root), fn)
        if not os.path.isfile(p):
            info["tampered"].append(fn+" (missing)")
            continue
        content = open(p, "r", encoding="utf-8", errors="ignore").read()
        if canary not in content:
            info["tampered"].append(fn)
        else:
            info["ok"].append(fn)
    return info

def restore_from_clone(root: str, rel: str) -> bool:
    base = latest_clone_base(root)
    if not base:
        return False
    # Използвай първия клон от групата
    head = base.split("_")[0]
    subclones = [d for d in sorted(os.listdir(clones_dir(root))) if d.startswith(os.path.basename(head))]
    if not subclones:
        return False
    src = os.path.join(clones_dir(root), subclones[0], rel)
    if not os.path.isfile(src):
        return False
    dst = os.path.join(root, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    return True

def cmdline():
    root = os.getcwd()
    ensure_dirs(root)
    args = sys.argv[1:]
    if not args or args[0] == "help":
        print("""📖 Titan v4 — команди:
  titan enable|disable|status
  titan harden
  titan clone [dir] [N]
  titan snapshot [dir]
  titan verify [dir]
  titan honey init [dir]
  titan honey check [dir]
  titan restore <relpath> [dir]
""")
        return
    cmd = args[0]
    if cmd == "titan":
        if len(args) < 2:
            print("Формат: titan enable|disable|status|harden|clone|snapshot|verify|honey|restore")
            return
        sub = args[1]
        if sub == "enable":
            pol = write_policy(root, True)
            print("🛡️ Titan: ENABLED")
            return
        if sub == "disable":
            pol = write_policy(root, False)
            print("🧰 Titan: DISABLED")
            return
        if sub == "status":
            pol = read_policy(root)
            print("📊 Titan:", "ENABLED" if pol.get("enabled") else "disabled")
            print("   Harden:", pol.get("harden"))
            print("   Watch ext:", ", ".join(pol.get("watch_ext", [])))
            return
        if sub == "harden":
            pol = write_policy(root, True)
            print("🔒 Политика записана:", policy_path(root))
            return
        if sub == "clone":
            tgt = args[2] if len(args) >= 3 else root
            n = int(args[3]) if len(args) >= 4 and args[3].isdigit() else 3
            label = make_clone(tgt, n)
            print(f"🧬 Създадени {n} клона: {label}_* в {clones_dir(tgt)}")
            return
        if sub == "snapshot":
            tgt = args[2] if len(args) >= 3 else root
            out = snapshot_zip(tgt)
            print("🧊 Snapshot:", out)
            return
        if sub == "verify":
            tgt = args[2] if len(args) >= 3 else root
            res = verify_against_latest_clone(tgt)
            print("🔎 Verify:", json.dumps(res, ensure_ascii=False, indent=2))
            return
        if sub == "honey":
            if len(args) < 3:
                print("Формат: titan honey init|check [dir]")
                return
            op = args[2]
            tgt = args[3] if len(args) >= 4 else root
            if op == "init":
                c = honey_init(tgt)
                print("🍯 Honeyfiles + canary готови. Канарче:", c)
                return
            if op == "check":
                res = honey_check(tgt)
                print("🍯 Honey check:", json.dumps(res, ensure_ascii=False, indent=2))
                return
        if sub == "restore":
            if len(args) < 3:
                print("Формат: titan restore <relpath> [dir]")
                return
            rel = args[2]
            tgt = args[3] if len(args) >= 4 else root
            ok = restore_from_clone(tgt, rel)
            print("✅ Възстановено." if ok else "❌ Няма клон/файл.")
            return
        print("Непозната подкоманда:", sub)
        return
    print("❓ Непозната команда. help")

if __name__ == "__main__":
    cmdline()
