#!/usr/bin/env python3
"""
🩹 AutoFix: липсващи Python модули (имена от логовете)
- Сканира логовете за "ModuleNotFoundError"
- Създава празен файл с правилно име, ако не съществува
"""
import re
from pathlib import Path

LOG_DIR = Path.home() / "WorkingProgram" / "HeartCore" / "logs"
CORE_DIR = Path.home() / "WorkingProgram" / "HeartCore"

def find_missing_modules():
    missing = set()
    pattern = re.compile(r"No module named ['\"]([\w_]+)['\"]", re.IGNORECASE)

    for log_file in LOG_DIR.glob("*.log"):
        with open(log_file, encoding="utf-8", errors="ignore") as f:
            for line in f:
                match = pattern.search(line)
                if match:
                    missing.add(match.group(1))

    return sorted(missing)

def create_module(name: str):
    fname = CORE_DIR / f"{name}.py"
    if not fname.exists():
        with open(fname, "w", encoding="utf-8") as f:
            f.write(f'""" 🔧 Auto-created stub for missing module: {name} """\n\n')
            f.write("def init():\n    pass\n")
        print(f"[+] Създаден: {fname}")
    else:
        print(f"[✓] Вече съществува: {fname}")

if __name__ == "__main__":
    print("🔍 Сканирам за липсващи модули...")
    missing = find_missing_modules()
    if not missing:
        print("✅ Няма липсващи модули в логовете.")
    else:
        print(f"🚨 Намерени липсващи модули: {missing}")
        for name in missing:
            create_module(name)
        print("✅ Готово.")
