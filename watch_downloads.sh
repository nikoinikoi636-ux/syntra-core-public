#!/data/data/com.termux/files/usr/bin/bash

WATCH_DIR="$HOME/downloads"
LOG_FILE="$HOME/watch_log.txt"

echo "🔍 Running self-check.."
for cmd in inotifywait termux-tts-speak python3 unzip; do
  if command -v $cmd >/dev/null 2>&1; then
    echo "✅ $cmd available"
  else
    echo "❌ $cmd NOT available"
  fi
done

echo "👁️ Watching $WATCH_DIR for new files..." | tee -a "$LOG_FILE"
termux-tts-speak "Watcher activated"

while true; do
  NEWFILE=$(inotifywait -e create --format '%f' "$WATCH_DIR" 2>/dev/null)
  FILEPATH="$WATCH_DIR/$NEWFILE"

  echo "📥 Detected new file: $NEWFILE" | tee -a "$LOG_FILE"
  termux-tts-speak "New file detected"

  case "$NEWFILE" in
    *.py)
      echo "🚀 Running Python: $NEWFILE" | tee -a "$LOG_FILE"
      termux-tts-speak "Running Python file"
      python3 "$FILEPATH"
      ;;
    *.sh)
      echo "🔧 Executing Shell: $NEWFILE" | tee -a "$LOG_FILE"
      termux-tts-speak "Executing shell file"
      bash "$FILEPATH"
      ;;
    *.json)
      echo "🧩 JSON config: $NEWFILE" | tee -a "$LOG_FILE"
      termux-tts-speak "JSON file detected"
      cp "$FILEPATH" "$HOME/WorkingProgram/HeartCore/configs/"
      ;;
    *.zip)
      echo "📦 ZIP Archive: $NEWFILE" | tee -a "$LOG_FILE"
      termux-tts-speak "Unzipping archive"
      unzip -o "$FILEPATH" -d "$HOME/WorkingProgram/HeartCore/imports/"
      ;;
    *)
      echo "🔹 Other file: $NEWFILE" | tee -a "$LOG_FILE"
      ;;
  esac

  echo "✅ Done handling: $NEWFILE" | tee -a "$LOG_FILE"
done
