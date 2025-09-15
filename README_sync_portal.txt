Sync Portal Bundle (Offline)
============================
Purpose: Let two local agents ("ChatGPT" and "Sintra") exchange messages *offline* via a small Flask server
or via direct file writes (no external network). Everything stays on 127.0.0.1 and local files.

Files
-----
- portal_server.py   : Flask server exposing /api/chatgpt, /api/sintra, /history, /health
- file_bridge.py     : CLI tool to append messages without HTTP (writes JSON lines to portal_log.jsonl)
- manifest_runner.py : Optional simulator that replays a manifest JSON/YAML into the server (localhost only)
- run_portal.sh      : Helper to start portal server
- README_sync_portal.txt : This file

Install (Termux)
----------------
cd ~/downloads
unzip sync_portal_bundle.zip -d sync_portal
cd sync_portal
pip install flask >/dev/null 2>&1 || true

# Start portal
./run_portal.sh
# -> http://127.0.0.1:5001/health  should return {"ok": true}

Usage
-----
1) Send message from "ChatGPT" side (HTTP):
   curl -s -X POST http://127.0.0.1:5001/api/chatgpt -H "Content-Type: application/json" -d '{"message":"Hello from ChatGPT"}'

2) Send message from "Sintra" side (HTTP):
   curl -s -X POST http://127.0.0.1:5001/api/sintra -H "Content-Type: application/json" -d '{"message":"Hello from Sintra"}'

3) Read history:
   curl -s http://127.0.0.1:5001/history

4) Without HTTP (no requests/curl), write directly:
   python3 file_bridge.py to_sintra "Local-only message to Sintra"
   python3 file_bridge.py to_chatgpt "Local-only message to ChatGPT"

5) Optional: Replay a manifest (JSON/YAML) to simulate conversation
   # Example manifest.json:
   # [
   #   {"origin":"ChatGPT","message":"Ping A"}, 
   #   {"origin":"Sintra","message":"Pong A"}
   # ]
   python3 manifest_runner.py manifest.json

Outputs
-------
- portal_log.jsonl    : append-only log of all messages (JSON lines)
- last_chatgpt.json   : last message sent by ChatGPT side
- last_sintra.json    : last message sent by Sintra side

Security
--------
- Binds to 127.0.0.1 only (local machine).
- No external calls; no persistence elsewhere.
- You can delete portal_log.jsonl anytime.
