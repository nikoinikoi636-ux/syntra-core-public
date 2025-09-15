
#!/bin/bash

# 👉 Настройки
REPO_NAME="bionet-full-suite"
GIT_USER="your-github-username"
EMAIL="your-email@example.com"

# 👉 Създай нова директория
mkdir -p ~/sintra_bionet_sync && cd ~/sintra_bionet_sync

# 👉 Клониране на репото (ако съществува) или създаване
if [ ! -d ".git" ]; then
    git init
    git config user.name "$GIT_USER"
    git config user.email "$EMAIL"
    gh repo create $GIT_USER/$REPO_NAME --public --source=. --remote=origin --push
fi

# 👉 Добави файловете
cp -r /data/data/com.termux/files/home/downloads/bionet_full_suite_complete.zip .
unzip -o bionet_full_suite_complete.zip
git add .
git commit -m "🚀 Add BioNet Full Suite from Sintra Integration"
git push -u origin main
