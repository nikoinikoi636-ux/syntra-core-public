#!/data/data/com.termux/files/usr/bin/bash
cd ~/downloads
tmux kill-session -t hc_connector 2>/dev/null
tmux new -d -s hc_connector "python connector_flask.py"
echo "[DONE] Flask connector running on 127.0.0.1:8787"
