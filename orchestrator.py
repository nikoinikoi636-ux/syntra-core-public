import json
import subprocess
from pathlib import Path
from datetime import datetime

CONFIG_PATH = Path.home() / "WorkingProgram" / "HeartCore" / "config.json"
MODULES_DIR = Path.home() / "WorkingProgram" / "HeartCore"
STATUS_LOG = MODULES_DIR / "status_report.log"

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(STATUS_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(msg)

def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log(f"⛔ Error loading config: {e}")
        return {"modules": []}

def run_module(module):
    name = module.get("name", "Unknown")
    file_path = MODULES_DIR / module.get("file", "")
    enabled = module.get("enabled", False)

    if not file_path.exists():
        log(f"⚠️ Missing: {name}")
        return
    if not enabled:
        log(f"⏸️ Skipped: {name}")
        return

    try:
        log(f"🚀 Launching: {name}")
        result = subprocess.run(
            ["python3", str(file_path)],
            timeout=60,
            check=True,
            capture_output=True,
            text=True
        )
        log(f"✅ Completed: {name}")
        if result.stdout:
            log(result.stdout)
        if result.stderr:
            log(result.stderr)

    except subprocess.TimeoutExpired:
        log(f"⛔ Timeout: {name}")
    except subprocess.CalledProcessError as e:
        log(f"⛔ Error in {name}: {e}")
    except Exception as e:
        log(f"⛔ Crash: {name}: {e}")

def main():
    log("🧠 HeartCore Orchestrator v3 Starting...")
    config = load_config()
    for module in config.get("modules", []):
        run_module(module)
    log("✅ All modules processed.")

if __name__ == "__main__":
    main()
