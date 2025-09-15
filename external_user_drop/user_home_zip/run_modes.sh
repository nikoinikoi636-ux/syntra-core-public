#!/usr/bin/env bash
set -euo pipefail

CORE="/mnt/data/core/sofia_sentinel_bionet_v3_plus.py"
LAB="/mnt/data/lab"
CALM="$LAB/heart_rules_calm.json"
STRICT="$LAB/heart_rules_strict.json"

if [[ ! -f "$CORE" ]]; then
  echo "Missing core script: $CORE"
  exit 1
fi

run_mode() {
  local RULES="$1"
  local NAME="$2"
  echo "== $NAME scan =="
  HEART_NODE=1 HEART_RULES="$RULES" python3 "$CORE" bionet scan "$LAB"
  echo "-- $NAME report --"
  python3 "$CORE" report last "$LAB"
  echo
}

run_mode "$CALM" "Calm"
run_mode "$STRICT" "Strict"
