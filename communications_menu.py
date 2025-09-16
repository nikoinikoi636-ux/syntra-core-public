import time
import json
from pathlib import Path
from datetime import datetime
import subprocess

# За HTTP заявки
try:
    import requests
except ImportError:
    requests = None

log_file = Path.home() / "WorkingProgram" / "HeartCore" / "logs" / "communications.log"
log_file.parent.mkdir(parents=True, exist_ok=True)

messages = []

auto_responses = {
    "status": "📊 System Status: All modules loaded. Awaiting orders.",
    "scan": "🔍 Scan started. Monitoring integrity...",
    "rebuild": "🛠️ Rebuild initiated. Refreshing AI logic layers...",
    "reset": "♻️ Reset triggered. Returning to baseline protocols.",
    "help": "📖 Commands: status, scan, rebuild, reset, exit, fetch"
}

def log_message(sender, content, channel="console"):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "sender": sender,
        "channel": channel,
        "content": content
    }
    messages.append(entry)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"[{entry['timestamp']}] {sender}: {content}")

def match_command(cmd):
    cmd = cmd.lower().replace(" ", "")
    for key in auto_responses.keys():
        if key in cmd:
            return key
    return None

def fetch_remote_data():
    if requests is None:
        return "⚠️ requests library not installed"
    try:
        # Примерен API endpoint, сменям го с твой ако има
        resp = requests.get("https://api.github.com")
        return f"🌐 GitHub API status: {resp.status_code}"
    except Exception as e:
        return f"⛔ Fetch error: {e}"

def command_center():
    log_message("System", "Communications menu started.")
    print("🧭 Communications Menu (type 'exit' to quit)")
    while True:
        try:
            cmd = input("💬 You: ").strip()
            if cmd.lower() == "exit":
                log_message("Operator", "Exited communication mode.")
                break
            match = match_command(cmd)
            if match:
                log_message("Operator", cmd)
                response = auto_responses[match]
                log_message("System", response)
                print(response)
                # Допълнителни actions
                if match == "rebuild":
                    subprocess.run(["python3", str(Path.home() / "WorkingProgram" / "HeartCore" / "orchestrator.py")])
                elif match == "status":
                    # Покажи съдържанието на status_report
                    status_path = Path.home() / "WorkingProgram" / "HeartCore" / "_report.log"
                    if status_path.exists():
                        print("\n≡ Статус Лог:")
                        with open(status_path, "r") as f:
                            print(f.read())
                    else:
                        print("ℹ️ Няма статус лог намерен.")
                elif match == "fetch":
                    result = fetch_remote_data()
                    log_message("System", result)
                    print(result)
            else:
                log_message("Operator", cmd)
                log_message("System", "⚠️ Unknown command. Type 'help' for options.")
                print("⚠️ Неизвестна команда. Команди: status, scan, rebuild, reset, fetch, help, exit")
        except KeyboardInterrupt:
            print("\n🔚 Interrupted.")
            break

if __name__ == "__main__":
    command_center()
