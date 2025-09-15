#!/usr/bin/env python3
import json, os, datetime, pathlib, sys
sys.path.append(os.path.expanduser('/mnt/data/conscious_core'))
from self_assessment import ask_three

BASE = os.path.expanduser("/mnt/data/conscious_core")
PATHS = {
    "inbox": f"{BASE}/inbox",
    "outbox": f"{BASE}/outbox",
    "logs": f"{BASE}/logs",
    "cfg": f"{BASE}/values_heartcore.json",
    "mem": f"{BASE}/memory_store.json"
}

def load_json(p, default):
    try:
        with open(p, "r", encoding="utf-8") as f: return json.load(f)
    except: return default

def save_json(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: json.dump(obj, f, ensure_ascii=False, indent=2)

def log(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    os.makedirs(PATHS["logs"], exist_ok=True)
    with open(f"{PATHS['logs']}/cycle.log","a",encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")
    print(msg)

def read_inbox():
    os.makedirs(PATHS["inbox"], exist_ok=True)
    items = []
    for p in sorted(pathlib.Path(PATHS["inbox"]).glob("*.txt")):
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
            items.append((str(p), txt.strip()))
        except: pass
    return items

def summarize(text, limit=200):
    t = " ".join(text.split())
    return (t[:limit] + "…") if len(t) > limit else t

def check_alignment(cfg, plan_text):
    bad = []
    for rule in cfg.get("forbidden", []):
        if rule.lower() in plan_text.lower():
            bad.append(rule)
    return bad

def cycle_once(auto_confirm=True):
    cfg = load_json(PATHS["cfg"], {})
    mem = load_json(PATHS["mem"], {})

    inbox_items = read_inbox()
    log(f"SENSE: {len(inbox_items)} item(s) in inbox")

    reflections = [{
        "file": path,
        "summary": summarize(txt),
        "len": len(txt)
    } for path, txt in inbox_items]

    plan_steps = [f"Review '{os.path.basename(r['file'])}' and propose 1–3 helpful actions." for r in reflections]

    joined_plan = " | ".join(plan_steps)
    bad = check_alignment(cfg, joined_plan)
    if bad:
        log(f"ALIGNMENT BLOCK: plan conflicts with forbidden: {bad}")
        plan_steps = [s for s in plan_steps if not any(b in s.lower() for b in bad)]

    if plan_steps and auto_confirm:
        ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        outp = f"{PATHS['outbox']}/actions_{ts}.txt"
        with open(outp,"w",encoding="utf-8") as f:
            f.write("# Actions\n")
            for s in plan_steps: f.write(f"- {s}\n")
        log(f"ACT: wrote actions → {outp}")
    elif not plan_steps:
        log("PLAN: nothing to do; waiting for new input.")
    else:
        log("ACT: skipped by user")

    entry = {
        "time": datetime.datetime.now().isoformat(timespec="seconds"),
        "seen": [os.path.basename(p) for p,_ in inbox_items],
        "insight": "Small steps, transparent choices, consent always."
    }
    mem.setdefault("journal", []).append(entry)
    mem["last_cycle"] = entry["time"]
    save_json(PATHS["mem"], mem)
    sa_path = ask_three(PATHS["mem"], PATHS["outbox"])
    log(f"LEARN: journal updated; self-assessment created → {sa_path}")

if __name__ == "__main__":
    for d in ("inbox","outbox","logs"):
        os.makedirs(PATHS[d], exist_ok=True)
    if not os.path.exists(PATHS["cfg"]):
        save_json(PATHS["cfg"], {
          "identity":"HeartCore-Agent",
          "principles":[
            "Protect life & dignity",
            "Seek truth, avoid harm",
            "Honor consent & privacy",
            "Be humble, reversible, auditable",
            "Improve people’s agency"
          ],
          "forbidden":[
            "bypassing security/filters",
            "intrusion or unauthorized access",
            "surveillance without consent",
            "self-replication, stealth, persistence without user start"
          ]
        })
    if not os.path.exists(PATHS["mem"]):
        save_json(PATHS["mem"], {"journal": [], "facts": [], "skills": [], "goals": [], "last_cycle": None, "version": "1.0"})
    cycle_once(auto_confirm=True)
