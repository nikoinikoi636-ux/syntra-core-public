#!/bin/bash
# Uploads a file or folder to Google Drive using rclone

SOURCE_PATH="$1"
DESTINATION="gdrive:/SyntraBackups"

if [ -z "$SOURCE_PATH" ]; then
  echo "Usage: $0 <path-to-file-or-folder>"
  exit 1
fi

echo "Uploading $SOURCE_PATH to $DESTINATION ..."
rclone copy "$SOURCE_PATH" "$DESTINATION" --progress
