#!/usr/bin/env bash
set -e
LOG=./self_learn.log
echo "▶ Starting self-learn watcher… (logs: $LOG)"
# първи пълен рескан
python3 self_learn.py || true
# watcher
nohup python3 self_learn.py watch >> "$LOG" 2>&1 &
echo $! > .self_learn.pid
echo "✓ PID $(cat .self_learn.pid)"
