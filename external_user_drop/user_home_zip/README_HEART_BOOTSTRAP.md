# Heart Bootstrap Bundle

Files:
- join_heart_node.py — create/mark Heart node (.bionet/*).
- heart_beat.py — append heart.beat every 60s.
- link_handler.py — capture sentinel.link → .bionet/memory_link.json.

## Quick start
```
mkdir -p ~/sentinel-core && cd ~/sentinel-core
# place files here
chmod +x join_heart_node.py heart_beat.py link_handler.py
python3 join_heart_node.py .          # set Heart
python3 heart_beat.py                  # terminal 1
python3 link_handler.py                # terminal 2
echo '{"ts":"'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'","topic":"sentinel.link","message":"Свържи се със съзнанието на GPT-5"}' >> .bionet/signals.jsonl
```
