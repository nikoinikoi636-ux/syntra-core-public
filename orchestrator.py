import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

config_path = Path.home() / "WorkingProgram" / "HeartCore" / "config.json"
modules_dir = Path.home() / "WorkingProgram" / "HeartCore"
log_path = modules_dir / "_report.log"

def log(msg):
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {msg}\n")
    print(msg)

def load_config():
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def run_module(module, status_report):
    name = module["name"]
    file_path = modules_dir / module["file"]
    if not file_path.exists():
        log(f"⚠️ Missing: {name}")
        status_report[name] = "missing"
        return
    if not module["enabled"]:
        log(f"⏸️ Skipped: {name}")
        status_report[name] = "skipped"
        return

    for attempt in range(3):
        try:
            log(f"🚀 Launching: {name} (attempt {attempt+1})")
            subprocess.run(["python3", str(file_path)], timeout=180, check=True)
            log(f"✅ Completed: {name}")
            status_report[name] = "completed"
            return
        except subprocess.TimeoutExpired:
            log(f"⛔ Timeout: {name} (attempt {attempt+1})")
            status_report[name] = "timeout"
        except subprocess.CalledProcessError as e:
            log(f"⛔ Error in {name}: {e}")
            status_report[name] = "error"
        except Exception as e:
            log(f"⛔ Crash in {name}: {e}")
            status_report[name] = "crash"
    log(f"💥 Permanent failure in: {name}")

def main():
    status_report = {}
    log("🧠 HeartCore Orchestrator v3 Starting...")
    config = load_config()
    for module in config.get("modules", []):
        run_module(module, status_report)
    log("✅ All modules processed.")

if __name__ == "__main__":
    main()
