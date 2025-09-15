#!/usr/bin/env python3
import os, json
from flask import Flask, jsonify, send_file, render_template_string

app = Flask(__name__)

TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Sintra AI Dashboard (Lite)</title>
  <style>
    body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial;margin:20px;line-height:1.4}
    .card{border:1px solid #e5e5e5;border-radius:12px;padding:16px;margin-bottom:16px;box-shadow:0 1px 2px rgba(0,0,0,.04)}
    h1{margin:0 0 12px}
    code,pre{background:#f7f7f7;padding:8px;border-radius:8px;display:block;overflow:auto}
    a.button{display:inline-block;padding:8px 12px;border:1px solid #333;border-radius:8px;text-decoration:none}
  </style>
</head>
<body>
  <h1>📊 Sintra AI Dashboard (Lite)</h1>

  <div class="card">
    <h3>Status</h3>
    <ul>
      <li>sintra_brain.json: {{ '✅' if brain_exists else '❌' }}</li>
      <li>sintra_diff_report.json: {{ '✅' if diff_exists else '❌' }}</li>
      <li>logic_map.gv (PDF/PNG): {{ '✅' if gv_exists else '❌' }}</li>
    </ul>
    <a class="button" href="/api/scan">🔄 Rescan now</a>
  </div>

  <div class="card">
    <h3>Brain snapshot</h3>
    {% if brain %}
      <pre>{{ brain|tojson(indent=2) }}</pre>
    {% else %}
      <p>No brain yet. Click “Rescan now”.</p>
    {% endif %}
  </div>

  <div class="card">
    <h3>Downloads</h3>
    <ul>
      <li><a href="/download/brain">sintra_brain.json</a></li>
      <li><a href="/download/diff">sintra_diff_report.json</a></li>
      <li><a href="/download/logic-png">logic_map.png</a> (if generated)</li>
      <li><a href="/download/logic-pdf">logic_map.pdf</a> (if generated)</li>
    </ul>
  </div>
</body>
</html>
"""

def _read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None

@app.route("/")
def home():
    brain = _read_json("sintra_brain.json")
    return render_template_string(
        TEMPLATE,
        brain=brain,
        brain_exists=os.path.exists("sintra_brain.json"),
        diff_exists=os.path.exists("sintra_diff_report.json"),
        gv_exists=os.path.exists("logic_map.gv") or os.path.exists("logic_map.gv.pdf") or os.path.exists("logic_map.png")
    )

@app.route("/api/scan")
def rescan():
    # minimal rescan: regenerate sintra_brain.json from script.py if present
    brain = {"status":"OK","note":"Lite rescan"}
    if os.path.exists("script.py"):
        try:
            with open("script.py","r",encoding="utf-8") as f:
                code = f.read()
            funcs = []
            for line in code.splitlines():
                line = line.strip()
                if line.startswith("def ") and "(" in line:
                    name = line.split("def ")[1].split("(")[0]
                    funcs.append(name)
            brain.update({"file":"script.py","functions":funcs})
        except:
            pass
    with open("sintra_brain.json","w",encoding="utf-8") as f:
        json.dump(brain,f,indent=2,ensure_ascii=False)
    return jsonify({"ok":True})

@app.route("/download/brain")
def dl_brain():
    if os.path.exists("sintra_brain.json"):
        return send_file("sintra_brain.json")
    return ("Not found", 404)

@app.route("/download/diff")
def dl_diff():
    if os.path.exists("sintra_diff_report.json"):
        return send_file("sintra_diff_report.json")
    return ("Not found", 404)

@app.route("/download/logic-png")
def dl_logic_png():
    if os.path.exists("logic_map.png"):
        return send_file("logic_map.png")
    return ("Not found", 404)

@app.route("/download/logic-pdf")
def dl_logic_pdf():
    if os.path.exists("logic_map.pdf"):
        return send_file("logic_map.pdf")
    return ("Not found", 404)

if __name__ == "__main__":
    # 0.0.0.0 lets you open from phone browser too
    app.run(host="0.0.0.0", port=8000, debug=False)
