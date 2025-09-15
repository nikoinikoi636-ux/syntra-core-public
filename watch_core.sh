#!/data/data/com.termux/files/usr/bin/bash
set -e
while true; do
  pgrep -f central_core_chat_v2_1.py >/dev/null || tmux new -ds core-portal 'cd $HOME/central_core && python central_core_chat_v2_1.py'
  pgrep -f 'central_core_bridge.py .* loop' >/dev/null || tmux new -ds core-bridge 'cd $HOME/central_core && python central_core_bridge.py --config bridge_config.json loop --interval 15'
  sleep 10
done
