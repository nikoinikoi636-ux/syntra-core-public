#!/bin/bash
# Sync Syntra export folder to Google Drive
EXPORT_DIR="$HOME/syntra_exports"
DESTINATION="gdrive:/SyntraExports"

mkdir -p "$EXPORT_DIR"

echo "Syncing Syntra export folder..."
rclone sync "$EXPORT_DIR" "$DESTINATION" --progress
