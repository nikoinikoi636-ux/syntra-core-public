#!/usr/bin/env python3
"""
💡 HeartCore Self Improver Module
- Анализира логове
- Засича повтарящи се проблеми
- Генерира предложения за подобрения
"""
import json, re
from pathlib import Path

LOG_DIR = Path.home() / "WorkingProgram" / "HeartCore" / "logs" / "modules"
OUT_FILE = Path.home() / "WorkingProgram" / "HeartCore" / "logs" / "self_improvement_suggestions.json"

def extract_errors(log_text):
    lines = log_text.lower().splitlines()
    return [line for line in lines if "error" in line or "exception" in line or "traceback" in line]

def suggest_improvements():
    results = {}
    for log_file in LOG_DIR.glob("*.log"):
        with open(log_file) as f:
            text = f.read()
        errors = extract_errors(text)
        if errors:
            results[log_file.name] = {
                "errors": errors,
                "suggestion": f"Модулът {log_file.name} съдържа {len(errors)} грешки. Провери логиката около ключовите функции и импорти."
            }
    with open(OUT_FILE, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"[🧠] Създадени предложения за подобрения: {OUT_FILE}")

if __name__ == "__main__":
    suggest_improvements()
