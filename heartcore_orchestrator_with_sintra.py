heartcore_orchestrator_with_sintra.py

import json import subprocess from pathlib import Path from datetime import datetime

config_path = Path.home() / "WorkingProgram" / "HeartCore" / "config.json" modules_dir = Path.home() / "WorkingProgram" / "HeartCore" sintra_cli_path = Path.home() / "HeartCore_OS_v1" / "sintra" / "sintra_codex_cli.py"

def log(msg): timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S") print(f"[{timestamp}] {msg}")

def load_config(): try: with open(config_path, "r", encoding="utf-8") as f: return json.load(f) except Exception as e: log(f"❌ Error loading config: {e}") return {}

def run_module(module, status_report): name = module.get("name") file = module.get("file") enabled = module.get("enabled", False) file_path = modules_dir / file

if not file_path.exists():
    log(f"⚠️ Missing: {name}")
    status_report[name] = "Missing"
    return

if not enabled:
    log(f"⏸️ Skipped: {name}")
    status_report[name] = "Skipped"
    return

log(f"🚀 Launching: {name}")
try:
    subprocess.run(["python3", str(file_path)], check=True, timeout=120)
    status_report[name] = "OK"
except subprocess.TimeoutExpired:
    log(f"⛔ Timeout: {name}")
    status_report[name] = "Timeout"
except subprocess.CalledProcessError as e:
    log(f"⛔ Error in: {name}: {e}")
    status_report[name] = "Error"
except Exception as e:
    log(f"⛔ Crash: {name}: {e}")
    status_report[name] = "Crash"

def run_sintra_actions(): if not sintra_cli_path.exists(): log("⚠️ Sintra CLI not found") return

log("🧠 Verifying Sintra Codex...")
subprocess.run(["python3", str(sintra_cli_path), "check"])

log("🔄 Rebuilding Sintra with backup...")
subprocess.run(["python3", str(sintra_cli_path), "rebuild", "--backup"])

def main(): log("🧠 HeartCore Orchestrator v3 Starting...") status_report = {} config = load_config() for module in config.get("modules", []): run_module(module, status_report)

run_sintra_actions()

log("✅ All modules processed.")
for k, v in status_report.items():
    print(f" - {k}: {v}")

if name == "main": main()

