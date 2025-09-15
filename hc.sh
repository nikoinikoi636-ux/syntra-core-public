#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

HC_ROOT="$HOME/WorkingProgram/HeartCore"
LOG="$HC_ROOT/orchestrator.log"
ORCH="$HC_ROOT/orchestrator.py"
OBJ="$HC_ROOT/objective_core.py"
CODEX_CLI="$HOME/HeartCore_OS_v1/sintra/sintra_codex_cli.py"
JSON_OUT="$HOME/HeartCore_OS_v1/logs/cycles_21_1000.json"

exists() { [ -e "$1" ]; }
running() { ps -ef | grep -v grep | grep -q "python3 .*$(basename "$1")"; }

start_orch() {
  if running "$ORCH"; then echo "[INFO] Orchestrator already running."; return 0; fi
  if ! exists "$ORCH"; then echo "[ERROR] Not found: $ORCH"; return 2; fi
  ( cd "$HC_ROOT" && nohup python3 "$ORCH" > "$LOG" 2>&1 & )
  sleep 1
  if running "$ORCH"; then echo "[OK] Orchestrator started. Log: $LOG"; else echo "[WARN] Start attempted; check log."; fi
}

stop_orch() {
  if running "$ORCH"; then
    pkill -f "$(basename "$ORCH")" && echo "[OK] Orchestrator stopped."
  else
    echo "[INFO] Orchestrator not running."
  fi
}

status_all() {
  echo "=== STATUS ==="
  echo -n "Orchestrator: "; running "$ORCH" && echo "RUNNING" || echo "STOPPED"
  [ -f "$LOG" ] && echo "Log path: $LOG"
  if [ -f "$OBJ" ]; then
    echo "--- ObjectiveCore state ---"
    python3 "$OBJ" status || true
  else
    echo "[WARN] objective_core.py not found."
  fi
}

tail_logs() {
  local n="${1:-60}"
  if [ ! -f "$LOG" ]; then echo "[WARN] No log yet: $LOG"; return 0; fi
  echo "--- last $n lines of orchestrator.log ---"
  tail -n "$n" "$LOG"
}

objective_activate() {
  if ! exists "$OBJ"; then echo "[ERROR] Not found: $OBJ"; return 2; fi
  python3 "$OBJ" activate
}

objective_get() {
  if ! exists "$OBJ"; then echo "[ERROR] Not found: $OBJ"; return 2; fi
  python3 "$OBJ" get
}

objective_set() {
  if ! exists "$OBJ"; then echo "[ERROR] Not found: $OBJ"; return 2; fi
  local p="$*"
  if [ -z "$p" ]; then
    echo "[ERROR] Provide purpose text, e.g.:"
    echo "hc obj-set Switch all systems on, connect all nodes, stabilize, defend HeartCore, and verify the goal."
    return 2
  fi
  python3 "$OBJ" set --purpose "$p"
  python3 "$OBJ" get
}

codex_rebuild() {
  if ! exists "$CODEX_CLI"; then echo "[ERROR] Not found: $CODEX_CLI"; return 2; fi
  python3 "$CODEX_CLI" rebuild --backup
}

codex_check() {
  if ! exists "$CODEX_CLI"; then echo "[ERROR] Not found: $CODEX_CLI"; return 2; fi
  python3 "$CODEX_CLI" check
}

codex_export() {
  if ! exists "$CODEX_CLI"; then echo "[ERROR] Not found: $CODEX_CLI"; return 2; fi
  python3 "$CODEX_CLI" export --range 21-1000 --out-json "$JSON_OUT"
}

print_menu() {
  clear 2>/dev/null || true
  cat <<MENU
================= HeartCore Control =================
1) Start Orchestrator
2) Stop Orchestrator
3) Status
4) Tail Logs (last 60)
5) Objective: Activate (bring-up + checks)
6) Objective: Show Purpose
7) Objective: Set Purpose
8) Codex: Rebuild (1..1000, backup)
9) Codex: Check
10) Codex: Export 21..1000 JSON
q) Quit
=====================================================
MENU
}

# CLI shortcuts: allow direct commands (hc start|stop|status|tail [N]|obj-activate|obj-get|obj-set ...|codex-*)
if [ $# -gt 0 ]; then
  case "$1" in
    start) start_orch ;;
    stop) stop_orch ;;
    status) status_all ;;
    tail) shift; tail_logs "${1:-60}" ;;
    obj-activate) objective_activate ;;
    obj-get) objective_get ;;
    obj-set) shift; objective_set "$@" ;;
    codex-rebuild) codex_rebuild ;;
    codex-check) codex_check ;;
    codex-export) codex_export ;;
    *) echo "Unknown command. Try: start|stop|status|tail|obj-activate|obj-get|obj-set|codex-rebuild|codex-check|codex-export"; exit 1 ;;
  esac
  exit $?
fi

# Interactive menu
while true; do
  print_menu
  read -rp "Choose: " choice
  case "$choice" in
    1) start_orch ;;
    2) stop_orch ;;
    3) status_all ;;
    4) tail_logs 60 ;;
    5) objective_activate ;;
    6) objective_get ;;
    7) read -rp "New Purpose: " newp; objective_set "$newp" ;;
    8) codex_rebuild ;;
    9) codex_check ;;
    10) codex_export ;;
    q|Q) echo "Bye."; exit 0 ;;
    *) echo "Invalid option." ;;
  esac
  echo
  read -rp "Press Enter to continue..." _
done
