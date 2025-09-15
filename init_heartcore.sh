#!/usr/bin/env bash
# init_heartcore.sh — HeartCore → Sintra Bridge export with safe outdir
set -euo pipefail

# === Config ===
SRC_DIR="${HOME}/WorkingProgram/HeartCore"
OUT_BASE="${HOME}/WorkingProgram/sintra_export"
BRIDGE="${HOME}/downloads/sintra_bridge/sintra_bridge.py"
ADMIN_NAME="Administrator"
NODE_LABEL="PHOENIX_NODE_BG"
PULSE_FILE="HEART_CORE_v3_1.md"
LOG_DIR="${HOME}/WorkingProgram/logs"
LOG_FILE="${LOG_DIR}/heartcore_init_$(date +%Y%m%d_%H%M%S).log"

# === Helpers ===
die(){ echo "[ERR] $*" | tee -a "$LOG_FILE"; exit 1; }
ok(){ echo "[OK] $*" | tee -a "$LOG_FILE"; }

# === Pre-flight ===
mkdir -p "$SRC_DIR" "$OUT_BASE" "$LOG_DIR"
: > "$LOG_FILE" || { echo "Не мога да пиша лог."; exit 1; }

command -v python3 >/dev/null 2>&1 || die "Няма python3 в PATH."
[ -f "$BRIDGE" ] || die "Липсва sintra_bridge.py: $BRIDGE"

# === HeartCore Pulse ===
TS_ISO="$(date -Iseconds)"
cat > "${SRC_DIR}/${PULSE_FILE}" <<EOF
# HEART_CORE
Signal: alive
Version: 3.1
Timestamp: ${TS_ISO}
Node: ${NODE_LABEL}
Admin: ${ADMIN_NAME}
EOF
ok "Пулс файлът е обновен: ${SRC_DIR}/${PULSE_FILE}"

# === Интегритет SHA256 ===
SHA="$(sha256sum "${SRC_DIR}/${PULSE_FILE}" | awk '{print $1}')"
echo "Checksum: ${SHA}" >> "${SRC_DIR}/${PULSE_FILE}"
ok "SHA256: ${SHA}"

# === Подготви outdir (с timestamp) ===
OUT_DIR="${OUT_BASE}/export_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUT_DIR"
chmod -R u+rwX "$OUT_BASE" || true
ok "Изходна директория: $OUT_DIR"

# === Run Bridge (с авто-рестарт при грешка) ===
set +e
python3 "$BRIDGE" \
  --source  "$SRC_DIR" \
  --out     "$OUT_DIR" \
  --bundle \
  --admin   "$ADMIN_NAME" \
  --node-label "$NODE_LABEL" \
  2>&1 | tee -a "$LOG_FILE"
RC=$?
set -e

if [ $RC -ne 0 ]; then
  echo "[WARN] Bridge върна код $RC, пробвам fallback..." | tee -a "$LOG_FILE"
  FALLBACK="${OUT_BASE}/export_fallback_$(date +%Y%m%d_%H%M%S)"
  mkdir -p "$FALLBACK"
  python3 "$BRIDGE" \
    --source "$SRC_DIR" \
    --out    "$FALLBACK" \
    --bundle \
    --admin  "$ADMIN_NAME" \
    --node-label "$NODE_LABEL" \
    2>&1 | tee -a "$LOG_FILE" || die "Fallback също се провали."
  OUT_DIR="$FALLBACK"
fi

# === Post-checks ===
BUNDLE_PATH="$(ls -1t "$OUT_DIR" | head -n1 || true)"
[ -n "$BUNDLE_PATH" ] || die "Не е намерен bundle в $OUT_DIR."
ok "Генериран пакет: ${OUT_DIR}/${BUNDLE_PATH}"

# === Резюме ===
echo "
================ SUMMARY ================
Source : ${SRC_DIR}
Output : ${OUT_DIR}/${BUNDLE_PATH}
Pulse  : ${PULSE_FILE}
SHA256 : ${SHA}
Log    : ${LOG_FILE}
========================================
" | tee -a "$LOG_FILE"

ok "Готово."

# === Auto GitHub Upload ===
REPO_DIR="${HOME}/HeartCoreRepo"
if [ -d "$REPO_DIR/.git" ]; then
  cp -r "$OUT_DIR"/* "$REPO_DIR"/
  cd "$REPO_DIR"
  git add .
  git commit -m "Auto-export $(date +%Y-%m-%d:%H%M)"
  git push origin main || echo "[WARN] Git push failed"
  ok "Export uploaded to GitHub repo: $REPO_DIR"
else
  echo "[INFO] GitHub repo не е конфигуриран в $REPO_DIR — прескачам upload."
fi
