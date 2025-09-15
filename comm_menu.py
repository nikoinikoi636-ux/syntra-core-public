import os
import subprocess

MENU = [
    ("🧠 Run Orchestrator", "~/WorkingProgram/HeartCore/orchestrator.py"),
    ("📡 Run Sync Engine", "~/WorkingProgram/HeartCore/sync_engine.py"),
    ("🚀 Boot Levski AI", "~/WorkingProgram/HeartCore/boot_levski_v3.py"),
    ("👁️ Self Awareness", "~/WorkingProgram/HeartCore/self_awareness.py observe"),
    ("🛰️ Watchdog", "~/WorkingProgram/HeartCore/watchdog_sync_loop.py"),
    ("🎤 Speech System", "~/WorkingProgram/HeartCore/speech_script.py"),
    ("📦 Run Codex CLI", "~/HeartCore_OS_v1/sintra/sintra_codex_cli.py"),
    ("🔚 Exit", "exit")
]

def show_menu():
    while True:
        os.system("clear")
        print("=== 🧠 HeartCore Communication Menu ===")
        for i, (title, _) in enumerate(MENU, 1):
            print(f"{i}. {title}")
        choice = input("\n🧩 Избери модул (1-{}): ".format(len(MENU)))
        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(MENU):
                raise ValueError
            title, command = MENU[idx]
            if command == "exit":
                print("👋 Изход.")
                break
            print(f"\n🚀 Стартиране на: {title}\n")
            subprocess.run(["python3"] + command.split())
            input("\n🔁 Натисни Enter за връщане в менюто...")
        except Exception as e:
            print(f"⛔ Невалиден избор или грешка: {e}")
            input("Натисни Enter за опит отново...")

if __name__ == "__main__":
    show_menu()
