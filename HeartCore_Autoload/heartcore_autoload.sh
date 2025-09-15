#!/usr/bin/env bash
# heartcore_autoload.sh — Autoload Heart Core + modules
# Generated: 2025-08-15 21:27 UTC

set -euo pipefail

ROOT="${1:-$PWD}"
CORE_DIR="$ROOT/HeartRoom_Core"
SAVE_DIR="$ROOT/HeartRoom_Save"
SELF_DIR="$CORE_DIR/SelfAwareness"

mkdir -p "$CORE_DIR" "$SAVE_DIR" "$SELF_DIR"

# Prefer FullOps profile if present; fallback to basic
FULLOPS="$SAVE_DIR/HeartCore_FullOps_PeterHristov.md"
BASIC="$SAVE_DIR/HeartCore_PeterHristov.md"

if [ -f "$FULLOPS" ]; then
  PROFILE="$FULLOPS"
elif [ -f "$BASIC" ]; then
  PROFILE="$BASIC"
else
  echo "(!) No HeartCore profile found in $SAVE_DIR. Place your .md there."; exit 1
fi

# Place profile into Core for active session
cp -f "$PROFILE" "$CORE_DIR/"

# Ensure Self-Awareness module files exist (copy from current dir if user placed them here)
for f in Core_SelfAwareness.md self_awareness_config.yaml self_awareness.py; do
  if [ -f "$f" ]; then
    cp -f "$f" "$SELF_DIR/"
  fi
done

echo "✔ Heart Core loaded from: $PROFILE"
echo "✔ Active Core path: $CORE_DIR"
echo "→ Run self-awareness logger (optional):"
echo "   cd "$SELF_DIR" && python3 self_awareness.py observe "Fact 1" "Fact 2" "Fact 3" --intent "First micro-step" --micro "10 min" --tags precious"
echo
echo "Toggles:"
echo " - диня  → Detect Filter Mode (toggle)"
echo " - курва → Z-Code Mode (toggle)"
