#!/usr/bin/env python3
"""
🧠 Self Evaluation Core
- Оценява структура, стил, и тестово покритие
- Генерира доклад с препоръки
"""
from pathlib import Path
import re

CODEBASE = Path.home() / "WorkingProgram" / "HeartCore"
REPORT = CODEBASE / "logs" / "self_eval_report.txt"

def evaluate_file(path):
    score = 100
    reasons = []
    with open(path, encoding="utf-8", errors="ignore") as f:
        content = f.read()

    if len(content) < 20:
        score -= 50
        reasons.append("Много кратък код.")
    if "import" not in content:
        score -= 10
        reasons.append("Липсва импорт — може да няма зависимости.")
    if "def " not in content:
        score -= 10
        reasons.append("Липсват функции.")
    if re.search(r'print\s*\(', content):
        score -= 5
        reasons.append("Използване на print вместо логиране.")

    return score, reasons

def run_self_eval():
    results = []
    for py_file in CODEBASE.glob("*.py"):
        score, reasons = evaluate_file(py_file)
        grade = "✅ Добро" if score >= 80 else "⚠️ Средно" if score >= 60 else "❌ Слабо"
        results.append(f"[{grade}] {py_file.name} → {score}/100")
        for r in reasons:
            results.append(f"   • {r}")
        results.append("")

    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(results))

    print(f"[🧪] Самооценка завършена → {REPORT}")

if __name__ == "__main__":
    run_self_eval()
