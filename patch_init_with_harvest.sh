# patch_init_with_harvest.sh — инжектира harvest стъпките в init_heartcore.sh
#!/usr/bin/env bash
set -euo pipefail

INIT="${HOME}/downloads/init_heartcore.sh"
TAG="=== Harvest knowledge ==="
BACKUP="${INIT}.bak.$(date +%Y%m%d_%H%M%S)"

[ -f "$INIT" ] || { echo "[ERR] Няма файл: $INIT"; exit 1; }

# 0) Бекап
cp -f "$INIT" "$BACKUP"
echo "[OK] Backup: $BACKUP"

# 1) Проверка дали вече е патчнат
if grep -q "$TAG" "$INIT"; then
  echo "[OK] Harvest блок вече съществува. Нищо не променям."
  exit 0
fi

# 2) Проверка за маркер на Bridge командата
if ! grep -q 'python3 "\$BRIDGE"' "$INIT"; then
  echo "[ERR] Не намирам ред с 'python3 \"$BRIDGE\"' в $INIT — няма къде да вмъкна блока."
  echo "     Увери се, че скриптът извиква Sintra Bridge с python3 \"$BRIDGE\" ..."
  exit 1
fi

# 3) Сглоби harvest блока
read -r -d '' HARVEST_BLOCK <<'EOF'
# === Harvest knowledge ===
python3 "${HOME}/WorkingProgram/harvest/harvester.py" \
  --config "${HOME}/WorkingProgram/harvest/sources.yml" \
  --out    "${HOME}/WorkingProgram/HeartCore/logic/kb.jsonl" \
  --seen   "${HOME}/WorkingProgram/HeartCore/logic/seen.txt" || true

python3 "${HOME}/WorkingProgram/harvest/ingest_local.py" \
  --notes-dir "${HOME}/WorkingProgram/HeartCore/notes" \
  --out       "${HOME}/WorkingProgram/HeartCore/logic/kb.jsonl" || true

EOF

# 4) Вмъкни блока точно преди първото извикване на Bridge
awk -v block="$HARVEST_BLOCK" '
  BEGIN{inserted=0}
  {
    if (!inserted && $0 ~ /python3 "\$BRIDGE"/) {
      print block
      inserted=1
    }
    print
  }
' "$INIT" > "${INIT}.tmp"

mv -f "${INIT}.tmp" "$INIT"
chmod +x "$INIT"

echo "[OK] Добавих Harvest блока преди Sintra Bridge в: $INIT"

# 5) Нежни напомняния/помощ
echo "[INFO] Увери се, че съществуват файловете:"
echo "  - \$HOME/WorkingProgram/harvest/harvester.py"
echo "  - \$HOME/WorkingProgram/harvest/sources.yml"
echo "  - \$HOME/WorkingProgram/harvest/ingest_local.py"
echo "Ако липсват, кажи и ще ти пусна auto-setup."
