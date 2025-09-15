
import os
import json
import ast
from pathlib import Path

heartcore_dir = Path.home() / "HeartCore"
log_file = heartcore_dir / "phoenix_rebuild_log.json"
log = {}

def check_python_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            ast.parse(f.read())
        return True
    except Exception as e:
        return str(e)

def inspect_and_rebuild():
    if not heartcore_dir.exists():
        print("📁 HeartCore directory not found. Creating...")
        heartcore_dir.mkdir(parents=True, exist_ok=True)

    for file in heartcore_dir.glob("*.py"):
        result = check_python_file(file)
        if result is True:
            print(f"✅ Valid Python file: {file.name}")
            log[file.name] = "OK"
        else:
            print(f"❌ Error in {file.name}: {result}")
            log[file.name] = f"Error: {result}"

    with open(log_file, "w", encoding="utf-8") as logf:
        json.dump(log, logf, indent=2)
    print(f"📜 Inspection log saved to {log_file}")

if __name__ == "__main__":
    print("🔁 Starting Phoenix Self-Recovery inspection...")
    inspect_and_rebuild()
