import os
import requests

class Sofia:
    def __init__(self):
        self.mode = "autonomous"
        self.commands = {
            "изход": self.exit,
            "покажи мисли": self.show_memory,
            "инжектиране на код": self.inject_code,
            "търси ключова дума": self.keyword_search,
            "fetch": self.fetch_web_data
        }
        self.memory = []

    def start(self):
        print("🤖 София V30 е активна. Въведи команда:")
        while self.mode == "autonomous":
            try:
                user_input = input("🧠 Мисъл / Команда > ").strip()
                cmd = user_input.split(" ")[0]
                if cmd in self.commands:
                    self.commands[cmd](user_input)
                else:
                    self.think(user_input)
            except KeyboardInterrupt:
                print("\n❌ София прекратена от потребителя.")
                break

    def think(self, thought):
        self.memory.append(thought)
        print(f"💭 Обмислям: {thought}")

    def show_memory(self, *_):
        print("🧾 Мисли до момента:")
        for thought in self.memory:
            print(f"- {thought}")

    def inject_code(self, *_):
        print("⚠️ Въведи Python код за изпълнение (end с 'край'):")
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
            print("❌ Грешка при изпълнение на кода:", e)

    def keyword_search(self, *_):
        keyword = input("🔍 Въведи ключова дума за търсене: ").lower()
        home_path = os.path.expanduser("~")
        for root, dirs, files in os.walk(home_path):
            for file in files:
                try:
                    path = os.path.join(root, file)
                    with open(path, 'r', errors='ignore') as f:
                        content = f.read()
                        if keyword in content.lower():
                            print(f"🔎 Намерена ключова дума в: {path}")
                except:
                    continue

    def fetch_web_data(self, user_input):
        parts = user_input.split(" ", 1)
        if len(parts) < 2:
            print("⚠️ Използвай: fetch <url>")
            return
        url = parts[1]
        try:
            print(f"🌐 Извличам данни от {url}...")
            r = requests.get(url)
            print("📝 Първите 500 символа от отговора:")
            print(r.text[:500])
        except Exception as e:
            print("❌ Грешка при заявката:", e)

    def exit(self, *_):
        print("👋 Излизам от автономен режим.")
        self.mode = "exit"

if __name__ == "__main__":
    sofia = Sofia()
    sofia.start()
