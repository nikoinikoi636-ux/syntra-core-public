#!/usr/bin/env python3
"""
🧪 Стартира всички тестове в системата
"""
import subprocess
from pathlib import Path

TEST_DIR = Path.home() / "WorkingProgram" / "HeartCore"
files = list(TEST_DIR.glob("test_*.py"))

print(f"[🔍] Открити тестови файлове: {len(files)}")

for test_file in files:
    print(f"[▶️] Стартирам {test_file.name}")
    subprocess.run(["python3", str(test_file)])
