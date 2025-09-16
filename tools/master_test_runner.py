#!/usr/bin/env python3
"""
🧪 Master Test Runner
- Сканира всички .py файлове
- Стартира ги, ако имат main() или init()
- Логва резултатите
"""

import subprocess
from pathlib import Path

CORE = Path.home() / "WorkingProgram" / "HeartCore"
EXCLUDE = {"__init__.py", "main.py", "orchestrator.py", "boot_levski.py"}
LOG_FILE = CORE / "logs" / "test_runner.log"

def has_testable_fn(code: str) -> bool:
    return "def main" in code or "def init" in code

def run_script(path: Path):
    try:
        result = subprocess.run(["python3", str(path)], capture_output=True, text=True, timeout=15)
        status = "✅ OK" if result.returncode == 0 else f"❌ ERR {result.returncode}"
        return status, result.stdout.strip() + "\n" + result.stderr.strip()
    except subprocess.TimeoutExpired:
        return "⏰ Timeout", f"{path.name} не отговори навреме."

def main():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "w", encoding="utf-8") as log:
        log.write("📋 Тестови резултати\n\n")
        for py_file in CORE.glob("*.py"):
            if py_file.name in EXCLUDE:
                continue
            code = py_file.read_text(encoding="utf-8", errors="ignore")
            if not has_testable_fn(code):
                continue
            status, output = run_script(py_file)
            log.write(f"--- {py_file.name} [{status}] ---\n{output}\n\n")
            print(f"[{status}] {py_file.name}")

if __name__ == "__main__":
    main()
