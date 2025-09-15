#!/data/data/com.termux/files/usr/bin/bash
set -e
cd "$(dirname "$0")"
echo "⚡ HeartCore Omni-Loader ⚡"
echo "Всички агенти са активни."
echo "-----------------------------------"
DOCS=~/storage/shared/Documents
DOWNLOADS=~/storage/shared/Download
OUT=./reports
mkdir -p "$OUT"
python3 heart_safe_agents.py truth "$DOCS" > "$OUT/truth_report.json" 2>&1 &
python3 heart_safe_agents.py integrity build "$DOWNLOADS" --manifest "$OUT/manifest.json" > "$OUT/integrity_build.log" 2>&1 &
python3 heart_safe_agents.py honor "$PWD" > "$OUT/honor_report.json" 2>&1 &
if [ -f "$DOCS/finances.csv" ]; then
  python3 heart_safe_agents.py balance "$DOCS/finances.csv" > "$OUT/balance_report.json" 2>&1 &
fi
if [ -f "$DOCS/contract.txt" ]; then
  python3 heart_safe_agents.py justice "$DOCS/contract.txt" > "$OUT/justice_report.json" 2>&1 &
fi
wait
echo "✅ Готово. Докладите са в $OUT/"
