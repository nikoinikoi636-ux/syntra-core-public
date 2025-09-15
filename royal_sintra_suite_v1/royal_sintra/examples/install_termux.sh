#!/usr/bin/env bash
set -e
pkg update -y
pkg install -y python git
python -m venv .venv || true
source .venv/bin/activate
pip install -r requirements.txt
echo "[OK] Termux setup complete."
