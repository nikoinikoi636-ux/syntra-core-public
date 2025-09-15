#!/data/data/com.termux/files/usr/bin/bash
# stop_wormlab.sh — stop simulator/guard and cleanup sandbox
cd ~/sentinel-core
tmux kill-session -t wormsim 2>/dev/null || true
tmux kill-session -t guard   2>/dev/null || true
python3 wormlab_sim.py undo 2>/dev/null || true
echo "🧹 wormlab stopped and restored."
