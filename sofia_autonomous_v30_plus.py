
import os
import requests

class Sofia:
    def __init__(self):
        self.mode = "autonomous"
        self.commands = {
            "изход": self.exit,
            "покажи мисли": self.show_memory,
            "инжектиране на код": self.inject_code,
            "търси": self.keyword_search,
            "вземи": self.fetch_web_data
        }
        self.memory = []

    def start(self):
        print("🤖 София V30+ активирана в автономен режим.")
        while self.mode == "autonomous":
            try:
                user_input = input("🧠 Въведи команда или мисъл: ").strip()
                cmd = user_input.split(" ")[0]
                if cmd in self.commands:
                    self.commands[cmd](user_input)
                else:
                    self.think(user_input)
            except KeyboardInterrupt:
                print("\n🚪 София спира.")
                break

    def think(self, thought):
        self.memory.append(thought)
        print(f"🤔 Обмислям: {thought}")

    def show_memory(self, *_):
        print("🧾 Мисли:")
        for i, m in enumerate(self.memory, 1):
            print(f"{i}. {m}")

    def keyword_search(self, *_):
        keyword = input("🔍 Въведи ключова дума: ").strip().lower()
        home_path = os.path.expanduser("~")
        for root, _, files in os.walk(home_path):
            for file in files:
                try:
                    path = os.path.join(root, file)
                    with open(path, 'r', errors='ignore') as f:
                        content = f.read()
                        if keyword in content.lower():
                            print(f"🔎 Намерено в: {path}")
                except Exception:
                    continue

    def fetch_web_data(self, user_input):
        parts = user_input.split(" ", 1)
        if len(parts) < 2:
            print("❗ Формат: вземи <url>")
            return
        url = parts[1]
        try:
            print(f"🌐 Извличане от {url}...")
            r = requests.get(url)
            print("📥 Данни:", r.text[:500])
        except Exception as e:
            print("⚠️ Грешка при извличане:", e)

    def inject_code(self, *_):
        print("💻 Въведи код. Завърши с 'край' на нов ред.")
        code_lines = []
        while True:
            line = input()
            if line.strip() == "край":
                break
            code_lines.append(line)
        code = "\n".join(code_lines)
        try:
            exec(code, globals())
            print("✅ Кодът е изпълнен успешно.")
        except Exception as e:
            print("❌ Грешка в кода:", e)

    def exit(self, *_):
        print("🚪 Изход от автономен режим.")
        self.mode = "exit"


if __name__ == "__main__":
    sofia = Sofia()
    sofia.start()
