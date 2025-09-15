#!/data/data/com.termux/files/usr/bin/bash
termux-job-scheduler --cancel-all 2>/dev/null || true
termux-job-scheduler --job-id 777 --period-ms 21600000 --persisted --termux-task "python $HOME/conscious_core/conscious_loop.py"
echo "[OK] Scheduled every 6h."
