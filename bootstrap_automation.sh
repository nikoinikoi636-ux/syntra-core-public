#!/usr/bin/env bash
set -euo pipefail

# --- Папки ---
mkdir -p "$HOME/WorkingProgram/logs" \
         "$HOME/WorkingProgram/reports" \
         "$HOME/WorkingProgram/locks"

# --- Зависимости (без чупливи пакети) ---
pkg install -y cronie poppler >/dev/null 2>&1 || true
pip install --upgrade requests beautifulsoup4 PyYAML typing_extensions soupsieve >/dev/null 2>&1 || true

# --- Конфиг файл (по желание редактирай после) ---
cat > "$HOME/WorkingProgram/.hc_env" <<'ENV'
ADMIN_NAME="Administrator"
NODE_LABEL="PHOENIX_NODE_BG"
REPO_DIR="$HOME/HeartCoreRepo"     # ако няма repo, upload се прескача
SOURCES="$HOME/WorkingProgram/harvest/sources.yml"
NOTES_DIR="$HOME/WorkingProgram/HeartCore/notes"
KB="$HOME/WorkingProgram/HeartCore/logic/kb.jsonl"
SEEN="$HOME/WorkingProgram/HeartCore/logic/seen.txt"
LOG_DIR="$HOME/WorkingProgram/logs"
REPORT_DIR="$HOME/WorkingProgram/reports"
ENV

# --- Главен рънър ---
cat > "$HOME/downloads/hc_run.sh" <<'RUN'
#!/usr/bin/env bash
set -euo pipefail
source "$HOME/WorkingProgram/.hc_env"

# Lock (flock или fallback)
LOCKF="$HOME/WorkingProgram/locks/hc.lock"
if command -v flock >/dev/null 2>&1; then
  exec 200>"$LOCKF"
  flock -n 200 || { echo "[WARN] Already running. Exit."; exit 0; }
else
  mkdir "${LOCKF}.d" 2>/dev/null || { echo "[WARN] Already running. Exit."; exit 0; }
  trap 'rm -rf "${LOCKF}.d"' EXIT
fi

ts(){ date +"%Y-%m-%d %H:%M:%S"; }
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/hc_$(date +%Y%m%d_%H%M%S).log"
echo "[INFO $(ts)] start hc_run" | tee -a "$LOG"

# НЕТ проверка (кратка и ясна)
if ! curl -Is https://www.google.com >/dev/null 2>&1; then
  echo "[WARN $(ts)] no internet, abort" | tee -a "$LOG"
  exit 0
fi

# Подготви пътища
mkdir -p "$(dirname "$KB")" "$REPORT_DIR"

# Жътва (интернет)
echo "[INFO $(ts)] harvest…" | tee -a "$LOG"
python3 "$HOME/WorkingProgram/harvest/harvester.py" \
  --config "$SOURCES" \
  --out    "$KB" \
  --seen   "$SEEN" 2>&1 | tee -a "$LOG" || true

# Инджест (локални бележки)
echo "[INFO $(ts)] ingest local…" | tee -a "$LOG"
python3 "$HOME/WorkingProgram/harvest/ingest_local.py" \
  --notes-dir "$NOTES_DIR" \
  --out       "$KB" 2>&1 | tee -a "$LOG" || true

# Верификация / кратък отчет
echo "[INFO $(ts)] verify…" | tee -a "$LOG"
python3 "$HOME/WorkingProgram/harvest/verify_kb.py" \
  --kb "$KB" \
  --config "$SOURCES" 2>/dev/null | head -n 20 | tee -a "$LOG" || true

# Пулс + експорт (твоят скрипт)
echo "[INFO $(ts)] export…" | tee -a "$LOG"
if ! "$HOME/downloads/init_heartcore.sh" 2>&1 | tee -a "$LOG"; then
  echo "[ERR  $(ts)] init_heartcore.sh failed" | tee -a "$LOG"
fi

# Намери последния export (директория/архив)
LAST_EXPORT=$(ls -1t "$HOME/WorkingProgram/sintra_export" 2>/dev/null | head -n1 || true)

# GitHub upload (ако има repo)
if [ -d "$REPO_DIR/.git" ]; then
  echo "[INFO $(ts)] github sync…" | tee -a "$LOG"
  if [ -n "$LAST_EXPORT" ]; then
    cp -r "$HOME/WorkingProgram/sintra_export/$LAST_EXPORT"/* "$REPO_DIR"/ 2>/dev/null || true
  fi
  ( cd "$REPO_DIR" && git add . && git commit -m "Auto-export $(date +%Y-%m-%d:%H%M)" && git push origin main ) \
    || echo "[WARN $(ts)] git push failed" | tee -a "$LOG"
else
  echo "[INFO $(ts)] no repo at $REPO_DIR – skip upload" | tee -a "$LOG"
fi

# Ротация на логове (дръж последните 50)
COUNT=$(ls -1t "$LOG_DIR"/hc_*.log 2>/dev/null | wc -l | tr -d ' ')
if [ "${COUNT:-0}" -gt 50 ]; then
  ls -1t "$LOG_DIR"/hc_*.log | tail -n +51 | xargs -r rm -f
fi

echo "[OK   $(ts)] done" | tee -a "$LOG"
RUN
chmod +x "$HOME/downloads/hc_run.sh"

# --- Cron (на всеки час, със случаен старт минута) ---
MIN=$(( RANDOM % 60 ))
( crontab -l 2>/dev/null | sed '/# HeartCore Automation/d' ; \
  echo "$MIN * * * * $HOME/downloads/hc_run.sh >> $HOME/WorkingProgram/logs/cron.log 2>&1 # HeartCore Automation" ) | crontab -

echo "[OK] Automation installed. Cron: minute=$MIN"
