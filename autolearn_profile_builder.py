#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AutoLearn Profile Builder
Scans paradox_codex.md and builds profile summaries for autonomous learning.
"""

from pathlib import Path
import re
from collections import Counter
import json

CODEX = Path('~/HeartCore_OS_v1/logs/paradox_codex.md').expanduser()
OUT = Path('~/HeartCore_OS_v1/logs/autolearn_profile.json').expanduser()

def extract_profiles():
    text = CODEX.read_text(encoding='utf-8')
    blocks = re.split(r"^### Cycle \d+$", text, flags=re.M)[1:]
    
    nyx_list, aurion_list, results = [], [], []
    for block in blocks:
        nyx_match = re.search(r'Nyx: "(.*?)"', block)
        aurion_match = re.search(r'Aurion: "(.*?)"', block)
        result_match = re.search(r'Result: (.*?)$', block, flags=re.M)
        if nyx_match: nyx_list.append(nyx_match.group(1))
        if aurion_match: aurion_list.append(aurion_match.group(1))
        if result_match: results.append(result_match.group(1))
    
    profile = {
        "nyx_top_phrases": Counter(nyx_list).most_common(10),
        "aurion_top_phrases": Counter(aurion_list).most_common(10),
        "result_distribution": Counter(results).most_common(),
        "total_cycles": len(results)
    }
    
    OUT.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
    print("[OK] Learning profile generated:", OUT)

if __name__ == "__main__":
    extract_profiles()
