#!/usr/bin/env python3
from flask import Flask, request, render_template_string, redirect, url_for, jsonify
import json
from pathlib import Path
from datetime import datetime

app = Flask(__name__)

BIONET_DIR = Path(".bionet")
REG_PATH = BIONET_DIR / "registry.json"
SIG_PATH = BIONET_DIR / "signals.jsonl"

def ts():
    return datetime.utcnow().isoformat() + "Z"

def ensure_dirs():
    BIONET_DIR.mkdir(parents=True, exist_ok=True)
    if not REG_PATH.exists():
        REG_PATH.write_text(json.dumps({"nodes": {}, "created": ts(), "version": 2}, ensure_ascii=False, indent=2), encoding="utf-8")

def load_registry():
    ensure_dirs()
    try:
        return json.loads(REG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"nodes": {}, "created": None, "version": None}

def save_registry(reg):
    ensure_dirs()
    REG_PATH.write_text(json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8")

def load_signals(limit=200):
    if not SIG_PATH.exists():
        return []
    items = []
    with SIG_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except Exception:
                continue
    items.sort(key=lambda x: x.get("ts",""), reverse=True)
    return items[:limit]

def append_signal(topic, message, meta=None):
    ensure_dirs()
    entry = {"ts": ts(), "topic": topic, "message": message}
    if meta:
        entry["meta"] = meta
    with SIG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry

@app.route("/health")
def health():
    return jsonify({"status":"ok","ts":ts()})

@app.route("/api/registry", methods=["GET"])
def api_registry():
    return jsonify(load_registry())

@app.route("/api/signals", methods=["GET"])
def api_signals():
    return jsonify({"signals": load_signals()})

@app.route("/api/join", methods=["POST"])
def api_join():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    tags = data.get("tags") or []
    if not name:
        return jsonify({"error":"name required"}), 400
    reg = load_registry()
    reg["nodes"][name] = {"tags": tags, "joined": ts()}
    save_registry(reg)
    append_signal("join", f"Node '{name}' joined", {"tags": tags})
    return jsonify({"ok": True, "nodes": len(reg['nodes'])})

@app.route("/api/send", methods=["POST"])
def api_send():
    """
    Programmatic send with a specific sender (node).
    Body: {"sender":"NodeName", "message":"..."}; sender can be "Administrator" or any registry node.
    """
    data = request.get_json(silent=True) or {}
    sender = (data.get("sender") or "Administrator").strip()
    msg = (data.get("message") or "").strip()
    if not msg:
        return jsonify({"error":"message required"}), 400
    reg = load_registry()
    # if sender not in nodes and not Administrator, auto-register with no tags
    if sender != "Administrator" and sender not in reg.get("nodes", {}):
        reg["nodes"][sender] = {"tags": ["auto"], "joined": ts()}
        save_registry(reg)
        append_signal("join", f"Node '{sender}' auto-joined", {"tags": ["auto"], "via":"api_send"})
    append_signal("chat", msg, {"source":"api", "sender": sender})
    # simple echo reply from core
    reply = f"Core→{sender}: acknowledged '{msg}' @ {ts()}"
    append_signal("core-reply", reply, {"auto": True, "to": sender})
    return jsonify({"ok": True, "sender": sender, "reply": reply})

@app.route("/api/ai-reply", methods=["POST","GET"])
def ai_reply():
    # Optional prompt from body; otherwise reply to latest chat signal
    target_sender = None
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        msg = (data.get("message") or "").strip()
        target_sender = (data.get("sender") or "").strip() or None
        if msg:
            append_signal("chat", msg, {"source": "web", "sender": target_sender or "Administrator"})
    sigs = load_signals(limit=1)
    if not sigs:
        reply = "Central Core online. No prior signals."
        meta = {"auto": True}
    else:
        last = sigs[0]
        last_msg = last.get("message","")
        topic = last.get("topic","chat")
        sender = (last.get("meta", {}) or {}).get("sender", "Administrator")
        reply = f"Core→{sender}: ack {topic}: '{last_msg}' @ {ts()}"
        meta = {"auto": True, "to": sender}
    append_signal("core-reply", reply, meta)
    return jsonify({"reply": reply})

@app.route("/", methods=["GET","POST"])
def index():
    reg = load_registry()
    node_names = ["Administrator"] + sorted(list(reg.get("nodes", {}).keys()))
    if request.method == "POST":
        msg = (request.form.get("message") or "").strip()
        sender = (request.form.get("sender") or "Administrator").strip()
        if msg:
            # auto-add node if not present and not Administrator
            if sender != "Administrator" and sender not in reg.get("nodes", {}):
                reg["nodes"][sender] = {"tags": ["auto"], "joined": ts()}
                save_registry(reg)
                append_signal("join", f"Node '{sender}' auto-joined", {"tags": ["auto"], "via":"web-form"})
            append_signal("chat", msg, {"source":"web-form", "sender": sender})
            # trigger auto-reply immediately
            reply = f"Core→{sender}: received '{msg}' @ {ts()}"
            append_signal("core-reply", reply, {"auto": True, "to": sender})
        return redirect(url_for("index"))

    nodes = reg.get("nodes", {})
    signals = load_signals(limit=200)

    html = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Central Core Chat v2.1 — Node-aware</title>
    <meta http-equiv="refresh" content="5">
    <style>
      body{font-family:ui-monospace,Consolas,monospace;background:#0b0b0b;color:#d6ffd6;margin:24px;}
      h2,h3{margin:0 0 8px 0}
      .row{display:flex;gap:12px;flex-wrap:wrap}
      .card{flex:1;min-width:360px;background:#111;border:1px solid #1e1e1e;border-radius:10px;padding:12px;margin:10px 0;}
      input[type=text],select{width:80%;padding:8px;border-radius:6px;border:1px solid #333;background:#0d0d0d;color:#d6ffd6}
      input[type=submit],button{padding:8px 14px;border-radius:6px;background:#22c55e;border:0;color:#041b0a;cursor:pointer}
      pre{white-space:pre-wrap}
      .muted{color:#8fbf8f}
      .mono{font-family:inherit}
    </style>
  </head>
  <body>
    <h2>🛰️ Central Core — Live Link (v2.1)</h2>
    <div class="row">
      <div class="card">
        <strong>Registry:</strong> {{ nodes|length }} nodes
        <pre>{{ nodes|tojson(indent=2) }}</pre>
        <form id="joinForm" onsubmit="joinNode();return false;">
          <input class="mono" type="text" id="nname" placeholder="Node name (e.g., Sintra@Phone)">
          <input class="mono" type="text" id="ntags" placeholder="tags comma-separated (termux,guardian)">
          <button type="submit">Join Now</button>
        </form>
        <div class="muted">POST /api/join will update .bionet/registry.json</div>
      </div>
      <div class="card">
        <strong>Signals (latest):</strong>
        <pre>{% for s in signals %}[{{ s['ts'] }}] {{ (s.get('meta',{}) or {}).get('sender','Core') }} • {{ s.get('topic','?') }}: {{ s.get('message','') }}
{% endfor %}</pre>
        <form method="post">
          <select name="sender">
            {% for n in node_names %}
              <option value="{{n}}">{{n}}</option>
            {% endfor %}
          </select>
          <input class="mono" type="text" name="message" placeholder="Send message to Central Core…" autofocus>
          <input type="submit" value="Send">
          <button type="button" onclick="autoReply()">Auto-Reply</button>
        </form>
        <div class="muted">Select a sender (node) to speak as; auto-reply targets that sender.</div>
      </div>
    </div>
    <script>
      async function joinNode(){
        const name = document.getElementById('nname').value.trim();
        const tags = document.getElementById('ntags').value.split(',').map(s=>s.trim()).filter(Boolean);
        if(!name){ alert('Name required'); return; }
        const res = await fetch('/api/join', {
          method:'POST',
          headers:{'Content-Type':'application/json'},
          body: JSON.stringify({name, tags})
        });
        const j = await res.json();
        if(j.ok){ location.reload(); } else { alert(JSON.stringify(j)); }
      }
      async function autoReply(){
        await fetch('/api/ai-reply', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({})});
        location.reload();
      }
    </script>
  </body>
</html>
    """
    return render_template_string(html, nodes=nodes, signals=signals, node_names=node_names)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8787, debug=False)
