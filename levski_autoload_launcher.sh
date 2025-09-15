#!/data/data/com.termux/files/usr/bin/bash

# === CONFIG ===
ROOT_DIR="$HOME/apps/Home/.titan/clones/20250831-025459_3"
LOG_FILE="$ROOT_DIR/levski_init_log.txt"
PYTHON="/data/data/com.termux/files/usr/bin/python3"
> "$LOG_FILE"

echo "🚀 Levski Auto-Loader started at $(date)" | tee -a "$LOG_FILE"
termux-tts-speak "Levski Autoload initiated"

# === STEP 1: Find all relevant files ===
FILES=$(find "$ROOT_DIR" -type f \( -iname "*.py" -o -iname "*.json" -o -iname "*.md" -o -iname "*.txt" -o -iname "*.yaml" \) )

# === STEP 2: Classify and run ===
for file in $FILES; do
  fname=$(basename "$file")
  case "$fname" in
    *_vault*|*vault_*)
      echo "🛡️ Vault module: $fname" | tee -a "$LOG_FILE"
      $PYTHON "$file" >> "$LOG_FILE" 2>&1
      ;;
    *symbolic*|*core*|*heartcore*|*bionet*|*sofia*|*sentinel*)
      echo "🧠 Core System: $fname" | tee -a "$LOG_FILE"
      $PYTHON "$file" >> "$LOG_FILE" 2>&1
      ;;
    *.json)
      echo "📄 Data File: $fname" | tee -a "$LOG_FILE"
      ;;
    *.md|*.txt|*.yaml)
      echo "🗒️ Text/Meta: $fname" | tee -a "$LOG_FILE"
      ;;
    *)
      echo "⚠️ Unrecognized file: $fname" | tee -a "$LOG_FILE"
      ;;
  esac
done

echo "✅ Levski Autoload complete at $(date)" | tee -a "$LOG_FILE"
termux-tts-speak "Levski Autoload complete"
