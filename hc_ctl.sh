#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
HC="$HOME/WorkingProgram/HeartCore"
PID="$HC/state/pids"
LOG="$HC/logs/modules"
mkdir -p "$PID" "$LOG"

mods=("boot_levski_v3.py" "sync_engine.py" "watchdog_sync_loop.py" "heart_walker.py" "orchestrator.py")

start() {
  for m in "${mods[@]}"; do
    name="${m%.py}"
    case "$name" in
      boot_levski_v3) out="$LOG/boot_levski.log" ;;
      sync_engine)    out="$LOG/sync_engine.log" ;;
      watchdog_sync_loop) out="$LOG/watcher.log" ;;
      heart_walker)   out="$LOG/heart_walker.log" ;;
      orchestrator)   out="$HC/orchestrator.log" ;;
    esac
    if [ -f "$PID/$name.pid" ] && kill -0 "$(cat "$PID/$name.pid")" 2>/dev/null; then
      echo "[ok] $name already running (PID $(cat "$PID/$name.pid"))"
      continue
    fi
    nohup python3 "$HC/$m" >> "$out" 2>&1 &
    echo $! > "$PID/$name.pid"
    echo "[start] $name → PID $(cat "$PID/$name.pid"))"
  done
}

stop() {
  for m in "${mods[@]}"; do
    name="${m%.py}"
    if [ -f "$PID/$name.pid" ]; then
      kill "$(cat "$PID/$name.pid")" 2>/dev/null || true
      rm -f "$PID/$name.pid"
      echo "[stop] $name"
    fi
  done
}

status() {
  for m in "${mods[@]}"; do
    name="${m%.py}"
    if [ -f "$PID/$name.pid" ] && kill -0 "$(cat "$PID/$name.pid")" 2>/dev/null; then
      echo "[RUNNING] $name (PID $(cat "$PID/$name.pid"))"
    else
      echo "[DOWN]    $name"
    fi
  done
}

logs() {
  tail -n 80 "$HC/orchestrator.log" 2>/dev/null || true
  for f in "$LOG"/{boot_levski.log,sync_engine.log,watcher.log,heart_walker.log}; do
    [ -f "$f" ] && { echo; echo "--- $(basename "$f") ---"; tail -n 50 "$f"; }
  done
}

case "${1:-status}" in
  start)  start ;;
  stop)   stop ;;
  restart) stop; start ;;
  status) status ;;
  logs)   logs ;;
  *) echo "Usage: $0 {start|stop|restart|status|logs}"; exit 1 ;;
esac
