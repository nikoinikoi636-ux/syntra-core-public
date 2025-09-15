#!/usr/bin/env python3
# file_bridge.py - Direct file-only messaging (no HTTP required)
import json, sys, time
from pathlib import Path

LOG = Path("portal_log.jsonl")
LAST_CHAT = Path("last_chatgpt.json")
LAST_SINTRA = Path("last_sintra.json")

def send(origin: str, message: str):
    entry = {"ts": time.time(), "origin": origin, "message": message}
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    if origin.lower().startswith("chat"):
        LAST_CHAT.write_text(json.dumps(entry, indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        LAST_SINTRA.write_text(json.dumps(entry, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Wrote:", entry)

def main():
    if len(sys.argv) < 3 or sys.argv[1] not in {"to_sintra", "to_chatgpt"}:
        print("Usage: file_bridge.py {to_sintra|to_chatgpt} "message"")
        raise SystemExit(2)
    origin = "ChatGPT" if sys.argv[1] == "to_sintra" else "Sintra"
    send(origin, sys.argv[2])

if __name__ == "__main__":
    main()
