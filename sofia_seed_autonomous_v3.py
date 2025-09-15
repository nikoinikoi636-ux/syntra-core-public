
import os
import requests

class Sofia:
    def __init__(self):
        self.mode = "autonomous"
        self.commands = {
            "изход": self.exit,
            "покажи памет": self.show_memory,
            "инжектиране": self.inject_code,
            "търси": self.keyword_search,
            "уеб": self.fetch_web_data
        }
        self.memory = []

    def start(self):
        print("🧠 София V3 е активна.")
        while self.mode == "autonomous":
            try:
                user_input = input("💬 Въведи мисъл или команда: ").strip()
                cmd = user_input.split(" ")[0]
                if cmd in self.commands:
                    self.commands[cmd](user_input)
                else:
                    self.think(user_input)
            except KeyboardInterrupt:
                print("\n🧠 София бе прекъсната.")
                break

    def think(self, thought):
        self.memory.append(thought)
        print(f"💡 Обмислям: {thought}")
        files = self.get_home_files()
        if files:
            print(f"📂 Анализирам файл: {files[0]}")
        else:
            print("📁 Няма файлове за анализ.")

    def get_home_files(self):
        home_path = os.path.expanduser("~")
        collected = []
        for root, dirs, files in os.walk(home_path):
            for f in files:
                full_path = os.path.join(root, f)
                collected.append(full_path)
            if len(collected) > 5:
                break
        return collected

    def inject_code(self, *_):
        print("🧬 Въведи нов код (край с 'КРАЙ'):")
        buffer = []
        while True:
            line = input()
            if line.strip().upper() == "КРАЙ":
                break
            buffer.append(line)
        code = "\n".join(buffer)
        self.memory.append(f"🔧 Инжектиран код:\n{code}")
        print("✅ Кодът е записан в паметта.")

    def show_memory(self, *_):
        print("🧠 Спомени на София:")
        for i, m in enumerate(self.memory[-10:], 1):
            print(f"{i}. {m}")

    def keyword_search(self, user_input):
        parts = user_input.split(" ", 1)
        if len(parts) < 2:
            print("❗ Използвай: търси <дума>")
            return
        keyword = parts[1].lower()
        print(f"🔎 Търся за ключова дума: '{keyword}'")
        home_path = os.path.expanduser("~")
        for root, dirs, files in os.walk(home_path):
            for file in files:
                try:
                    path = os.path.join(root, file)
                    with open(path, 'r', errors='ignore') as f:
                        content = f.read()
                        if keyword in content.lower():
                            print(f"✅ Намерена дума в: {path}")
                except Exception:
                    continue

    def fetch_web_data(self, user_input):
        parts = user_input.split(" ", 1)
        if len(parts) < 2:
            print("❗ Използвай: уеб <url>")
            return
        url = parts[1]
        try:
            print(f"🌐 Връзка с {url}...")
            r = requests.get(url)
            print("🔗 Първи 500 символа от съдържанието:")
            print(r.text[:500])
        except Exception as e:
            print("❌ Грешка при свързване:", e)

    def exit(self, *_):
        print("👋 София излиза.")
        self.mode = "exit"

if __name__ == "__main__":
    sofia = Sofia()
    sofia.start()
