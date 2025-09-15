#!/usr/bin/env python3
# manifest_runner.py - replay a local manifest into the portal (prefers HTTP; falls back to file_bridge)
import sys, json, time
from pathlib import Path

def load_manifest(path: Path):
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except Exception:
        # naive YAML-to-JSON: only supports arrays of simple objects
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        items = []
        cur = {}
        for line in lines:
            if line.startswith("-"):
                if cur:
                    items.append(cur); cur = {}
                line = line[1:].strip()
                if line:
                    k, _, v = line.partition(":")
                    cur[k.strip()] = v.strip().strip('"\'')
            else:
                k, _, v = line.partition(":")
                cur[k.strip()] = v.strip().strip('"\'')
        if cur:
            items.append(cur)
        return items

def try_http_send(origin, message):
    try:
        import requests
        url = "http://127.0.0.1:5001/api/chatgpt" if origin.lower().startswith("chat") else "http://127.0.0.1:5001/api/sintra"
        requests.post(url, json={"message": message}, timeout=2)
        return True
    except Exception:
        return False

def file_send(origin, message):
    from file_bridge import send as file_send_fn
    file_send_fn(origin, message)

def main():
    if len(sys.argv) < 2:
        print("Usage: manifest_runner.py <manifest.json|yaml>")
        raise SystemExit(2)
    manifest = load_manifest(Path(sys.argv[1]))
    if not isinstance(manifest, list):
        print("Manifest must be a list of messages: [{origin, message}, ...]")
        raise SystemExit(2)

    use_http = try_http_send("ChatGPT", "__portal_warmup__")
    for entry in manifest:
        origin = entry.get("origin", "ChatGPT")
        message = entry.get("message", "")
        if use_http:
            ok = try_http_send(origin, message)
            if not ok:
                file_send(origin, message)
        else:
            file_send(origin, message)
        time.sleep(0.1)

if __name__ == "__main__":
    main()
