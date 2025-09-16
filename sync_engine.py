import subprocess
import os
from datetime import datetime
from pathlib import Path

log_dir = Path.home() / "WorkingProgram" / "HeartCore" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
error_log = log_dir / "git_sync_errors.log"

def log(msg):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(error_log, "a") as f:
        f.write(f"{timestamp} {msg}\n")
    print(f"{timestamp} {msg}")

def git_command(cmd, allow_fail=False):
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        if not allow_fail:
            log(f"❌ Error: {e}")
        return False

def auto_git_sync():
    log("📡 Starting Git auto-sync...")
    if not git_command(["git", "status"], allow_fail=True):
        log("⚠️ Not a git repo. Skipping sync.")
        return

    if git_command(["git", "push"]):
        log("✅ Regular push successful.")
        return

    log("🔁 Conflict detected. Trying rebase...")
    if git_command(["git", "pull", "--rebase"]):
        log("🔃 Rebase succeeded. Retrying push...")
        if git_command(["git", "push"]):
            log("✅ Push after rebase succeeded.")
            return

    log("💣 Rebase failed. Forcing push as last resort...")
    if git_command(["git", "push", "-f"]):
        log("⚠️ Force push completed. Review if needed.")
    else:
        log("🛑 Force push failed. Manual intervention needed.")

if __name__ == "__main__":
    auto_git_sync()
