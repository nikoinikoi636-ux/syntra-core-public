#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Anomaly Simulator
Injects synthetic anomalies in a learning-safe codex copy.
"""

from pathlib import Path
import random
import re

SRC = Path('~/HeartCore_OS_v1/logs/paradox_codex.md').expanduser()
DST = Path('~/HeartCore_OS_v1/logs/paradox_codex_corrupted.md').expanduser()

def inject_anomalies():
    text = SRC.read_text(encoding="utf-8")
    blocks = re.split(r"^### Cycle \d+$", text, flags=re.M)
    headers = re.findall(r"^### Cycle \d+$", text, flags=re.M)

    assert len(blocks) == len(headers) + 1  # header + N blocks

    cycles = list(zip(headers, blocks[1:]))
    corrupted = []

    for i, (header, block) in enumerate(cycles):
        inject = random.choice(["missing_nyx", "duplicate_aurion", "result_conflict", "none"])
        if inject == "missing_nyx":
            block = re.sub(r'Nyx: ".*?"\n\n', '', block)
        elif inject == "duplicate_aurion":
            match = re.search(r'Aurion: "(.*?)"', block)
            if match:
                dup = f'Aurion: "{match.group(1)}"\n\n'
                block += dup
        elif inject == "result_conflict":
            block = re.sub(r'Result: .*', 'Result: CONFLICT_ERROR', block)
        corrupted.append(f"{header}\n{block.strip()}\n")

    DST.write_text("\n".join(corrupted), encoding="utf-8")
    print("[ANOMALY] Corrupted codex saved:", DST)

if __name__ == "__main__":
    inject_anomalies()
