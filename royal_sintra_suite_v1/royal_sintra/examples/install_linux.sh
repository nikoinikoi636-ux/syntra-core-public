#!/usr/bin/env bash
set -e
if command -v apt >/dev/null 2>&1; then
  sudo apt update && sudo apt install -y python3-venv git
fi
python3 -m venv .venv || true
source .venv/bin/activate
pip install -r requirements.txt
echo "[OK] Linux setup complete."
