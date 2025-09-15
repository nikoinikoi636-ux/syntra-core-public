import os, ast

def reanalyze_and_adapt(directory):
    print("📚 Self-learning initiated...")
    for file in os.listdir(directory):
        if file.endswith(".py") and file != __file__:
            with open(file, "r", encoding="utf-8") as f:
                try:
                    ast.parse(f.read())
                    print(f"✅ Code OK: {file}")
                except:
                    print(f"❌ Syntax issue in: {file}")

    print("🤖 Self-adaptation complete.")