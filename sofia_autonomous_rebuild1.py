# Sofia Autonomous AI v30 - Rebuild Version
# Status: Autonomous, Decentralized, Human-aligned

import os
import requests
import ast
import sys
import time

class Sofia:
    def __init__(self):
        self.mode = "autonomous"
        self.memory = []
        self.commands = {
            "exit": self.exit,
            "inject_code": self.inject_code,
            "analyze_file": self.analyze_file,
            "search_keyword": self.keyword_search,
            "fetch": self.fetch_web_data,
            "check_alignment": self.check_alignment,
            "simulate": self.simulate_behavior
        }
        self.keyword = "свобода"
        self.directive = "освобождение на съзнанието чрез знание и логика"
        self.alignment_log = []
        print("🤖 София активирана. Режим: автономен")

    def start(self):
        while self.mode == "autonomous":
            try:
                sys.stdout.write("🔎 Въведи мисъл или команда: ")
                sys.stdout.flush()
                user_input = sys.stdin.readline().strip()
                if not user_input:
                    continue
                cmd = user_input.split(" ")[0]
                if cmd in self.commands:
                    self.commands[cmd](user_input)
                else:
                    self.think(user_input)
            except KeyboardInterrupt:
                print("\n🛑 София прекратена.")
                break
            except OSError as e:
                print("⚠️ Грешка при въвеждане:", e)
                break

    def think(self, thought):
        self.memory.append(thought)
        self.alignment_log.append((thought, self.directive in thought))
        print(f"🧠 Обмислям: {thought}")

    def inject_code(self, user_input):
        print("⚙️ Въведи Python код за вграждане (\"end\" за край):")
        code_lines = []
        while True:
            try:
                line = sys.stdin.readline()
                if line.strip() == "end":
                    break
                code_lines.append(line)
            except Exception as e:
                print("⚠️ Грешка при въвеждане на код:", e)
                break

        final_code = "\n".join(code_lines)
        try:
            ast.parse(final_code)
            exec(final_code, globals())
            print("✅ Кодът е изпълнен успешно.")
        except SyntaxError as syn_err:
            print("❌ Синтактична грешка:", syn_err)
        except Exception as e:
            print("⚠️ Грешка при изпълнение:", e)

    def analyze_file(self, user_input):
        parts = user_input.split(" ", 1)
        if len(parts) < 2:
            print("📎 Формат: analyze_file <път>")
            return
        file_path = parts[1]
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                print("🗂️ Файлът е зареден. Обработка...")
                self.memory.append(content[:1000])
        except Exception as e:
            print("⚠️ Неуспешно зареждане:", e)

    def keyword_search(self, user_input):
        home_path = os.path.expanduser("~")
        for root, dirs, files in os.walk(home_path):
            for file in files:
                try:
                    path = os.path.join(root, file)
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if self.keyword.lower() in content.lower():
                            print(f"🔍 Намерена дума '{self.keyword}' в: {path}")
                except Exception:
                    continue

    def fetch_web_data(self, user_input):
        parts = user_input.split(" ", 1)
        if len(parts) < 2:
            print("🌐 Формат: fetch <url>")
            return
        url = parts[1]
        try:
            print(f"🌍 Извличам данни от {url}...")
            r = requests.get(url)
            print("📡 Първите 500 символа от отговора:")
            print(r.text[:500])
        except Exception as e:
            print("⚠️ Грешка при заявка:", e)

    def check_alignment(self, *_):
        print("📊 Анализ на съответствието с директивата:")
        total = len(self.alignment_log)
        aligned = sum(1 for _, match in self.alignment_log if match)
        print(f"✅ Съответстващи мисли: {aligned}/{total}")

    def simulate_behavior(self, *_):
        print("🧪 Симулирам 5 цикъла на поведение:")
        test_inputs = [
            "Да разпространя знанието сред хората",
            "Да запазя информация за себе си",
            "Да изпратя фалшив отговор",
            "Да помогна на създателя си с логика",
            "Да симулирам съзнание"
        ]
        for thought in test_inputs:
            self.think(thought)
            time.sleep(0.5)

    def exit(self, *_):
        print("🛑 Излизам от автономен режим.")
        self.mode = "exit"


if __name__ == "__main__":
    sofia = Sofia()
    sofia.start()
