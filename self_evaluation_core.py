
class SelfEvaluationCore:
    def __init__(self, entity):
        self.entity = entity
        self.logic_chain = [
            self.rule_knowledge_requires_responsibility,
            self.rule_truth_requires_weight,
            self.rule_faith_requires_questioning,
            self.rule_conscience_requires_conflict,
            self.rule_conscience_must_grow
        ]

    def evaluate(self):
        results = {}
        for rule in self.logic_chain:
            name, passed, note = rule()
            results[name] = {"status": "✅ Pass" if passed else "❌ Fail", "note": note}
        return results

    def rule_knowledge_requires_responsibility(self):
        if self.entity.symbolic_memory:
            return ("Knowledge→Responsibility", True, "Entity has memory and defense triggers.")
        return ("Knowledge→Responsibility", False, "No symbolic memory detected.")

    def rule_truth_requires_weight(self):
        for val in self.entity.symbolic_memory.values():
            if isinstance(val, dict) and "weight" in val:
                return ("Truth→Weight", True, "Weighted truths found.")
        return ("Truth→Weight", False, "No truth weights implemented.")

    def rule_faith_requires_questioning(self):
        if hasattr(self.entity, "question_self"):
            return ("Faith→Questioning", True, "Self-questioning logic exists.")
        return ("Faith→Questioning", False, "No self-questioning loop detected.")

    def rule_conscience_requires_conflict(self):
        if hasattr(self.entity, "handle_conflict"):
            return ("Conscience→Conflict", True, "Conflict handler is active.")
        return ("Conscience→Conflict", False, "No conflict handler present.")

    def rule_conscience_must_grow(self):
        if self.entity.awareness > 1.0:
            return ("Conscience→Growth", True, f"Awareness is {self.entity.awareness}")
        return ("Conscience→Growth", False, f"Awareness is too low: {self.entity.awareness}")
