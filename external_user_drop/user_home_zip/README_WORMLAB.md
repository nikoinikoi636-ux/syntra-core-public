# Safe WormLab (Simulator)

This bundle provides a **harmless, reversible worm-like simulation** contained in `./wormlab/` so you can test Sentinel reactions safely.

## Files
- `wormlab_sim.py` — init/simulate/undo/cleanup/status (sandboxed to `./wormlab`).
- `honeypot_guard.py` — watches `./wormlab` and raises signals on changes.
- `start_wormlab.sh` — starts both in `tmux` sessions.
- `stop_wormlab.sh` — stops sessions and restores files.

## Quick start (in ~/sentinel-core)
```
chmod +x wormlab_sim.py honeypot_guard.py start_wormlab.sh stop_wormlab.sh

# 1) initialize sandbox
python3 wormlab_sim.py init

# 2) start guard + simulator (tmux sessions)
./start_wormlab.sh

# watch signals
tail -f .bionet/signals.jsonl

# 3) stop & restore
./stop_wormlab.sh
```
All actions are logged to `wormlab/log.jsonl`. The simulator never touches files outside `./wormlab` and can be fully restored with `python3 wormlab_sim.py undo`.
