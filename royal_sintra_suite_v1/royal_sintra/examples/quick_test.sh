#!/usr/bin/env bash
set -e
python royal_sintra.py collect --paths "$HOME/sintra_logic" "$PREFIX/var/log" --max-size-mb 5 || true
LATEST=$(ls -1dt evidence/* | head -n1)
python royal_sintra.py normalize --evidence "$LATEST"
python royal_sintra.py sanitize --evidence "$LATEST"
python royal_sintra.py analyze --evidence "$LATEST"
