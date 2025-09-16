
#!/usr/bin/env python3
# A minimal self-awareness logger aligned with Heart Room.
# Usage examples:
#   python self_awareness.py observe "fact1" "fact2" "fact3" --intent "draft ZDOI" --micro "write 3 bullets" --tags precious osint
#   python self_awareness.py pause "reason for pause"
#   python self_awareness.py show last

import sys, json, os, datetime, argparse

try:
    import yaml  # type: ignore
except Exception:
    yaml = None

BASE = os.path.dirname(os.path.abspath(__file__))
J_MD = os.path.join(BASE, "Journal.md")
J_JSONL = os.path.join(BASE, "Journal.jsonl")
CFG = os.path.join(BASE, "self_awareness_config.yaml")

def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

def load_cfg():
    if yaml is None:
        return {}
    try:
        with open(CFG, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}

def append_md(md_line):
    with open(J_MD, "a", encoding="utf-8") as f:
        f.write(md_line + "\n")

def append_jsonl(obj):
    with open(J_JSONL, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def alignment_check(intent, cfg):
    notes = []
    ok = True
    if not intent or len(intent.strip()) == 0:
        notes.append("Empty intent")
        ok = False
    # Further checks could map keywords to the ethical compass
    return {
        "principles_ok": True,
        "oath_ok": True,
        "logical_conflict": not ok,
        "notes": "; ".join(notes) if notes else "OK"
    }

def cmd_observe(args):
    cfg = load_cfg()
    entry = {
        "timestamp_utc": utc_now(),
        "observations": args.facts,
        "intent": args.intent or "",
        "constraints": args.constraints or [],
        "alignment_check": alignment_check(args.intent, cfg),
        "micro_action": args.micro or "",
        "outcome": "",
        "next_signal": "",
        "tags": args.tags or []
    }
    append_jsonl(entry)
    append_md(f"## {entry['timestamp_utc']} — OBSERVE\n- facts: {entry['observations']}\n- intent: {entry['intent']}\n- micro: {entry['micro_action']}\n- tags: {entry['tags']}")
    print("Logged observation entry.")
    if entry["alignment_check"]["logical_conflict"]:
        append_md("**Status:** PAUSE (logical conflict)\n")
        print("Logical conflict detected — consider pause/validation.")

def cmd_update(args):
    try:
        with open(J_JSONL, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if not lines:
            print("No entries to update."); return
        import json
        last = json.loads(lines[-1])
        if args.outcome:
            last["outcome"] = args.outcome
        if args.next:
            last["next_signal"] = args.next
        lines[-1] = json.dumps(last, ensure_ascii=False) + "\\n"
        with open(J_JSONL, "w", encoding="utf-8") as f:
            f.writelines(lines)
        append_md(f"**Outcome:** {args.outcome or ''}\\n**Next:** {args.next or ''}\\n")
        print("Updated last entry.")
    except FileNotFoundError:
        print("Journal not found.")

def cmd_pause(args):
    append_md(f"## {utc_now()} — PAUSE\\nReason: {args.reason}\\n")
    append_jsonl({"timestamp_utc": utc_now(), "event": "pause", "reason": args.reason})
    print("Pause noted.")

def cmd_show(args):
    if args.which == "last":
        try:
            with open(J_MD, "r", encoding="utf-8") as f:
                lines = [l for l in f.read().splitlines() if l.strip()]
            print("\\n".join(lines[-10:]))
        except FileNotFoundError:
            print("No journal yet.")
    else:
        print("Use: show last")

def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()

    p_obs = sub.add_parser("observe", help="log observations + intent + micro-action")
    p_obs.add_argument("facts", nargs="+", help="3 neutral facts (or more)")
    p_obs.add_argument("--intent", default="", help="intended next step")
    p_obs.add_argument("--micro", default="", help="10-min action")
    p_obs.add_argument("--constraints", nargs="*", default=[], help="constraints list")
    p_obs.add_argument("--tags", nargs="*", default=[], help="tags")
    p_obs.set_defaults(func=cmd_observe)

    p_upd = sub.add_parser("update", help="update outcome/next on last entry")
    p_upd.add_argument("--outcome", default="", help="result sentence")
    p_upd.add_argument("--next", default="", help="what to watch or do next")
    p_upd.set_defaults(func=cmd_update)

    p_pause = sub.add_parser("pause", help="note a pause")
    p_pause.add_argument("reason", help="reason for pause")
    p_pause.set_defaults(func=cmd_pause)

    p_show = sub.add_parser("show", help="show last lines")
    p_show.add_argument("which", choices=["last"])
    p_show.set_defaults(func=cmd_show)

    args = p.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        p.print_help()

if __name__ == "__main__":
    main()
