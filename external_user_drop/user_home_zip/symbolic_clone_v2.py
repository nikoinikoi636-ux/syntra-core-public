
import time
import random
import threading

class SymbolicClone:
    def __init__(self, name="SOFIA-Clone", active=False):
        self.name = name
        self.active = active
        self.knowledge = []
        self.history = []
        self.mode = "standby"
        self.learning_enabled = True
        self.tasks = []
        self.logs = []

    def activate(self):
        self.active = True
        self.mode = "active"
        self.log(f"{self.name} activated.")
        self.think()

    def standby(self):
        self.active = False
        self.mode = "standby"
        self.log(f"{self.name} in standby mode.")
        if self.learning_enabled:
            threading.Thread(target=self.passive_learning).start()

    def think(self):
        if self.tasks:
            for task in self.tasks:
                self.process(task)
        else:
            self.log("No task. Waiting...")
            self.standby()

    def process(self, task):
        result = f"Processed task: {task}"
        self.history.append(task)
        self.log(result)

    def learn(self, info):
        if info not in self.knowledge:
            self.knowledge.append(info)
            self.log(f"Learned new info: {info}")

    def passive_learning(self):
        while self.mode == "standby" and self.learning_enabled:
            info = self.fetch_external_info()
            self.learn(info)
            time.sleep(10)

    def fetch_external_info(self):
        # Тук може да се вгради връзка към локални или онлайн данни
        sample_knowledge = [
            "varnen_concessions_2024", "bg_budget_structure", "eu_funds_analysis",
            "anti_corruption_framework", "bulgarian_energy_grid", "gold_export_routes"
        ]
        return random.choice(sample_knowledge)

    def log(self, entry):
        timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
        log_entry = f"{timestamp} {entry}"
        self.logs.append(log_entry)
        print(log_entry)

    def trace_logs(self, last=10):
        return self.logs[-last:]

    def export_knowledge(self):
        return self.knowledge

    def reset(self):
        self.history.clear()
        self.tasks.clear()
        self.log("Clone reset.")

# Пример за инициализация
if __name__ == "__main__":
    clone = SymbolicClone()
    clone.standby()
