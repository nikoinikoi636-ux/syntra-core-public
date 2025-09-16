#!/usr/bin/env python3
"""
🧠 Auto-Improver for Weak Python Files
- Добавя logging
- Генерира примерна функция, ако няма
- Превръща print -> logging
"""

from pathlib import Path

CORE = Path.home() / "WorkingProgram" / "HeartCore"
TARGETS = [
    "test123.py", "test_check.py", "test_pesh.py", "test_run.py",
    "test_script.py", "__init__.py", "ef112e5b03cf3ee474d0d3e9fdc981f6.py",
    "entity_agent.py", "sofia_1_module.py", "sofia_search_directive.py"
]

def improve(file_path: Path):
    code = file_path.read_text(encoding="utf-8")
    if "import" not in code:
        code = "import logging\nlogger = logging.getLogger(__name__)\n\n" + code

    if "def " not in code:
        code += "\ndef main():\n    logger.info('Placeholder main function')\n\n"

    if "print(" in code:
        code = code.replace("print(", "logger.info(")

    file_path.write_text(code.strip() + "\n", encoding="utf-8")
    print(f"[✓] Подобрен: {file_path.name}")

if __name__ == "__main__":
    print("🔧 Подобряване на слаби модули...")
    for fname in TARGETS:
        path = CORE / fname
        if path.exists():
            improve(path)
        else:
            print(f"[!] Пропуснат (няма такъв): {fname}")
    print("✅ Готово.")
