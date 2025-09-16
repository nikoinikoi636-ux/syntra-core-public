#!/data/data/com.termux/files/usr/bin/bash
LOG_DIR="$HOME/WorkingProgram/HeartCore/logs"
TOOL_DIR="$HOME/WorkingProgram/HeartCore/tools"
cd "$LOG_DIR" || exit 1

print_menu() {
  echo "============== 💠 HeartCore MENU 💠 =============="
  echo "1) 📄 Преглед на log файлове"
  echo "2) 🧪 Стартирай Self Evaluation"
  echo "3) 🔁 Генерирай Auto-Merge Patch"
  echo "4) 💾 Git Commit & Push"
  echo "5) 🚪 Изход"
  echo "=============================================="
}

view_logs() {
  echo "📁 Налични логове:"
  mapfile -t files < <(find "$LOG_DIR" -type f -name "*.log" -o -name "*.json" -o -name "*.txt")
  for i in "${!files[@]}"; do echo "$((i+1))) ${files[$i]##*/}"; done

  echo -n "Избери номер: "
  read -r choice
  index=$((choice - 1))
  [ "$choice" -ge 1 ] && [ "$choice" -le "${#files[@]}" ] || { echo "❌ Невалиден избор."; return; }

  echo "Откриване: ${files[$index]}"
  less "${files[$index]}"
}

run_eval() {
  echo "🧪 Стартиране на самооценка..."
  python3 "$TOOL_DIR/self_evaluation_core.py"
}

run_patch() {
  echo "🔁 Генериране на auto-patch..."
  python3 "$TOOL_DIR/auto_merge_patch.py"
  echo "Готово. Прегледай: $LOG_DIR/auto_patch_plan.txt"
}

git_commit_push() {
  echo "💾 Извършване на git commit & push..."
  cd "$HOME/WorkingProgram/HeartCore" || return
  git add .
  git commit -m "🤖 Auto-patch & evaluation update"
  git push
}

while true; do
  print_menu
  echo -n "Избор: "
  read -r opt
  case "$opt" in
    1) view_logs ;;
    2) run_eval ;;
    3) run_patch ;;
    4) git_commit_push ;;
    5) echo "🚪 Изход..."; break ;;
    *) echo "❗ Невалиден избор." ;;
  esac
  echo ""
done
