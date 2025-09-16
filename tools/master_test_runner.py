#!/usr/bin/env python3
"""
🧪 Лек Master Test Runner
- Стартира един или всички Python файлове
- Проверява за main/init
- Работи икономично (Termux-friendly)
"""

import subprocess
from pathlib import Path
import sys

CORE = Path.home() / "WorkingProgram" / "HeartCore"
LOG_FILE = CORE / "logs" / "test_runner.log"
EXCLUDE = {"__init__.py", "main.py", "orchestrator.py", "boot_levski.py"}

def has_testable_fn(code: str) -> bool:
    return "def main" in code or "def init" in code

def run_script(path: Path):
    try:
        result = subprocess.run(
            ["python3", str(path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        status = "✅ OK" if result.returncode == 0 else f"❌ ERR {result.returncode}"
        return status, result.stdout.strip() + "\n" + result.stderr.strip()
    except subprocess.TimeoutExpired:
        return "⏰ Timeout", f"{path.name} не отговори навреме."
    except Exception as e:
        return "❌ Exception", str(e)

def main():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    args = sys.argv[1:]
    targets = []

    if args:
        file_name = args[0]
        file_path = CORE / file_name
        if file_path.exists():
            targets = [file_path]
        else:
            print(f"❌ Файлът не съществува: {file_name}")
            return
    else:
        # Няма аргументи → сканираме всички *.py
        for py in CORE.glob("*.py"):
            if py.name not in EXCLUDE:
                code = py.read_text(encoding="utf-8", errors="ignore")
                if has_testable_fn(code):
                    targets.append(py)

    if not targets:
        print("⚠️ Няма открити файлове за тестване.")
        return

    with open(LOG_FILE, "w", encoding="utf-8") as log:
        for py_file in targets:
            status, output = run_script(py_file)
            log.write(f"--- {py_file.name} [{status}] ---\n{output}\n\n")
            print(f"[{status}] {py_file.name}")

    print(f"\n📄 Записано в: {LOG_FILE}")

if __name__ == "__main__":
    main()
