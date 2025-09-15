#!/bin/bash
cd ~/syntra_core || exit 1
git add .
git commit -m "🧠 SyntraCore logic update $(date)"
git push origin main
