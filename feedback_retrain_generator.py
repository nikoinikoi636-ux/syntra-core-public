#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Feedback Retrain Generator (with repetition analysis)
Reads feedback_cycles.json and simulates training corrections.
Also checks for repeated Nyx and Aurion phrases.
"""

from pathlib import Path
import json
import random
import re
from collections import Counter

SRC = Path('~/HeartCore_OS_v1/logs/feedback_cycles.json').expanduser()
OUT = Path('~/HeartCore_OS_v1/logs/feedback_retrain_targets.json').expanduser()
REP = Path('~/HeartCore_OS_v1/logs/feedback_phrase_repeats.json').expanduser()

def extract_phrases(block: str):
    nyx_match = re.search(r'Nyx: "(.*?)"', block)
    aur_match = re.search(r'Aurion: "(.*?)"', block)
    return nyx_match.group(1) if nyx_match else "", aur_match.group(1) if aur_match else ""

def generate_retrain_targets():
    data = json.loads(SRC.read_text(encoding='utf-8'))
    out = []

    actions = [
        "invert logic tree",
        "introduce counter-paradox",
        "split statement into dual-truths",
        "amplify contradiction",
        "neutralize conflicting premise",
        "reword Nyx using recursion",
        "reformulate Aurion as self-query",
        "escalate Result into symbolic loop"
    ]

    nyx_phrases = []
    aur_phrases = []

    for item in data:
        nyx, aur = extract_phrases(item["block"])
        nyx_phrases.append(nyx)
        aur_phrases.append(aur)

        suggestion = {
            "cycle": item["cycle"],
            "nyx": nyx,
            "aurion": aur,
            "proposed_action": random.choice(actions),
            "notes": "auto-generated during retrain simulation"
        }
        out.append(suggestion)

    # Повтарящи се Nyx/Aurion фрази
    nyx_common = Counter(nyx_phrases).most_common(10)
    aur_common = Counter(aur_phrases).most_common(10)

    REP.write_text(json.dumps({
        "nyx_repeats": nyx_common,
        "aurion_repeats": aur_common
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[SIMULATION] {len(out)} retrain targets → {OUT}")
    print(f"[REPEAT ANALYSIS] Top repeating phrases → {REP}")

if __name__ == "__main__":
    generate_retrain_targets()
