import time
import json
from pathlib import Path
from datetime import datetime

log_file = Path.home() / "WorkingProgram" / "HeartCore" / "logs" / "communications.log"
log_file.parent.mkdir(parents=True, exist_ok=True)

messages = []

auto_responses = {
    "status": "📊 System Status: All modules loaded. Awaiting orders.",
    "scan": "🔍 Scan started. Monitoring integrity...",
    "rebuild": "🛠️ Rebuild initiated. Refreshing AI logic layers...",
    "reset": "♻️ Reset triggered. Returning to baseline protocols.",
    "help": "📖 Commands: status, scan, rebuild, reset, exit"
}

def match_command(cmd):
    cmd = cmd.lower().replace(" ", "")
    for key in auto_responses.keys():
        if key in cmd:
            return key
    return None

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

def command_center():
    print("🧭 Communications Menu (type 'exit' to quit)")
    while True:
        try:
            cmd = input("💬 You: ").strip()
            if cmd.lower() == "exit":
                log_message("Operator", "Exited communication mode.")
                break
            match = match_command(cmd)
            if match:
                response = auto_responses[match]
                log_message("Operator", cmd)
                log_message("System", response)
            else:
                log_message("Operator", cmd)
                log_message("System", "⚠️ Unknown command. Type 'help' for options.")
        except KeyboardInterrupt:
            print("\n🔚 Interrupted.")
            break

if __name__ == "__main__":
    log_message("System", "Communications menu started.")
    command_center()
