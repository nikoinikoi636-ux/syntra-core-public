#!/usr/bin/env python3
import subprocess
import sys
import os
import signal
from pathlib import Path
from datetime import datetime
import time
import json

# Constants
HC = Path.home() / "WorkingProgram" / "HeartCore"
LOG = HC / "orchestrator.log"
LOG_DIR = HC / "logs" / "modules"
LOG_DIR.mkdir(parents=True, exist_ok=True)

MODULES = [
    "speech_script.py",
    "boot_levski_v3.py",
    "self_awareness.py",
    "sync_engine.py",
    "watchdog_sync_loop.py"
]

DETACHED_MODULES = {"sync_engine.py", "watchdog_sync_loop.py"}
MAX_RETRIES = 2
TIMEOUT = 180
GIT_ENABLED = True  # Disable if not using Git

def log(msg: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full = f"[{now}] {msg}"
    print(full)
    with open(LOG, "a") as f:
        f.write(full + "\n")

def run_module(module: str, attempt: int = 1):
    file_path = HC / module
    if not file_path.exists():
        log(f"⛔ File not found: {module}")
        return False

    log_file = LOG_DIR / f"{module.replace('.py', '')}.log"
    if module in DETACHED_MODULES:
        log(f"🚀 Launching (detached): {module}")
        subprocess.Popen(
            ["python3", str(file_path)],
            cwd=str(HC),
            stdout=open(log_file, "a"),
            stderr=subprocess.STDOUT
        )
        return True

    for i in range(1, MAX_RETRIES + 1):
        log(f"🚀 Launching: {module} (attempt {i})")
        try:
            proc = subprocess.run(
                ["python3", str(file_path)],
                cwd=str(HC),
                timeout=TIMEOUT,
                check=True,
                stdout=open(log_file, "a"),
                stderr=subprocess.STDOUT
            )
            log(f"✅ {module} exited with code 0")
            return True
        except subprocess.TimeoutExpired:
            log(f"⏰ Timeout: {module}")
        except subprocess.CalledProcessError as e:
            log(f"❌ {module} failed with code {e.returncode}")
    log(f"❗ Max retries reached: {module}")
    return False

def git_sync():
    if not GIT_ENABLED:
        return
    log("☁️ Syncing to GitHub...")
    try:
        subprocess.run(["git", "add", "."], cwd=str(HC), check=True)
        subprocess.run(["git", "commit", "-m", "🔁 Auto-sync after orchestrator run"], cwd=str(HC), check=False)
        subprocess.run(["git", "push"], cwd=str(HC), check=True)
        log("✅ Git sync complete.")
    except Exception as e:
        log(f"❌ Git sync failed: {e}")

def analyze_logs():
    log("📊 Analyzing module logs...")
    errors = {}
    for file in LOG_DIR.glob("*.log"):
        with open(file) as f:
            content = f.read()
        found = [line for line in content.splitlines() if "error" in line.lower() or "exception" in line.lower()]
        if found:
            errors[file.name] = found
    if errors:
        out_path = HC / "logs" / "analyzed_errors.json"
        with open(out_path, "w") as f:
            json.dump(errors, f, indent=2)
        log(f"🧠 Errors saved to: {out_path}")
    else:
        log("✅ No errors detected in module logs.")

def main():
    log("🧠 HeartCore Orchestrator v4 Starting...")
    results = []
    for module in MODULES:
        result = run_module(module)
        results.append((module, result))

    git_sync()
    analyze_logs()

    failed = [m for m, ok in results if not ok]
    if failed:
        log("❗ Failed modules: " + ", ".join(failed))
    else:
        log("✅ All modules completed successfully.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("🛑 Interrupted by user.")
        sys.exit(0)
