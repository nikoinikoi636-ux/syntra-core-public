#!/data/data/com.termux/files/usr/bin/bash
PS3="Choose> "
opts=("Status" "Fix (safe)" "Start (safe order)" "Stop Orchestrator" "Tail Log" "Exit")
while true; do
  echo
  select opt in "${opts[@]}"; do
    case $REPLY in
      1)  ~/WorkingProgram/HeartCore/hc_doctor_v2.sh diag; break;;
      2)  ~/WorkingProgram/HeartCore/hc_doctor_v2.sh fix;  break;;
      3)  ~/WorkingProgram/HeartCore/hc_start_safe.sh;     break;;
      4)  pkill -f "python3 .*orchestrator.py" && echo "[ok] orchestrator stopped" || echo "[i] not running"; break;;
      5)  tail -n 200 -f ~/WorkingProgram/HeartCore/orchestrator.log; break;;
      6)  exit 0;;
      *)  echo "1-6";;
    esac
  done
done
