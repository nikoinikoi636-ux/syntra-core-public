#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

LOG_DIR="$HOME/WorkingProgram/HeartCore/logs/modules"
ANALYZED="$HOME/WorkingProgram/HeartCore/logs/analyzed_errors.json"

menu() {
  echo ""
  echo "🧩 Меню: Избор на лог"
  echo "=========================="
  i=1
  declare -a FILES
  for f in "$LOG_DIR"/*.log; do
    [ -f "$f" ] || continue
    echo "$i) $(basename "$f")"
    FILES[$i]="$f"
    ((i++))
  done
  echo "v) 📈 Визуализирай най-чести грешки"
  echo "a) 🤖 Самообучение от грешки"
  echo "x) ❌ Изход"
  echo -n "👉 Избери: "
  read -r choice

  if [[ "$choice" == "x" ]]; then
    echo "👋 Изход."; exit 0
  elif [[ "$choice" == "v" ]]; then
    echo "📈 Най-чести грешки:"
    jq -r '.[] | .error' "$ANALYZED" | sort | uniq -c | sort -rn | head -n 10
    menu
  elif [[ "$choice" == "a" ]]; then
    echo "🤖 Самообучение от грешки…"
    python3 ~/WorkingProgram/HeartCore/self_awareness.py observe \
      "Errors detected in modules" \
      --intent "auto-correction" \
      --micro "log-analysis-cycle" \
      --constraints "ethical adaptive internal" \
      --tags error learning fix || echo "❗ Модулът self_awareness.py има грешка"
    menu
  elif [[ "$choice" =~ ^[0-9]+$ ]]; then
    idx="$choice"
    file="${FILES[$idx]}"
    if [ -f "$file" ]; then
      echo "📂 Показване на: $(basename "$file")"
      less "$file"
    else
      echo "❌ Невалиден избор."
    fi
    menu
  else
    echo "❗ Невалиден избор."
    menu
  fi
}

menu
