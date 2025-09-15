#!/data/data/com.termux/files/usr/bin/bash
# start_wormlab.sh — run the simulator and guard safely in Termux
cd ~/sentinel-core

# init sandbox if missing
if [ ! -d "wormlab" ]; then
  python3 wormlab_sim.py init
fi

# start guard and simulate in tmux sessions
if ! tmux has-session -t guard 2>/dev/null; then
  tmux new -d -s guard 'cd ~/sentinel-core && python3 honeypot_guard.py'
  echo "🛡️ guard started in tmux session 'guard'"
else
  echo "guard already running"
fi

if ! tmux has-session -t wormsim 2>/dev/null; then
  tmux new -d -s wormsim 'cd ~/sentinel-core && python3 wormlab_sim.py simulate --rounds 30 --sleep 0.5'
  echo "🧪 simulator started in tmux session 'wormsim'"
else
  echo "simulator already running"
fi

echo "Use: tmux attach -t guard   # to watch guard"
echo "     tmux attach -t wormsim # to watch simulator"
