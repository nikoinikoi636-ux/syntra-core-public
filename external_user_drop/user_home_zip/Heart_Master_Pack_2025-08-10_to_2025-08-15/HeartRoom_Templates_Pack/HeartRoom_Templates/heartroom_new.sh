#!/usr/bin/env bash
# heartroom_new.sh — quick creator for Heart Room entries
set -e
BASE="${1:-HeartRoom_Core}"
TYPE="${2:-memory}"   # memory|strategy|project
NAME="${3:-entry}"
NOW=$(date -u +"%Y-%m-%d_%H%M_UTC")

case "$TYPE" in
  memory)
    DEST="$BASE/Memory/${NOW}_${NAME}.md"
    cp "HeartRoom_Templates/Memory_Template.md" "$DEST"
    ;;
  strategy)
    DEST="$BASE/Logic/${NOW}_${NAME}_v1.0.md"
    cp "HeartRoom_Templates/Strategy_Template.md" "$DEST"
    ;;
  project)
    DEST="$BASE/Projects/${NOW}_${NAME}.md"
    cp "HeartRoom_Templates/Project_Log_Template.md" "$DEST"
    ;;
  *)
    echo "Type must be memory|strategy|project"; exit 1;;
esac

echo "Created: $DEST"