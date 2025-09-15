#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

HC="$HOME/WorkingProgram/HeartCore"
LOG="$HC/orchestrator.log"
ERR="$HC/heartcore_error.log"
ORCH="$HC/orchestrator.py"
OBJ="$HC/objective_core.py"
CODEX="$HOME/HeartCore_OS_v1/logs/paradox_codex.md"
CODEX_CLI="$HOME/HeartCore_OS_v1/sintra/sintra_codex_cli.py"

line(){ printf '%s\n' "------------------------------------------------------------"; }
hdr(){ line; echo "$1"; line; }

exists(){ [ -e "$1" ]; }
running_py(){ ps -ef | grep -v grep | grep -q "python3 .*$(basename "$1")"; }

# keep only newest PID for a pattern, kill the rest
one_instance(){
  pat="$1"
  mapfile -t PIDS < <(ps -ef | grep -v grep | grep -E "$pat" | awk '{print $2}' || true)
  if [ "${#PIDS[@]}" -gt 1 ]; then
    keep=$(printf '%s\n' "${PIDS[@]}" | sort -n | tail -n1)
    for p in "${PIDS[@]}"; do
      if [ "$p" != "$keep" ]; then
        kill -9 "$p" 2>/dev/null || true
      fi
    done
    echo "[fix] Deduped '$pat' → kept PID $keep"
  fi
}

ensure_running(){
  # $1 = abs path to python file
  tgt="$1"
  if running_py "$tgt"; then
    echo "[ok] $(basename "$tgt") already running."
  else
    if [ -f "$tgt" ]; then
      ( cd "$HC" && nohup python3 "$tgt" >> "$LOG" 2>&1 & )
      sleep 1
      running_py "$tgt" && echo "[ok] started $(basename "$tgt")" || echo "[warn] start attempted for $(basename "$tgt"); check log."
    else
      echo "[warn] missing: $tgt"
    fi
  fi
}

diagnose(){
  hdr "PHOENIX / HEARTCORE DIAGNOSE"
  echo "[*] Time: $(date)"
  echo "[*] Root: $HC"
  echo

  if command -v tmux >/dev/null 2>&1; then
    echo "[tmux] Sessions:"; tmux ls 2>/dev/null || echo "  (none)"
  else
    echo "[tmux] Not installed (ok)."
  fi
  echo

  echo "[proc] python3 processes:"
  ps -ef | grep -v grep | grep python3 || echo "  (none)"
  echo

  echo "[orch] file: $ORCH"
  exists "$ORCH" && echo "  OK" || echo "  MISSING"
  echo -n "[orch] running: "; running_py "$ORCH" && echo "YES" || echo "NO"

  echo "[objective_core.py] $(exists "$OBJ" && echo OK || echo MISSING)"
  echo

  echo "[git] origin:"
  if [ -d "$HC/.git" ]; then
    git -C "$HC" remote -v || true
    if ! git -C "$HC" remote -v | grep -q '^origin'; then
      echo "  (no origin) → To set:"
      echo "  git -C \"$HC\" remote add origin <YOUR_GITHUB_URL>"
      echo "  git -C \"$HC\" push -u origin main"
    fi
  else
    echo "  Not a git repo →"
    echo "  git -C \"$HC\" init && git -C \"$HC\" add -A && git -C \"$HC\" commit -m 'init'"
  fi
  echo

  echo "[logs]"
  [ -f "$LOG" ] && echo "  orchestrator.log: $(wc -l < "$LOG") lines" || echo "  orchestrator.log: (none)"
  [ -f "$ERR" ] && echo "  heartcore_error.log: $(wc -l < "$ERR") lines" || echo "  heartcore_error.log: (none)"
  echo "  recent errors (orchestrator.log):"
  [ -f "$LOG" ] && (grep -E "Timeout|Traceback|ERROR|Exception" -n "$LOG" | tail -n 10 || true) || true
  echo

  echo "[codex] $CODEX"
  if [ -f "$CODEX" ]; then
    COUNT=$(grep -c '^### Cycle ' "$CODEX" || echo 0)
    echo "  cycles: $COUNT"
  else
    echo "  (missing)"
  fi
  echo

  echo "[phoenix] tail signature:"
  # busybox sed had trouble with the dash range → use tr instead of sed
  if [ -f "$LOG" ]; then
    tail -n 30 "$LOG" | tr -d '0-9-: ' | cksum
  else
    echo "  (no log)"
  fi
}

fix_safe(){
  hdr "APPLY SAFE FIXES"

  if ! command -v tmux >/dev/null 2>&1; then
    echo "[fix] Installing tmux (Termux)…"
    yes | pkg install tmux >/dev/null 2>&1 || echo "[warn] tmux install skipped."
  fi

  # Deduplicate frequent offenders first
  one_instance "python3 .*sync_engine\.py"
  one_instance "python3 .*boot_levski(_v3)?\.py"

  # Ensure these are up before orchestrator to reduce orchestrator timeouts
  ensure_running "$HC/boot_levski_v3.py"
  ensure_running "$HC/sync_engine.py"

  # Now orchestrator
  if running_py "$ORCH"; then
    echo "[ok] orchestrator running."
  else
    echo "[fix] starting orchestrator (nohup)…"
    if [ -f "$ORCH" ]; then
      ( cd "$HC" && nohup python3 "$ORCH" >> "$LOG" 2>&1 & )
      sleep 1
      running_py "$ORCH" && echo "[ok] orchestrator started." || echo "[warn] start attempted; check $LOG"
    else
      echo "[warn] missing orchestrator: $ORCH"
    fi
  fi

  # rotate log if huge
  if [ -f "$LOG" ]; then
    LINES=$(wc -l < "$LOG")
    if [ "$LINES" -gt 200000 ]; then
      TS=$(date +%Y%m%d-%H%M%S)
      echo "[fix] Rotating orchestrator.log ($LINES lines)…"
      mv "$LOG" "$LOG.$TS"; : > "$LOG"; echo "[ok] Rotated to $LOG.$TS"
    fi
  fi

  # Codex integrity
  NEED=0
  if [ ! -f "$CODEX" ]; then NEED=1; echo "[fix] codex missing → rebuild"; else
    COUNT=$(grep -c '^### Cycle ' "$CODEX" || echo 0)
    [ "$COUNT" -ne 1000 ] && NEED=1 && echo "[fix] codex count=$COUNT → rebuild"
  fi
  if [ "$NEED" -eq 1 ] && [ -f "$CODEX_CLI" ]; then
    python3 "$CODEX_CLI" rebuild --backup || echo "[warn] codex rebuild failed."
  fi

  echo "[done] Safe fixes applied."
}

case "${1:-run}" in
  diag) diagnose ;;
  fix)  fix_safe ;;
  run)  diagnose; echo; fix_safe; echo; diagnose ;;
  *) echo "Usage: $0 [diag|fix|run]"; exit 1 ;;
esac
