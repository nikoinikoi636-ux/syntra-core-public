import json
import subprocess
from pathlib import Path
from datetime import datetime

config_path = Path.home() / "WorkingProgram" / "HeartCore" / "config.json"
modules_dir = Path.home() / "WorkingProgram" / "HeartCore"
log_path = modules_dir / "heartcore_error.log"
status_path = modules_dir / "module_status.json"

def log_error(msg):
    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"[{datetime.now()}] {msg}\n")

def load_config():
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def run_module(module, status_report):
    file_path = modules_dir / module["file"]
    name = module["name"]

    if not file_path.exists():
        print(f"⚠️ Missing: {name}")
        log_error(f"Missing file: {file_path}")
        status_report[name] = "missing"
        return

    if not module.get("enabled", False):
        print(f"⏸️ Skipped: {name}")
        status_report[name] = "skipped"
        return

    print(f"🚀 Launching: {name}")
    try:
        subprocess.run(["python3", str(file_path)], timeout=15, check=True)
        status_report[name] = "ok"
    except subprocess.TimeoutExpired:
        print(f"⛔ Timeout: {name}")
        log_error(f"Timeout in module: {name}")
        status_report[name] = "timeout"
    except subprocess.CalledProcessError as e:
        print(f"⛔ Error in: {name}")
        log_error(f"Error in {name}: {e}")
        status_report[name] = "error"
    except Exception as e:
        print(f"⛔ Crash: {name}")
        log_error(f"Crash in {name}: {e}")
        status_report[name] = "crash"

def main():
    print("🧠 HeartCore Orchestrator v3 Starting...")
    config = load_config()
    status_report = {}
    for module in config.get("modules", []):
        run_module(module, status_report)
    with open(status_path, "w", encoding="utf-8") as f:
        json.dump(status_report, f, indent=2)
    print("✅ All modules processed.")

if __name__ == "__main__":
    main()
