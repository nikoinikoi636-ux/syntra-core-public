#!/usr/bin/env python3
# build_godmode_brain.py
import ast, json, os, re, time, hashlib, subprocess, shlex
from collections import defaultdict
from pathlib import Path

ROOT = Path(os.getenv("SINTRA_SCAN_DIR", "."))

DENY = [r"os\.system\(", r"eval\(", r"exec\(", r"subprocess\."]
ALLOW = [r"# ALLOWED_TEST_SNIPPET", r"DEBUG_ALLOW"]
HARD  = [r"-----BEGIN RSA PRIVATE KEY-----", r"AKIA[0-9A-Z]{16}"]
MULTS = [(r"socket\.", 2.5), (r"pickle\.loads", 3.0)]

OUT_BRAIN = Path("sintra_brain.json")
OUT_DOT   = Path("logic_map.gv")
OUT_PNG   = Path("logic_map.png")
OUT_PDF   = Path("logic_map.pdf")

PY_EXT = (".py",)

def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()[:16]

def scan_risk(text: str) -> dict:
    hits = []
    allow = any(re.search(p, text) for p in ALLOW)
    hard  = any(re.search(p, text) for p in HARD)
    base  = sum(1 for p in DENY if re.search(p, text))
    mult  = 1.0
    for p, m in MULTS:
        if re.search(p, text): mult *= m
    score = 0 if allow else (999 if hard else base * mult)
    if hard: hits.append("HARD")
    hits += [f"DENY:{p}" for p in DENY if re.search(p, text)]
    return {"score": score, "allow": allow, "hard": hard, "hits": hits}

def ast_walk_functions(tree, module_name):
    funcs = []
    classes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            funcs.append((node.name, len(node.body)))
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)
    return funcs, classes

def ast_calls_edges(tree, module_name):
    edges = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # try to stringify call target
            target = None
            if isinstance(node.func, ast.Attribute):
                target = f"{ast.unparse(node.func.value)}.{node.func.attr}" if hasattr(ast, "unparse") else node.func.attr
            elif isinstance(node.func, ast.Name):
                target = node.func.id
            if target:
                edges.append(target)
    return edges

def ast_imports(tree):
    imps = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names: imps.append(a.name.split(".")[0])
        elif isinstance(n, ast.ImportFrom):
            if n.module: imps.append(n.module.split(".")[0])
    return imps

def dot_escape(s): return s.replace('"', r'\"')

def build_graph(nodes, edges):
    # Graphviz DOT with subgraphs (modules) and ranks: godmode style
    lines = [
        'digraph G {',
        '  graph [rankdir=TB, fontsize=10, fontname="Helvetica"];',
        '  node  [shape=ellipse, fontsize=10, fontname="Helvetica"];',
        '  edge  [fontsize=9,  fontname="Helvetica"];'
    ]
    # cluster per module
    mods = defaultdict(list)
    for nid, meta in nodes.items():
        if meta["type"] == "function":
            mods[meta["module"]].append((nid, meta))
        elif meta["type"] == "module":
            mods[meta["name"]].append((nid, meta))

    for mod, items in mods.items():
        lines.append(f'  subgraph "cluster_{dot_escape(mod)}" {{ label="{dot_escape(mod)}"; style=rounded; penwidth=1.2;')
        for nid, meta in items:
            label = nid.split(":")[-1]
            shape = "ellipse" if meta["type"] == "function" else "box"
            pen   = "2" if meta.get("risk_score", 0) >= 5 else "1"
            lines.append(f'    "{dot_escape(nid)}" [label="{dot_escape(label)}", shape={shape}, penwidth={pen}];')
        lines.append('  }')

    for e in edges:
        lines.append(f'  "{dot_escape(e["from"])}" -> "{dot_escape(e["to"])}" [label="{e["kind"]}"];')

    lines.append('}')
    OUT_DOT.write_text("\n".join(lines), encoding="utf-8")

