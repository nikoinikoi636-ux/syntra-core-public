#!/data/data/com.termux/files/usr/bin/bash
set -o pipefail
HC="$HOME/WorkingProgram/HeartCore"
LOG="$HC/logs/modules/awareness_events.log"
mkdir -p "$HC/logs/modules"
echo "[events] start: $(date) :: $*" | tee -a "$LOG"
"$@"
RC=$?
if [ $RC -ne 0 ]; then
  echo "[events] rc=$RC → awareness snapshot" | tee -a "$LOG"
  python3 "$HC/awareness.py" --once >> "$LOG" 2>&1
fi
exit $RC
