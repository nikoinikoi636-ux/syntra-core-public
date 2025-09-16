#!/usr/bin/env python3
"""
🔁 Auto-Merge Patch Engine
- Чете self_improvement_suggestions.json
- Генерира инструкции за merge
- Показва какво да се оправи
"""
import json
from pathlib import Path

SUGGESTIONS = Path.home() / "WorkingProgram" / "HeartCore" / "logs" / "self_improvement_suggestions.json"
OUT_PATCH = Path.home() / "WorkingProgram" / "HeartCore" / "logs" / "auto_patch_plan.txt"

def generate_patch_plan():
    if not SUGGESTIONS.exists():
        print("❌ Няма предложения за подобрение.")
        return

    with open(SUGGESTIONS, encoding="utf-8") as f:
        suggestions = json.load(f)

    with open(OUT_PATCH, "w", encoding="utf-8") as f:
        for fname, data in suggestions.items():
            f.write(f"# 🛠️ Модул: {fname}\n")
            for err in data["errors"]:
                f.write(f"- Проблем: {err.strip()}\n")
            f.write(f"- 🔧 Предложение: {data['suggestion']}\n\n")
    
    print(f"[✅] Auto-patch план записан в: {OUT_PATCH}")

if __name__ == "__main__":
    generate_patch_plan()
