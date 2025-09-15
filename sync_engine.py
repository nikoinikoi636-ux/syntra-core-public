import os, time, json, subprocess
from pathlib import Path

WATCH_DIR = Path(".")
GITHUB_REPO = "yourusername/sintra-sync-ai"
REMOTE_NAME = "origin"

def sync_to_github():
    print("☁️ Syncing to GitHub...")
    subprocess.run(["git", "add", "."], check=False)
    subprocess.run(["git", "commit", "-m", "🔁 Auto-sync update"], check=False)
    subprocess.run(["git", "push", REMOTE_NAME, "main"], check=False)

def load_external_knowledge():
    # Stub for future implementation (API, GitHub clone, etc.)
    print("📚 Pulling external knowledge...")

def monitor():
    print("🛰️ Real-time sync engine started")
    known_files = set()
    while True:
        current_files = set(WATCH_DIR.glob("*.py"))
        new_files = current_files - known_files
        if new_files:
            print(f"🔍 New/changed files detected: {[f.name for f in new_files]}")
            sync_to_github()
            load_external_knowledge()
        known_files = current_files
        time.sleep(10)

if __name__ == "__main__":
    monitor()