#!/usr/bin/env bash
set -euo pipefail
export LOCAL_DIR="${LOCAL_DIR:-$HOME/ChatGPT_Refuge}"
export BLOCK_NET="${BLOCK_NET:-off}"
export HARDEN="${HARDEN:-true}"
echo "[*] Starting Autonomous Sintra Core..."; ./sintra_core.sh || true
echo "[*] Running Autonomous Reasoner on Home ZIP data..."
DATAROOT="$PWD/external_user_drop/user_home_zip" LOGICROOT="$HOME/autonomous_logic" ./autonomous_reasoner.sh --json || true
echo "[*] Optional web snapshot..."; if [[ -f ./web_sources.txt ]]; then ./web_snapshot.sh web_sources.txt || true; SNAPDIR="$HOME/web_snapshots" OUTDIR="$HOME/web_diffs" ./html_diff_report.sh || true; fi
echo "[*] Done. Reports in $HOME/autonomous_logic and $HOME/web_diffs"