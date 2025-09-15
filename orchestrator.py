#!/usr/bin/env python3
import subprocess
import sys
import os
import signal
from pathlib import Path
from datetime import datetime

MODULES = [
    "speech_script.py",
    "boot_levski_v3.py",
    "self_awareness.py",
    "sync_engine.py",
    "watchdog_sync_loop.py"
]

HC = Path.home() / "WorkingProgram" / "HeartCore"
LOG = HC / "orchestrator.log"
LOG_DIR = HC / "logs" / "modules"
LOG_DIR.mkdir(parents=True, exist_ok=True)

processes = []

def log(msg: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full = f"[{now}] {msg}"
    print(full)
    with open(LOG, "a") as f:
        f.write(full + "\n")

def run_module_async(module: str):
    file_path = HC / module
    if not file_path.exists():
        log(f"⛔ File not found: {module}")
        return
    log_file = LOG_DIR / f"{module.replace('.py', '')}.log"
    log(f"🚀 Launching (bg): {module}")
    proc = subprocess.Popen(
        ["python3", str(file_path)],
        stdout=open(log_file, "a"),
        stderr=subprocess.STDOUT
    )
    processes.append((module, proc))

def sync_to_git():
    log("☁️ Syncing to GitHub...")
    try:
        subprocess.run(["git", "add", "."], cwd=HC, check=True)
        subprocess.run(
            ["git", "commit", "-m", "🔁 Auto-sync after orchestrator run"],
            cwd=HC,
            check=False
        )
        subprocess.run(["git", "push"], cwd=HC, check=True)
        log("✅ Git sync completed.")
    except subprocess.CalledProcessError as e:
        log(f"❌ Git error: {e}")

def main():
    log("🧠 HeartCore Orchestrator v3 Starting (parallel + git sync)...")
    for module in MODULES:
        run_module_async(module)

    log("⏳ Waiting for modules to complete... (Ctrl+C to interrupt)")
    try:
        for name, proc in processes:
            ret = proc.wait(timeout=180)
            log(f"✅ {name} exited with code {ret}")
    except subprocess.TimeoutExpired:
        log(f"⏰ Timeout waiting for module.")
    except KeyboardInterrupt:
        log("🛑 Interrupted. Terminating all child processes...")
        for name, proc in processes:
            proc.terminate()
        log("✅ All processes terminated by user.")
    except Exception as e:
        log(f"❗ Unexpected error: {e}")
    finally:
        sync_to_git()
        log("✅ All modules processed.\n")

if __name__ == "__main__":
    main()
