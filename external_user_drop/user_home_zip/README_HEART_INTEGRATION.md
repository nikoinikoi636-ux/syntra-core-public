# Heart Integration for Sofia Sentinel v1.0

This companion adds **BioNet Heart** commands without editing v1.0:
- `heart set <path|.>` — mark a directory/file as the Heart node.
- `heart find [--pattern "..."] [--max N]` — discover candidates.
- `heart pick <N>` — pick from the last discovery list.

## Usage
```
# put both files in your project root
python3 sofia_sentinel_heart_cli.py heart set .
python3 sofia_sentinel_heart_cli.py heart find --pattern "sentinel,heart,.py"
python3 sofia_sentinel_heart_cli.py heart pick 1
```
Outputs are written to `.bionet/` (registry.json, heart.json, signals.jsonl) that v1.0 already uses.
