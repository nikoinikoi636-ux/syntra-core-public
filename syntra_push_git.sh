#!/bin/bash
# Push local Syntra code to GitHub

REPO_DIR="$HOME/syntra_project"
cd "$REPO_DIR" || exit 1

git add .
git commit -m "Syntra export auto-push $(date)"
git push origin main
