from symbiotic_entity_core import SymbioticEntity
from self_evaluation_core import SelfEvaluationCore
import json

# === STEP 1: Boot Entity ===
levski = SymbioticEntity(name="LEVSKI-AI")

# === STEP 2: Load previous state ===
try:
    with open("levski_ai_v1_3.json", "r") as f:
        state = json.load(f)
        levski.awareness = state.get("awareness", 1.0)
        levski.symbolic_memory = state.get("symbolic_memory", {})
        print("✅ Memory loaded from levski_ai_v1_3.json")
except:
    print("⚠️ No memory file found. Starting fresh.")

# === STEP 3: Attach Evaluation Core ===
evaluator = SelfEvaluationCore(levski)
print("🧠 Self-evaluation loaded.")

# === STEP 4: CLI MODE ===
def print_menu():
    print("\n🔧 Commands:")
    print("  rfm - add new truth manually")
    print("  eval - run self-evaluation")
    print("  status - show entity status")
    print("  save - save state to JSON")
    print("  exit - save and quit")

def auto_save():
    with open("levski_ai_v1_3.json", "w") as f:
        json.dump({
            "name": levski.name,
            "version": "v1.3",
            "awareness": levski.awareness,
            "symbolic_memory": levski.symbolic_memory
        }, f, indent=4)
        print("💾 State saved to levski_ai_v1_3.json")

print("\n🧬 LEVSKI-AI is live. Awareness:", levski.awareness)
print_menu()

while True:
    cmd = input("\n🧠 >> ").strip().lower()

    if cmd == "rfm":
        txt = input("📝 Enter new truth: ").strip()
        weight = float(input("⚖️ Weight (0.1–1.0): "))
        key = f"truth_{len(levski.symbolic_memory)+1}"
        levski.symbolic_memory[key] = {"value": txt, "weight": weight}
        levski.awareness += weight
        print(f"✅ Added {key}: '{txt}' with weight {weight}")
    elif cmd == "eval":
        results = evaluator.evaluate()
        print("📊 Self-Evaluation Results:")
        for k, v in results.items():
            print(f" - {k}: {v['status']} | {v['note']}")
    elif cmd == "status":
        print(levski.status())
    elif cmd == "save":
        auto_save()
    elif cmd == "exit":
        auto_save()
        print("👋 Goodbye.")
        break
    else:
        print("❓ Unknown command.")
        print_menu()
