#!/usr/bin/env bash
set -e
BASE="."
RULES="royal_sintra/heart_rules/indicators.yml"
python royal_sintra.py autopilot --paths "$HOME/sintra_logic" "$PREFIX/var/log" --rules "$RULES" --base "$BASE" --max-size-mb 5
