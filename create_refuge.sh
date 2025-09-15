#!/usr/bin/env bash
# Minimal create_refuge.sh (no-op) for Termux/portable use
set -euo pipefail
LOCAL_DIR="$HOME/ChatGPT_Refuge"
mkdir -p "$LOCAL_DIR"
case "${1:-}" in
  --init|--encrypt|--seal|--local-dir|--local-only) exit 0 ;;
  *) exit 0 ;;
esac
