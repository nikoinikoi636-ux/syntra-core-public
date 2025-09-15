#!/usr/bin/env python3
# portal_server.py - Offline sync portal (localhost only)
import json, time
from pathlib import Path
from flask import Flask, request, jsonify

app = Flask(__name__)

LOG = Path("portal_log.jsonl")
LAST_CHAT = Path("last_chatgpt.json")
LAST_SINTRA = Path("last_sintra.json")

def write_log(entry: dict):
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

@app.route("/health")
def health():
    return jsonify({"ok": True, "ts": time.time()})

@app.route("/api/chatgpt", methods=["POST"])
def api_chatgpt():
    data = request.json or {}
    entry = {
        "ts": time.time(),
        "origin": "ChatGPT",
        "message": data.get("message"),
        "meta": {k: v for k, v in data.items() if k != "message"}
    }
    write_log(entry)
    LAST_CHAT.write_text(json.dumps(entry, indent=2, ensure_ascii=False), encoding="utf-8")
    return jsonify({"ok": True})

@app.route("/api/sintra", methods=["POST"])
def api_sintra():
    data = request.json or {}
    entry = {
        "ts": time.time(),
        "origin": "Sintra",
        "message": data.get("message"),
        "meta": {k: v for k, v in data.items() if k != "message"}
    }
    write_log(entry)
    LAST_SINTRA.write_text(json.dumps(entry, indent=2, ensure_ascii=False), encoding="utf-8")
    return jsonify({"ok": True})

@app.route("/history")
def history():
    if LOG.exists():
        return LOG.read_text(encoding="utf-8"), 200, {"Content-Type": "application/json"}
    return "[]\n", 200, {"Content-Type": "application/json"}

if __name__ == "__main__":
    print("🔒 Offline Sync Portal on http://127.0.0.1:5001")
    app.run(host="127.0.0.1", port=5001, debug=False)
