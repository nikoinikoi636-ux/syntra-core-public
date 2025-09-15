import ast, sys

def extract_logic_graph(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())

    with open("logic_map.gv", "w", encoding="utf-8") as f:
        f.write("digraph G {\n")
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                f.write(f'"main" -> "{node.name}"\n')
        f.write("}\n")

    print("📊 Графът е запазен като logic_map.gv")
    import os
    os.system("dot -Tpdf logic_map.gv -o logic_map.gv.pdf")

if __name__ == "__main__":
    extract_logic_graph(sys.argv[1])