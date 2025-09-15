#!/data/data/com.termux/files/usr/bin/bash

echo "📦 Премахване на нестабилния Python..."
pkg uninstall -y python

echo "⬇️ Инсталиране на Python 3.11..."
pkg install -y python3.11

echo "🧪 Активация на pip..."
python3.11 -m ensurepip
python3.11 -m pip install --upgrade pip setuptools wheel

echo "🧠 Инсталиране на библиотеки за Sintra AI..."
python3.11 -m pip install numpy==1.25.2
python3.11 -m pip install streamlit==1.27.2

echo "🛠️ Даване на права за изпълнение на всички .sh и .py файлове..."
chmod +x *.sh
chmod +x *.py

echo "📊 Стартиране на таблото..."
python3.11 -m streamlit run dashboard.py
