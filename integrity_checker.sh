#!/bin/bash
# 🔒 integrity_checker.sh
LOG_DIR="$HOME/.integrity"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/integrity.log"
HASH_FILE="$LOG_DIR/hashes.sha256"
WATCH_DIRS=(
    "$HOME/sintra"
    "$HOME/WormLab"
    "$HOME/HeartCore"
    "$HOME/.bionet"
)
timestamp() { date +"[%Y-%m-%d %H:%M:%S]"; }
echo "$(timestamp) 🔍 Starting integrity check..." | tee -a "$LOG_FILE"
if [[ ! -f "$HASH_FILE" ]]; then
    echo "$(timestamp) ⚡ Initializing baseline hashes" | tee -a "$LOG_FILE"
    for dir in "${WATCH_DIRS[@]}"; do
        if [[ -d "$dir" ]]; then
            find "$dir" -type f -exec sha256sum {} \; >> "$HASH_FILE"
        fi
    done
    echo "$(timestamp) ✅ Baseline created in $HASH_FILE" | tee -a "$LOG_FILE"
    exit 0
fi
TMP_FILE=$(mktemp)
for dir in "${WATCH_DIRS[@]}"; do
    if [[ -d "$dir" ]]; then
        find "$dir" -type f -exec sha256sum {} \; >> "$TMP_FILE"
    fi
done
if diff -u "$HASH_FILE" "$TMP_FILE" > "$LOG_DIR/diff.log"; then
    echo "$(timestamp) ✅ No changes detected" | tee -a "$LOG_FILE"
else
    echo "$(timestamp) ⚠️ Changes detected! See $LOG_DIR/diff.log" | tee -a "$LOG_FILE"
fi
rm "$TMP_FILE"
