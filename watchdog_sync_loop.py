
#!/usr/bin/env python3
import os, time
from pathlib import Path
from analyze_collected_code import analyze_codebase

WATCH_DIR = Path.home() / "bionet_collected_code"
CHECK_INTERVAL = 10  # секунди

def run_watchdog():
    seen = set()
    print("👁️ Watchdog стартиран... следи за нови файлове.")
    while True:
        current = set(WATCH_DIR.glob("*"))
        new_files = current - seen
        if new_files:
            print(f"🆕 Открити нови файлове: {[f.name for f in new_files]}")
            analyze_codebase(WATCH_DIR)
            print("📡 (симулация) Изпращане към Sintra...")
        seen = current
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    run_watchdog()
