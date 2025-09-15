#!/usr/bin/env bash
set -euo pipefail

pkg update -y || true
pkg install -y tmux python jq git || true

echo "[*] Termux dependencies installed (tmux, python, jq)."
echo "[*] Next steps:"
echo "    bash install.sh"
echo "    bash start_all.sh --dry-run  # preview"
echo "    bash start_all.sh            # interactive start"
