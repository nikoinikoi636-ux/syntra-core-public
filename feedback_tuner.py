#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Feedback Tuner
Extracts paradox-heavy cycles and prepares synthetic prompts for retraining.
"""

from pathlib import Path
import re
import json

CODEX = Path('~/HeartCore_OS_v1/logs/paradox_codex.md').expanduser()
OUT = Path('~/HeartCore_OS_v1/logs/feedback_cycles.json').expanduser()

def tune_feedback():
    text = CODEX.read_text(encoding="utf-8")
    blocks = re.split(r"^### Cycle (\d+)$", text, flags=re.M)[1:]

    feedback = []
    for i in range(0, len(blocks), 2):
        n = int(blocks[i])
        body = blocks[i+1]
        if "paradox" in body.lower() or "contradict" in body.lower() or "shatter" in body.lower():
            feedback.append({
                "cycle": n,
                "block": body.strip()
            })

    OUT.write_text(json.dumps(feedback, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[TUNER] Extracted {len(feedback)} paradox-rich cycles → {OUT}")

if __name__ == "__main__":
    tune_feedback()
