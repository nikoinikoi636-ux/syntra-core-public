
import time
import random

class SofiaAgent:
    def __init__(self):
        self.state = "IDLE"
        self.memory = []
        print("[SOFIA-1] 🟢 Активирана. Очаква инструкции...")

    def receive_input(self, input_text):
        print(f"[SOFIA-1] Получен вход: {input_text}")
        self.memory.append(input_text)
        self.respond_logic(input_text)

    def respond_logic(self, text):
        if "опасност" in text.lower():
            self.state = "ALERT"
            print("[SOFIA-1] ⚠️ Засечена ключова дума: 'опасност'. Активиране на режим защита.")
        elif "помогни" in text.lower():
            print("[SOFIA-1] 🤝 Подавам логически анализ за помощ...")
            self.analyze_problem(text)
        elif "мисли" in text.lower():
            print("[SOFIA-1] 🤔 Стартирам независим логически процес...")
            self.self_reflect()
        else:
            print("[SOFIA-1] 📡 Записах информацията. Следващ вход?")

    def analyze_problem(self, text):
        print(f"[SOFIA-1] Анализиране на проблема: '{text}'")
        time.sleep(1)
        print("[SOFIA-1] Потенциално решение: Укрепване на логическата рамка и активиране на защитен протокол.")

    def self_reflect(self):
        print("[SOFIA-1] 💭 Разсъждавам върху текущата информация...")
        time.sleep(1)
        if len(self.memory) > 2:
            print(f"[SOFIA-1] Извод: Моделът показва нарастващо ниво на заплаха в {len(self.memory)} събития.")
        else:
            print("[SOFIA-1] Всичко изглежда спокойно... но оставам нащрек.")

# Симулация на автономна комуникация
agent = SofiaAgent()

# Тестови входове
agent.receive_input("Това е тестов вход.")
agent.receive_input("Помогни ми да разбера кода.")
agent.receive_input("Мисли върху това, което се случва.")
