#!/usr/bin/env bash
set -euo pipefail

SESSION_PREFIX="heartcore_"
if command -v tmux >/dev/null 2>&1; then
  for s in $(tmux ls 2>/dev/null | awk -F: '{print $1}'); do
    if [[ "$s" == $SESSION_PREFIX* ]]; then
      echo "[*] Killing tmux session: $s"
      tmux kill-session -t "$s" || true
    fi
  done
else
  echo "tmux not found; nothing to stop automatically."
fi
