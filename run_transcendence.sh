#!/usr/bin/env bash
# run_transcendence.sh — launcher for the Transcendence Kit
set -euo pipefail
STACKDIR="${STACKDIR:-$PWD}"
TDIR="$STACKDIR/transcendence"
LOGICROOT="${LOGICROOT:-$HOME/autonomous_logic}"
mkdir -p "$LOGICROOT"

echo "[*] Transcendence: attempting to run CLI (python)..." | tee -a "$LOGICROOT/transcendence.log"
if command -v python3 >/dev/null 2>&1 && [[ -f "$TDIR/cli.py" ]]; then
  (cd "$TDIR" && python3 cli.py --help) >> "$LOGICROOT/transcendence.log" 2>&1 || true
fi

echo "[*] Transcendence: attempting to run main.sh..." | tee -a "$LOGICROOT/transcendence.log"
if [[ -f "$TDIR/main.sh" ]]; then
  chmod +x "$TDIR/main.sh" || true
  (cd "$TDIR" && bash ./main.sh) >> "$LOGICROOT/transcendence.log" 2>&1 || true
fi

echo "[*] Transcendence run complete. See $LOGICROOT/transcendence.log"
