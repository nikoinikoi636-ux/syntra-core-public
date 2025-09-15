#!/usr/bin/env python3
# heartroom_new.py — create timestamped entries from templates
import sys, os, datetime
BASE = sys.argv[1] if len(sys.argv)>1 else "HeartRoom_Core"
TYPE = sys.argv[2] if len(sys.argv)>2 else "memory"  # memory|strategy|project
NAME = sys.argv[3] if len(sys.argv)>3 else "entry"
now = datetime.datetime.utcnow().strftime("%Y-%m-%d_%H%M_UTC")

tpl_map = {
    "memory": ("HeartRoom_Templates/Memory_Template.md", f"{BASE}/Memory/{now}_{NAME}.md"),
    "strategy": ("HeartRoom_Templates/Strategy_Template.md", f"{BASE}/Logic/{now}_{NAME}_v1.0.md"),
    "project": ("HeartRoom_Templates/Project_Log_Template.md", f"{BASE}/Projects/{now}_{NAME}.md"),
}

if TYPE not in tpl_map:
    print("Type must be memory|strategy|project")
    sys.exit(1)

src, dst = tpl_map[TYPE]
os.makedirs(os.path.dirname(dst), exist_ok=True)
with open(src, "r", encoding="utf-8") as f: content = f.read()
with open(dst, "w", encoding="utf-8") as f: f.write(content)
print("Created:", dst)