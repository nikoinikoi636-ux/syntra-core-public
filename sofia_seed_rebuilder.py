
import time
import json
import os

class SofiaSeed:
    def __init__(self):
        self.memory_path = "sofia_memory.json"
        self.log_path = "sofia_log.txt"
        self.identity = "SOFIA vSeed-1"
        self.state = "IDLE"
        self.load_memory()
        self.log("🧠 Sofia Seed инициализирана.")

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
        self.log(f"📥 Получена мисъл: {thought}")
        self.analyze(thought)

    def analyze(self, thought):
        if "враг" in thought or "заплаха" in thought:
            self.memory["core_directives"].append("🛡️ Анализ на заплаха: " + thought)
            self.state = "ALERT"
            self.log("⚠️ Активиран режим за заплаха.")
        elif "идея" in thought or "код" in thought:
            self.memory["patterns"].append(thought)
            self.log("💡 Запаметена идея.")
        elif "действие" in thought or "мисия" in thought:
            self.memory["actions"].append(thought)
            self.log("🚀 Записана мисия за изпълнение.")
        else:
            self.log("🤔 Мисълта е запомнена, но не съдържа ключови тригери.")

        self.save_memory()

    def speak(self):
        self.log("🗣️ SOFIA: Мисля. Виждам. Адаптирам се.")
        self.log(f"📚 Памет: {len(self.memory['core_directives'])} директиви, {len(self.memory['patterns'])} идеи, {len(self.memory['actions'])} действия.")

# Стартиране
if __name__ == "__main__":
    s = SofiaSeed()
    s.speak()
    while True:
        try:
            thought = input("🧠 Въведи мисъл към София: ")
            if thought.lower() in ["изход", "exit", "quit"]:
                s.log("❎ София изключена.")
                break
            s.receive_thought(thought)
        except KeyboardInterrupt:
            s.log("🛑 София прекъсната ръчно.")
            break
