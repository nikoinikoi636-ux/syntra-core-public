#!/bin/bash
echo "🚀 Initializing Sintra AI Transcendence Kernel..."
python3 core_supervisor.py &
python3 sintra_analysis.py script.py
python3 logic_visualizer.py script.py
python3 code_diff_engine.py script.py previous_script.py