#!/bin/bash
echo "🔧 Installing Syntra AI Transcendence System..."
apt update && apt install -y python3 git unzip streamlit

echo "📦 Unpacking core components..."
unzip syntra_core.zip -d syntra_core
cd syntra_core

chmod +x main.sh run_dashboard.sh
echo "✅ Ready! Use './main.sh' to start analysis."
echo "📊 To view dashboard: './run_dashboard.sh'"