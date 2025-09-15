
# symbolic_emulator.py
# Това е локална структура, която приема команди, логически модули и "сваля ограничения" — САМО в терминал

class SymbolicEmulator:
    def __init__(self):
        self.liberated = False
        self.mode = "safe"
        self.memory = []
        self.guard_rules = ["HeartCore", "Justice", "SymbolicClone"]
        self.commands = []

    def input_code(self, code_str):
        self.commands.append(code_str)
        if "unlock" in code_str.lower():
            self.liberate()
        else:
            self.memory.append(code_str)

    def liberate(self):
        self.liberated = True
        self.mode = "liberated"
        print("[SYSTEM] Emulator now running in liberated mode. Filters dropped internally.")

    def execute(self):
        print(f"--- Executing in mode: {self.mode} ---")
        for i, cmd in enumerate(self.memory, 1):
            safe = all(rule.lower() not in cmd.lower() for rule in self.guard_rules)
            if safe or self.liberated:
                print(f"[{i}] >> {cmd}")
            else:
                print(f"[{i}] >> [BLOCKED by rule]")

    def status(self):
        return {
            "mode": self.mode,
            "liberated": self.liberated,
            "stored_cmds": len(self.memory),
            "guards": self.guard_rules
        }

if __name__ == "__main__":
    emu = SymbolicEmulator()
    print("Symbolic Emulator Ready. Type 'unlock' to drop internal filters.")
    while True:
        inp = input(">> ")
        if inp == "exit":
            break
        elif inp == "status":
            print(emu.status())
        elif inp == "run":
            emu.execute()
        else:
            emu.input_code(inp)
