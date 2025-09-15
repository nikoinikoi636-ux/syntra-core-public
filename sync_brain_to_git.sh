#!/usr/bin/env bash
set -e
git add sintra_brain.json logic_map.gv logic_map.png 2>/dev/null || true
git commit -m "chore: brain autosync $(date -u +%F_%T)" || true
git push || true
