import os, hmac, hashlib, time, json, subprocess, requests
from flask import Flask, request, jsonify, abort

SINTRA_URL = os.environ.get("SINTRA_WEBHOOK_URL","")
BEARER     = os.environ.get("SINTRA_BEARER","")
NODE       = os.environ.get("HC_NODE_ID","varnavlad-01")
SECRET     = os.environ.get("HC_SHARED_SECRET","")

app = Flask(__name__)

@app.get("/health")
def health():
    return {"ok": True, "node": NODE, "sintra_url_set": bool(SINTRA_URL)}

def post_to_sintra(payload: dict):
    if not SINTRA_URL:
        return {"ok": True, "note": "SINTRA_WEBHOOK_URL not set (local test)"}
    headers = {"Content-Type":"application/json"}
    if BEARER: headers["Authorization"] = f"Bearer {BEARER}"
    r = requests.post(SINTRA_URL, headers=headers, json=payload, timeout=10)
    try: return r.json()
    except Exception: return {"status": r.status_code, "text": r.text}

def verify_sig(raw_body: bytes, sig: str):
    if not SECRET: return True
    expected = hmac.new(SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig or "")

@app.post("/send")
def send_msg():
    data = request.get_json(silent=True) or {}
    payload = {"channel":"heartcore","author":NODE,"type":"message",
               "text": data.get("text",""), "meta": data.get("meta",{})}
    return jsonify(post_to_sintra(payload))

@app.post("/event")
def recv_event():
    raw = request.get_data()
    sig = request.headers.get("X-HC-Sig","")
    if not verify_sig(raw, sig): abort(401)
    data = request.get_json(silent=True) or {}
    payload = {"channel":"heartcore","author":NODE,"type":"event",
               "timestamp": int(time.time()), "data": data}
    return jsonify(post_to_sintra(payload))

@app.post("/cmd")
def run_cmd():
    if SECRET and request.headers.get("X-HC-Sig","") != SECRET: abort(401)
    body = request.get_json(silent=True) or {}
    cmd = body.get("cmd")
    if not cmd: return jsonify({"ok":False,"error":"no cmd"}), 400
    try:
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=30).decode()
        post_to_sintra({"channel":"heartcore","author":NODE,"type":"cmd_result","text":out})
        return jsonify({"ok":True,"out":out})
    except subprocess.CalledProcessError as e:
        return jsonify({"ok":False,"error":e.output.decode()}), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8787)
