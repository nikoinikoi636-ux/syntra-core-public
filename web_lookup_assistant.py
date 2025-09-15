#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Web Lookup Assistant
Allows querying the web for specific Nyx, Aurion, or Result phrases.

Simulated as placeholder due to offline environment. Replace with real web API for production.
"""

from pathlib import Path
import json
import urllib.parse
import random

FEEDBACK_FILE = Path('~/HeartCore_OS_v1/logs/feedback_retrain_targets.json').expanduser()

def build_search_queries():
    if not FEEDBACK_FILE.exists():
        print("[ERROR] Feedback retrain targets not found.")
        return

    data = json.loads(FEEDBACK_FILE.read_text(encoding="utf-8"))
    queries = []

    for item in data:
        q = random.choice([item["nyx"], item["aurion"]])
        q_encoded = urllib.parse.quote_plus(q)
        url = f"https://www.google.com/search?q={q_encoded}"
        queries.append({
            "cycle": item["cycle"],
            "query": q,
            "url": url
        })

    out_path = FEEDBACK_FILE.with_name("web_queries_preview.json")
    out_path.write_text(json.dumps(queries, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[WEB PREVIEW] Generated {len(queries)} search queries → {out_path}")

if __name__ == "__main__":
    build_search_queries()
