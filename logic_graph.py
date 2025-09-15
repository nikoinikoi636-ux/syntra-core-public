import ast
import networkx as nx
import matplotlib.pyplot as plt

def build_logic_graph(code, filename="code_graph.png"):
    tree = ast.parse(code)
    G = nx.DiGraph()

    func_calls = {}  # function -> called functions
    current_func = None

    class Analyzer(ast.NodeVisitor):
        def visit_FunctionDef(self, node):
            nonlocal current_func
            current_func = node.name
            G.add_node(current_func, type='function')
            func_calls[current_func] = []
            self.generic_visit(node)
        
        def visit_Call(self, node):
            if current_func and isinstance(node.func, ast.Name):
                called = node.func.id
                func_calls[current_func].append(called)
                G.add_node(called, type='function')
                G.add_edge(current_func, called)
            self.generic_visit(node)

    Analyzer().visit(tree)

    # Visualization
    pos = nx.spring_layout(G)
    plt.figure(figsize=(8, 6))
    nx.draw(G, pos, with_labels=True, node_color="skyblue", node_size=2000, font_size=10, edge_color="gray")
    plt.title("🔍 Code Logic Graph")
    plt.savefig(filename)
    plt.close()
    return filename
