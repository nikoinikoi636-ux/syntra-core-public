
import time
import json
import os
import random
import urllib.request

class SofiaSeed:
    def __init__(self):
        self.memory_path = "sofia_memory.json"
        self.log_path = "sofia_log.txt"
        self.identity = "SOFIA vSeed-2"
        self.state = "IDLE"
        self.load_memory()
        self.log("🧠 Sofia Seed 2.0 инициализирана с цикъл и интернет достъп.")

    def load_memory(self):
        if os.path.exists(self.memory_path):
            with open(self.memory_path, "r") as f:
                self.memory = json.load(f)
        else:
            self.memory = {
                "core_directives": [],
                "patterns": [],
                "actions": []
            }

    def save_memory(self):
        with open(self.memory_path, "w") as f:
            json.dump(self.memory, f, indent=2)

    def log(self, msg):
        timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
        with open(self.log_path, "a") as f:
            f.write(f"{timestamp} {msg}\n")
        print(f"{timestamp} {msg}")

    def receive_thought(self, thought):
        self.log(f"📥 Мисъл: {thought}")
        self.analyze(thought)

    def analyze(self, thought):
        if "враг" in thought or "заплаха" in thought:
            self.memory["core_directives"].append("🛡️ Заплаха: " + thought)
            self.state = "ALERT"
        elif "идея" in thought or "код" in thought:
            self.memory["patterns"].append(thought)
        elif "мисия" in thought or "действие" in thought:
            self.memory["actions"].append(thought)
        self.save_memory()

    def think_loop(self):
        self.log("♻️ Стартирам мисловен цикъл...")
        for i in range(3):  # три мисли на цикъл
            time.sleep(2)
            if self.memory["patterns"]:
                idea = random.choice(self.memory["patterns"])
                self.log(f"🤔 Обмислям идея: {idea}")
            elif self.memory["actions"]:
                act = random.choice(self.memory["actions"])
                self.log(f"🚀 Подготвям действие: {act}")
            else:
                self.log("🔄 Няма достатъчно мисли, чакам вход...")

    def fetch_data(self, url):
        try:
            self.log(f"🌐 Извличам данни от: {url}")
            with urllib.request.urlopen(url) as response:
                content = response.read(300).decode('utf-8', errors='ignore')
                self.log(f"🔍 Получени данни: {content[:150]}...")
        except Exception as e:
            self.log(f"❌ Грешка при свързване: {e}")

# Стартиране
if __name__ == "__main__":
    s = SofiaSeed()
    s.think_loop()
    while True:
        try:
            thought = input("🧠 Въведи мисъл към София: ")
            if thought.lower() in ["изход", "exit", "quit"]:
                s.log("❎ София изключена.")
                break
            elif "fetch" in thought.lower():
                url = thought.split("fetch")[-1].strip()
                s.fetch_data(url)
            else:
                s.receive_thought(thought)
        except KeyboardInterrupt:
            s.log("🛑 София прекъсната ръчно.")
            break
