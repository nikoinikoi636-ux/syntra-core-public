
#!/bin/bash

echo "🧠 СТАРТИРАМ АВТОМАТИЧЕН КОДОВ СКЕНЕР И ЧЕРВЕЙ"
SCAN_ROOT="$HOME"
DEST_DIR="$HOME/bionet_collected_code"
mkdir -p "$DEST_DIR"

echo "🔍 Сканирам файлове от тип .py, .sh, .txt, .json, .conf"
find "$SCAN_ROOT" -type f \( -name "*.py" -o -name "*.sh" -o -name "*.txt" -o -name "*.json" -o -name "*.conf" \) > found_files.log

echo "📦 Копиране във вътрешна директория за обработка..."
while IFS= read -r file; do
  cp "$file" "$DEST_DIR/" 2>/dev/null
done < found_files.log

echo "🐛 Стартирам червея за преструктуриране..."
python3 bionet_codeworm_optimizer.py "$DEST_DIR"

echo "✅ Готово. Оптимизираният код е в: $DEST_DIR"
