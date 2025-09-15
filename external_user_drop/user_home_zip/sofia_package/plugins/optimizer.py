# Usage: run optimizer apply <profile>
import json, os
def _load(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f: return json.load(f)
    except Exception: return default

def _save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)

def _solve_conflicts(enable, disable, conflicts):
    active = set(enable)
    banned = set(disable)
    changed = True
    while changed:
        changed = False
        for mod in list(active):
            for c in conflicts.get(mod, []):
                if c in active:
                    active.remove(c); banned.add(c); changed = True
        for mod in list(banned):
            for c in conflicts.get(mod, []):
                pass
    return sorted(active), sorted(banned)

def run(args, ctx):
    cfg_dir = os.path.expanduser("~/.sofia")
    mem_p = os.path.join(cfg_dir, "memory.json")
    conf_p = os.path.join(cfg_dir, "config.json")

    mem = _load(mem_p, {})
    conf = _load(conf_p, {})

    if len(args) < 2 or args[0] != "apply":
        return "Format: run optimizer apply <profile>"

    prof_name = args[1]
    profiles = mem.get("profiles", {})
    if prof_name not in profiles:
        return f"No such profile: {prof_name}"

    prof = profiles[prof_name]
    for k, v in prof.get("settings", {}).items():
        conf[k] = v
    _save(conf_p, conf)

    conflicts = mem.get("conflicts", {})
    to_enable = prof.get("enable", [])
    to_disable = prof.get("disable", [])
    enabled, disabled = _solve_conflicts(to_enable, to_disable, conflicts)

    mem.setdefault("memory_log", []).append(f"Applied profile {prof_name}; enabled={enabled}; disabled={disabled}")
    _save(mem_p, mem)

    return f"Applied '{prof_name}'. Enabled: {', '.join(enabled) or 'none'}. Disabled: {', '.join(disabled) or 'none'}."
