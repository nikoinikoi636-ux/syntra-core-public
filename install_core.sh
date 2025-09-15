#!/data/data/com.termux/files/usr/bin/bash
echo "📦 Installing requirements..."
pkg update -y && pkg install -y python git nano

echo "🐍 Setting up Python environment..."
pip install requests psutil

echo "📁 Creating folders..."
mkdir -p ~/sintra_ai/core ~/sintra_ai/modules ~/sintra_ai/reports

echo "📜 Launching Core AI..."
python3 sintra_analysis.py
