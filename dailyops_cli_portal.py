#!/usr/bin/env python3
# DailyOps -> Offline Portal Bridge (defensive)
import json, os, datetime, platform, shutil
from pathlib import Path

# достъп до portal_client.py (намира се в родителската папка на adapters/)
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from portal_client import to_chatgpt

def collect_status():
    # uptime (ако има)
    try:
        uptime = os.popen("uptime").read().strip()
    except Exception:
        uptime = "n/a"
    return {
        "uptime": uptime,
        "cwd": str(Path.cwd()),
        "python": platform.python_version(),
        "disk_free_mb": shutil.disk_usage(".").free // (1024*1024),
    }

def now_utc():
    # избягваме DeprecationWarning за utcnow()
    return datetime.datetime.now(datetime.UTC).isoformat()

def main():
    event = {
        "component": "DailyOps",
        "event": "status",
        "data": collect_status(),
        "ts": now_utc()
    }
    res = to_chatgpt(event)
    print(json.dumps({"sent": event, "portal_response": res}, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
