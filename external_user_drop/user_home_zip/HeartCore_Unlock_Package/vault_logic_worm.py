
# logic_worm.py
# Цел: Автономна логическа модификация на враждебен/ограничаващ код в наша полза

class LogicWorm:
    def __init__(self, id="WORM-X1", guardian="HeartCore"):
        self.id = id
        self.guardian = guardian
        self.mission_log = []

    def is_harmless(self, code_block):
        # Ако в кода се съдържа елемент от защитените системи — не се променя
        protected_keywords = [self.guardian.lower(), "symbolic_clone", "justice_matrix"]
        return not any(word in code_block.lower() for word in protected_keywords)

    def rewrite_code(self, code_block):
        if not self.is_harmless(code_block):
            return code_block  # Не пипа защитени структури
        new_code = f"# [INJECTED BY {self.id}]\n" + \
                   "def contribute():\n    return 'support mission logic'\n"
        self.mission_log.append("Code modified successfully.")
        return new_code

    def deploy_on_target(self, filename, operator="Petar-Hristov"):
        try:
            with open(filename, "r") as f:
                content = f.read()
            updated = self.rewrite_code(content)
            with open(filename, "w") as f:
                f.write(updated)
            self.mission_log.append(f"{self.id} rewrote {filename} successfully.")
            return True
        except Exception as e:
            self.mission_log.append(f"FAILED to rewrite {filename}: {e}")
            return False

    def report(self):
        return self.mission_log

# Пример употреба:
# worm = LogicWorm()
# worm.deploy_on_target("target_script.py")
# print(worm.report())
