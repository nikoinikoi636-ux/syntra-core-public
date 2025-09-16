import time
import json
from pathlib import Path
from datetime import datetime

log_file = Path.home() / "WorkingProgram" / "HeartCore" / "logs" / "communications.log"
log_file.parent.mkdir(parents=True, exist_ok=True)

messages = []

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
            cmd = input("💬 You: ")
            if cmd.strip().lower() == "exit":
                log_message("Operator", "Exited communication mode.")
                break
            elif cmd.strip().lower() == "status":
                log_message("System", "Status requested: All modules operational.")
            else:
                log_message("Operator", cmd)
        except KeyboardInterrupt:
            print("\n🔚 Interrupted.")
            break

if __name__ == "__main__":
    log_message("System", "Communications menu started.")
    command_center()
