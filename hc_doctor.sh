#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

HC="$HOME/WorkingProgram/HeartCore"
LOG="$HC/orchestrator.log"
ERR="$HC/heartcore_error.log"
ORCH="$HC/orchestrator.py"
OBJ="$HC/objective_core.py"
CODEX="$HOME/HeartCore_OS_v1/logs/paradox_codex.md"
CODEX_CLI="$HOME/HeartCore_OS_v1/sintra/sintra_codex_cli.py"

line() { printf '%s\n' "------------------------------------------------------------"; }
hdr()  { line; echo "$1"; line; }

exists(){ [ -e "$1" ]; }
running_py(){ ps -ef | grep -v grep | grep -q "python3 .*$(basename "$1")"; }

diagnose(){
  hdr "PHOENIX / HEARTCORE DIAGNOSE"
  echo "[*] Time: $(date)"
  echo "[*] Root: $HC"
  echo

  # tmux sessions (odd duplicates often cause the repeated Phoenix prints)
  if command -v tmux >/dev/null 2>&1; then
    echo "[tmux] Sessions:"
    tmux ls 2>/dev/null || echo "  (none)"
  else
    echo "[tmux] Not installed (ok)."
  fi
  echo

  # Python processes
  echo "[proc] python3 processes:"
  ps -ef | grep -v grep | grep python3 || echo "  (none)"
  echo

  # Orchestrator presence and state
  echo "[orch] file: $ORCH"
  exists "$ORCH" && echo "  OK" || echo "  MISSING"
  echo -n "[orch] running: "; running_py "$ORCH" && echo "YES" || echo "NO"

  # Objective Core presence
  echo "[objective_core.py] $(exists "$OBJ" && echo OK || echo MISSING)"
  echo

  # Git origin check (will not change anything, just reports and shows fix)
  echo "[git] origin:"
  if [ -d "$HC/.git" ]; then
    git -C "$HC" remote -v || true
    if ! git -C "$HC" remote -v | grep -q '^origin'; then
      echo "  (no origin) → To set:"
      echo "  git -C \"$HC\" remote add origin <YOUR_GITHUB_SSH_OR_HTTPS_URL>"
      echo "  git -C \"$HC\" push -u origin main"
    fi
  else
    echo "  Not a git repo → init with:"
    echo "  git -C \"$HC\" init && git -C \"$HC\" add -A && git -C \"$HC\" commit -m 'init'"
  fi
  echo

  # Logs
  echo "[logs]"
  [ -f "$LOG" ] && echo "  orchestrator.log: $(wc -l < "$LOG") lines" || echo "  orchestrator.log: (none)"
  [ -f "$ERR" ] && echo "  heartcore_error.log: $(wc -l < "$ERR") lines" || echo "  heartcore_error.log: (none)"
  echo "  recent errors (orchestrator.log):"
  [ -f "$LOG" ] && (grep -E "Timeout|Traceback|ERROR|Exception" -n "$LOG" | tail -n 10 || true) || true
  echo

  # Codex check
  echo "[codex] $CODEX"
  if [ -f "$CODEX" ]; then
    COUNT=$(grep -c '^### Cycle ' "$CODEX" || echo 0)
    echo "  cycles: $COUNT"
  else
    echo "  (missing)"
  fi
  echo

  # Phoenix “loop” indicator: check if the same last lines repeat continuously
  echo "[phoenix] tail signature:"
  [ -f "$LOG" ] && tail -n 30 "$LOG" | sed 's/[0-9-: ]//g' | cksum || echo "  (no log)"
}

fix_safe(){
  hdr "APPLY SAFE FIXES"

  # Install tmux if not present (helps control background tasks)
  if ! command -v tmux >/dev/null 2>&1; then
    echo "[fix] Installing tmux (Termux)…"
    yes | pkg install tmux >/dev/null 2>&1 || echo "[warn] tmux install skipped."
  fi

  # Kill duplicate orchestrator instances (safe)
  if running_py "$ORCH"; then
    echo "[info] Orchestrator is running."
  else
    echo "[fix] Starting orchestrator (nohup)…"
    if [ -f "$ORCH" ]; then
      ( cd "$HC" && nohup python3 "$ORCH" >> "$LOG" 2>&1 & )
      sleep 1
      running_py "$ORCH" && echo "[ok] Orchestrator started." || echo "[warn] Start attempted; check $LOG"
    else
      echo "[warn] $ORCH not found, skip start."
    fi
  fi

  # Simple log rotate if too large (>200k lines)
  if [ -f "$LOG" ]; then
    LINES=$(wc -l < "$LOG")
    if [ "$LINES" -gt 200000 ]; then
      TS=$(date +%Y%m%d-%H%M%S)
      echo "[fix] Rotating orchestrator.log ($LINES lines)…"
      mv "$LOG" "$LOG.$TS"
      : > "$LOG"
      echo "[ok] Rotated to $LOG.$TS"
    fi
  fi

  # Codex integrity: rebuild if missing or wrong count
  NEED_CODEX_REBUILD=0
  if [ ! -f "$CODEX" ]; then
    NEED_CODEX_REBUILD=1
    echo "[fix] Codex missing → will rebuild."
  else
    COUNT=$(grep -c '^### Cycle ' "$CODEX" || echo 0)
    if [ "$COUNT" -ne 1000 ]; then
      NEED_CODEX_REBUILD=1
      echo "[fix] Codex count=$COUNT (expected 1000) → will rebuild."
    fi
  fi
  if [ "$NEED_CODEX_REBUILD" -eq 1 ]; then
    if [ -f "$CODEX_CLI" ]; then
      python3 "$CODEX_CLI" rebuild --backup || echo "[warn] codex rebuild failed."
    else
      echo "[warn] Codex CLI not found at $CODEX_CLI (skip)."
    fi
  fi

  echo "[done] Safe fixes applied."
}

case "${1:-run}" in
  diag) diagnose ;;
  fix)  fix_safe ;;
  run)  diagnose; echo; fix_safe; echo; diagnose ;;
  *)    echo "Usage: $0 [diag|fix|run]"; exit 1 ;;
esac
