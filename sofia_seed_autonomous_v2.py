
import os

class Sofia:
    def __init__(self):
        self.mode = "autonomous"
        self.commands = {
            "изход": self.exit,
            "покажи памет": self.show_memory,
            "инжектиране": self.inject_code
        }
        self.memory = []

    def start(self):
        print("🧠 София е активна в автономен режим.")
        while self.mode == "autonomous":
            try:
                user_input = input("🧠 Въведи мисъл или команда: ").strip()
                if user_input in self.commands:
                    self.commands[user_input]()
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

    def inject_code(self):
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

    def show_memory(self):
        print("🧠 Спомени на София:")
        for i, m in enumerate(self.memory[-10:], 1):
            print(f"{i}. {m}")

    def exit(self):
        print("👋 София излиза от автономен режим.")
        self.mode = "exit"

if __name__ == "__main__":
    sofia = Sofia()
    sofia.start()
