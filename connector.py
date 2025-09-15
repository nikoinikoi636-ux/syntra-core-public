from fastapi import FastAPI, Request, Header, HTTPException
import uvicorn, os, hmac, hashlib, json, time, subprocess, requests

SINTRA_URL = os.environ["SINTRA_WEBHOOK_URL"]
BEARER = os.environ.get("SINTRA_BEARER", "")
NODE = os.environ.get("HC_NODE_ID","node")
SECRET = os.environ.get("HC_SHARED_SECRET","")

app = FastAPI()

def post_to_sintra(payload: dict):
    headers = {"Content-Type":"application/json"}
    if BEARER: headers["Authorization"] = f"Bearer {BEARER}"
    r = requests.post(SINTRA_URL, headers=headers, json=payload, timeout=10)
    r.raise_for_status()
    return r.json() if r.text else {"ok":True}

def verify_sig(raw_body: bytes, sig: str):
    if not SECRET: return True
    expected = hmac.new(SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig or "")

@app.post("/event")
async def receive_event(request: Request, x_hc_sig: str = Header(default="")):
    raw = await request.body()
    if not verify_sig(raw, x_hc_sig): raise HTTPException(401, "bad signature")
    data = json.loads(raw or "{}")
    # нормализираме събитие -> съобщение в Sintra
    payload = {
        "channel": "heartcore",
        "author": NODE,
        "type": "event",
        "timestamp": int(time.time()),
        "data": data
    }
    try:
        resp = post_to_sintra(payload)
        return {"ok": True, "sintra": resp}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/send")
async def send_to_sintra(msg: dict):
    # директно пращане на чат съобщение
    payload = {
        "channel": "heartcore",
        "author": NODE,
        "type": "message",
        "text": msg.get("text",""),
        "meta": msg.get("meta",{})
    }
    return post_to_sintra(payload)

@app.post("/cmd")
async def run_cmd(body: dict, x_hc_sig: str = Header(default="")):
    raw = (await Request.body.__wrapped__(Request))(request=None)  # not used
    # проста защита – изискваме секрет
    if SECRET and x_hc_sig != SECRET: raise HTTPException(401,"unauthorized")
    cmd = body.get("cmd")
    if not cmd: return {"ok": False, "error": "no cmd"}
    try:
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=30).decode()
        post_to_sintra({"channel":"heartcore","author":NODE,"type":"cmd_result","text":out})
        return {"ok": True, "out": out}
    except subprocess.CalledProcessError as e:
        return {"ok": False, "error": e.output.decode()}
