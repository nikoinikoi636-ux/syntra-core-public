
#!/bin/bash

echo "📊 BioNet Control Center"
echo "========================="
echo "1) Стартирай пълен тест (всички фази)"
echo "2) Сканирай директория"
echo "3) Качи резултати в GitHub"
echo "4) Генерирай отчет"
echo "5) Стартирай авто-събиране на нови файлове"
echo "6) CodeWorm: Сканирай телефона и преструктурирай кода"
echo "6) Изход"
echo "========================="
read -p "Избери опция (1-6): " choice

case $choice in
    1)
        python3 master_test_runner.py
        ;;
    2)
        read -p "👉 Въведи път до директорията за сканиране: " folder
        python3 sofia_sentinel_bionet_v3_plus.py bionet scan "$folder"
        ;;
    3)
        ./sintra_git_sync_webhook.sh
        ;;
    4)
        cat /tmp/bionet_full_test/bionet_test_report.json | less
        ;;
    5)
        echo "🔍 Сканираме за нови .py/.json/.txt файлове в ~/downloads..."
        find ~/downloads -type f \( -name "*.py" -o -name "*.txt" -o -name "*.json" \) > new_files.log
        while IFS= read -r file; do
            echo "➡️ Сканирам: $file"
            python3 sofia_sentinel_bionet_v3_plus.py bionet scan "$(dirname "$file")"
        done < new_files.log
        ;;

    5)
        echo "🧠 Стартиране на сканиране и преструктуриране на код (CodeWorm)"
        ./scan_and_optimize.sh
        ;;
    6)
        echo "👋 Изход..."
        exit 0
        ;;
    *)
        echo "❌ Невалиден избор!"
        ;;
esac