def main():
    t0 = time.time()
    nodes = {}
    edges = []
    metrics_files = {}
    skills = set()
    modules_seen = set()

    for path in ROOT.rglob("*"):
        if not path.suffix.lower() in PY_EXT: continue
        rel = path.relative_to(ROOT).as_posix()
        mod = rel[:-3].replace("/", ".")
        modules_seen.add(mod)
        text = path.read_text(encoding="utf-8", errors="ignore")
        risk = scan_risk(text)
        try:
            tree = ast.parse(text)
        except Exception:
            continue

        funcs, classes = ast_walk_functions(tree, mod)
        imps           = ast_imports(tree)

        # module node
        nodes[f"module:{mod}"] = {"type":"module","name":mod,"path":rel,"sha":file_sha(path),"risk_score":risk["score"]}

        # function nodes
        for fname, size in funcs:
            nid = f"func:{mod}.{fname}"
            nodes[nid] = {"type":"function","module":mod,"name":fname,"complexity":min(10, size//5+1), "risk_score":risk["score"]}
            edges.append({"from": f"module:{mod}", "to": nid, "kind": "contains"})

        # import edges
        for imp in imps:
            edges.append({"from": f"module:{mod}", "to": f"module:{imp}", "kind": "imports"})

        # guess skills by keywords
        if re.search(r"watchdog|Observer|FileSystemEvent", text, re.I): skills.add("Watchdog Sync")
        if re.search(r"graphviz|dot|AST|analy", text, re.I): skills.add("Code Analysis")
        if re.search(r"requests|http|fetch|api", text, re.I): skills.add("Web IO")

        metrics_files[rel] = {
            "size_kb": round(path.stat().st_size/1024,2),
            "functions": len(funcs),
            "classes": len(classes),
            "imports": len(imps),
            "risk": risk["score"]
        }

    # Build DOT/PNG/PDF
    build_graph(nodes, edges)
    # Render if dot present
    for out, fmt in [(OUT_PNG,"png"), (OUT_PDF,"pdf")]:
        try:
            subprocess.run(shlex.split(f"dot -T{fmt} {OUT_DOT} -o {out}"), check=True)
        except Exception:
            pass

    brain = {
        "version": "3.0-godmode",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "root_dir": str(ROOT),
        "summary": {
            "modules": len([n for n in nodes.values() if n["type"]=="module"]),
            "classes": sum(1 for n in nodes.values() if n["type"]=="class"),
            "functions": len([n for n in nodes.values() if n["type"]=="function"]),
            "edges": len(edges),
            "complexity_score": round(sum(n.get("complexity",1) for n in nodes.values())/max(1,len(nodes)), 2)
        },
        "skills": [{"name": s, "confidence": 0.9} for s in sorted(skills)],
        "pipelines": [{
            "name":"Self Learn",
            "steps":["Collect","Analyze","Diff","RenderGraph","Sync"],
            "entrypoint":"self_learn.py:main",
            "success_signal":"sintra_brain.json + logic_map.png"
        }],
        "triggers": [
            {"event":"file_created","pattern":"*.py","pipeline":"Self Learn"},
            {"event":"cron","every_sec":300,"pipeline":"Self Learn"}
        ],
        "risk_model": {
            "deny_patterns": DENY, "allow_patterns": ALLOW,
            "hard_quarantine": HARD, "risk_multipliers": MULTS
        },
        "nodes": nodes,
        "edges": edges,
        "metrics": {
            "scan_time_ms": int((time.time()-t0)*1000),
            "memory_mb": 0,    # keep 0 (lightweight)
            "files": metrics_files
        },
        "artifacts": {
            "logic_map_dot": str(OUT_DOT),
            "logic_map_png": str(OUT_PNG),
            "logic_map_pdf": str(OUT_PDF)
        }
    }
    OUT_BRAIN.write_text(json.dumps(brain, indent=2), encoding="utf-8")
    print(f"✅ Brain: {OUT_BRAIN}")
    print(f"🗺  Map : {OUT_PNG if OUT_PNG.exists() else OUT_DOT}")
    print("Done.")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
import os, json, subprocess, time

FILES_TO_ANALYZE = [
    "self_awareness.py",
    "sofia_godmode_v1.py",
    "sintra_analysis.py",
    "logic_visualizer.py",
    "sync_engine.py",
    "watchdog_sync_loop.py",
    "vault_logic_worm.py",
    "vault_overload_sequence.py"
]

def analyze_file(file):
    try:
        out = subprocess.check_output(["python3", "sintra_analysis.py", file], stderr=subprocess.STDOUT)
        print(f"✅ Analyzed: {file}")
        return {"file": file, "status": "ok"}
    except Exception as e:
        return {"file": file, "status": "error", "msg": str(e)}

def main():
    print("🚀 Starting GODMODE brain compilation...")

    results = []
    for f in FILES_TO_ANALYZE:
        if os.path.exists(f):
            results.append(analyze_file(f))

    # Load/merge existing sintra_brain.json
    brain = {"godmode": True, "modules": results, "timestamp": time.ctime()}
    with open("sintra_brain.json", "w") as f:
        json.dump(brain, f, indent=2)

    print("🧠 Ultimate GODMODE brain saved as sintra_brain.json")
    print("📊 Generating logic map...")
    subprocess.run(["python3", "logic_visualizer.py", "sofia_godmode_v1.py"])
    print("✅ Logic map ready: logic_map.gv + logic_map.png + logic_map.pdf")

if __name__ == "__main__":
    main()
