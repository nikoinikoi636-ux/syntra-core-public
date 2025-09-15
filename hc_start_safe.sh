#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
HC="$HOME/WorkingProgram/HeartCore"
LOG="$HC/orchestrator.log"

# Helpers
running_py(){ ps -ef | grep -v grep | grep -q "python3 .*$(basename "$1")"; }
kill_dupes(){
  pat="$1"
  mapfile -t PIDS < <(ps -ef | grep -v grep | grep -E "$pat" | awk '{print $2}' || true)
  if [ "${#PIDS[@]}" -gt 1 ]; then
    keep=$(printf '%s\n' "${PIDS[@]}" | sort -n | tail -n1)
    for p in "${PIDS[@]}"; do [ "$p" != "$keep" ] && kill -9 "$p" 2>/dev/null || true; done
    echo "[fix] Deduped '$pat' → kept PID $keep"
  fi
}

# 0) Optional: kill noisy tmux sessions that might re-spawn things
tmux kill-session -t autoscan6h 2>/dev/null || true
tmux kill-session -t alerts-test 2>/dev/null || true
tmux kill-session -t watchDL 2>/dev/null || true

# 1) Deduplicate anything previous
kill_dupes "python3 .*sync_engine\.py"
kill_dupes "python3 .*watchdog_sync_loop\.py"
kill_dupes "python3 .*orchestrator\.py"
kill_dupes "python3 .*boot_levski(_v3)?\.py"

# 2) Pre-warm Boot Levski (directly)
if running_py "$HC/boot_levski_v3.py"; then
  echo "[ok] boot_levski_v3.py already running."
else
  echo "[*] Starting boot_levski_v3.py…"
  nohup python3 -u "$HC/boot_levski_v3.py" >> "$LOG" 2>&1 &
  sleep 1
  running_py "$HC/boot_levski_v3.py" && echo "[ok] Boot Levski up." || echo "[warn] Boot Levski tried; check $LOG"
fi

# 3) Start Sync Engine with resilience
echo "[*] Starting Sync Engine (resilient)…"
"$HC/run_module_resilient.sh" "$HC/sync_engine.py" || echo "[warn] Sync Engine failed to stabilize."

# 4) Start Watcher with resilience
if [ -f "$HC/watchdog_sync_loop.py" ]; then
  echo "[*] Starting Watcher (resilient)…"
  "$HC/run_module_resilient.sh" "$HC/watchdog_sync_loop.py" || echo "[warn] Watcher failed to stabilize."
fi

# 5) Orchestrator last
if running_py "$HC/orchestrator.py"; then
  echo "[ok] orchestrator already running."
else
  echo "[*] Starting orchestrator…"
  nohup python3 -u "$HC/orchestrator.py" >> "$LOG" 2>&1 &
  sleep 1
  running_py "$HC/orchestrator.py" && echo "[ok] orchestrator up." || echo "[warn] orchestrator start attempted; check $LOG"
fi

echo
echo "[*] Tail orchestrator (last 60):"
tail -n 60 "$LOG" || true
echo
echo "[*] Recent module logs (last 40 lines each):"
for f in "$HC"/logs/modules/*.log; do
  [ -f "$f" ] || continue
  echo "----- $(basename "$f") -----"
  tail -n 40 "$f"
done
