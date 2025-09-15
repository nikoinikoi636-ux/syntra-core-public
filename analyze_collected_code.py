#!/usr/bin/env python3
"""
Fallback analyzer for watchdog_sync_loop.py

Provides analyze_codebase(root) and returns a simple summary
without external deps. Safe for Termux; handles large trees.
"""
from __future__ import annotations
from pathlib import Path
import json, re

PY_PAT = re.compile(r"\.py$", re.I)

def analyze_codebase(root: str | None = None) -> dict:
    base = Path(root or ".").resolve()
    files, py_files, lines = 0, 0, 0
    top = []
    for p in base.rglob("*"):
        if p.is_file():
            files += 1
            if PY_PAT.search(p.name):
                py_files += 1
                try:
                    with p.open("r", encoding="utf-8", errors="ignore") as f:
                        cnt = sum(1 for _ in f)
                    lines += cnt
                    top.append((cnt, str(p.relative_to(base))))
                except Exception:
                    pass
    top.sort(reverse=True)
    return {
        "root": str(base),
        "files_total": files,
        "py_files": py_files,
        "total_py_lines": lines,
        "top_py_by_lines": top[:10],
        "ok": True,
    }

if __name__ == "__main__":
    print(json.dumps(analyze_codebase("."), ensure_ascii=False, indent=2))
