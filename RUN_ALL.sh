#!/usr/bin/env bash
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
PYBIN="python3"; command -v python3 >/dev/null 2>&1 || PYBIN="python"
# Smart defaults for mobile/Termux
$PYBIN heartcore_launcher.py --smart-batch --stagger 1 --session heartcore
