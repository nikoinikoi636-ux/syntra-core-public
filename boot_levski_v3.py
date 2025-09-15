import time
from pathlib import Path

def log(msg):
    print(f"[Levski Boot] {msg}")

def scan_files():
    home = Path.home()
    downloads = home / "downloads"
    if not downloads.exists():
        log("❌ Downloads папката не съществува.")
        return

    log(f"📂 Сканиране на {downloads}")
    py_files = list(downloads.glob("*.py"))
    for f in py_files:
        log(f"🔍 Намерен .py файл: {f.name}")

def main():
    log("🚀 Initializing Levski AI boot sequence...")
    time.sleep(1)

    # Основна логика
    scan_files()

    # Симулирай зареждане
    time.sleep(1)
    log("✅ Levski AI успешно зареден.")

if __name__ == "__main__":
    main()
