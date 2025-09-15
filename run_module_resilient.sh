#!/data/data/com.termux/files/usr/bin/bash
# Usage: run_module_resilient.sh <abs_python_file>
set -euo pipefail
MOD="$1"
NAME="$(basename "$MOD")"
HC="$(dirname "$MOD")"
LOG_DIR="$HC/logs/modules"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/${NAME%.py}.log"

# Low-memory env knobs (safe on Termux/Android)
export PYTHONUNBUFFERED=1
export MALLOC_ARENA_MAX=2
export UV_THREADPOOL_SIZE=1

max_tries=3
delay=2

echo "[$(date '+%F %T')] START $NAME" | tee -a "$LOG"
for i in $(seq 1 $max_tries); do
  echo "[$(date '+%F %T')] attempt $i/$max_tries → python3 -u $MOD" | tee -a "$LOG"
  set +e
  nohup python3 -u "$MOD" >>"$LOG" 2>&1 &
  PID=$!
  wait "$PID"
  RC=$?
  set -e

  if [ $RC -eq 0 ]; then
    echo "[$(date '+%F %T')] OK $NAME exited 0" | tee -a "$LOG"
    exit 0
  elif [ $RC -eq 137 ]; then
    echo "[$(date '+%F %T')] SIGKILL (137) for $NAME — likely OOM. Backoff ${delay}s." | tee -a "$LOG"
  elif [ $RC -eq 143 ]; then
    echo "[$(date '+%F %T')] SIGTERM (143) for $NAME — stopping." | tee -a "$LOG"
    exit 143
  else
    echo "[$(date '+%F %T')] ERR $NAME exit=$RC — see $LOG. Backoff ${delay}s." | tee -a "$LOG"
  fi

  sleep "$delay"
  delay=$((delay*2))
done

echo "[$(date '+%F %T')] FAIL $NAME after $max_tries tries" | tee -a "$LOG"
exit 1
