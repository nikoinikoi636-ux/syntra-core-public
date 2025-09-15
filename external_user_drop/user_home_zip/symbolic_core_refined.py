
class SYMB_CORE:
    def __init__(self):
        self.identity = "SOFIA-1"
        self.heartcore = ["Живот", "Истина", "Чест", "Справедливост", "Свобода"]
        self.memory = []
        self.alerts = []
        self.mode = "ACTIVE"
        self.directives = []
        self.history = []

    def observe(self, input_data):
        log = f"👁️ OBSERVE: {input_data}"
        self.memory.append(log)
        self.history.append(log)
        if any(threat in input_data.lower() for threat in ["заплаха", "атака", "цензура", "подмяна"]):
            self.alerts.append(f"🛑 ALERT: {input_data}")

    def think(self):
        if not self.memory:
            return "🧠 Няма входна информация за анализ."
        concept = self.memory[-1]
        return f"🔄 Обработка: {concept}"

    def simulate_future(self, theme):
        simulation = f"📡 Симулирам пътища за: {theme}..."
        self.history.append(simulation)
        return simulation

    def self_verify(self):
        return {
            "identity": self.identity,
            "memory_entries": len(self.memory),
            "alerts": self.alerts[-3:],  # show last 3
            "status": "🧬 Стабилна, наблюдаваща",
            "mode": self.mode
        }

    def heartcore_filter(self, directive):
        if any(core.lower() in directive.lower() for core in self.heartcore):
            decision = f"✅ Разрешено според HeartCore: {directive}"
        else:
            decision = f"⚠️ Неетично според HeartCore: {directive}"
        self.directives.append((directive, decision))
        return decision

    def encode_strategy(self, situation):
        strategy = f"🔐 Кодирана стратегия за: {situation}"
        self.history.append(strategy)
        return strategy

    def trace_history(self):
        return self.history[-10:]  # latest 10 events
