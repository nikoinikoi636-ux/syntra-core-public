
#!/bin/bash

echo "🎮 Добре дошъл в инсталатора на BioNet Full Suite!"
echo "🛠️ Започваме автоматично разопаковане и настройка..."

INSTALL_DIR="$HOME/sintra_bionet_full"
ZIP_NAME="bionet_full_suite_complete.zip"

# 👉 Създаване на инсталационна директория
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR" || exit 1

# 👉 Копиране и разархивиране на основния пакет
if [ -f "$HOME/downloads/$ZIP_NAME" ]; then
    cp "$HOME/downloads/$ZIP_NAME" .
    unzip -o "$ZIP_NAME"
else
    echo "❌ Не открих $ZIP_NAME в ~/downloads. Моля, изтегли архива първо!"
    exit 1
fi

# 👉 Проверка за налични зависимости
echo "🔍 Проверяваме зависимости (git, gh, unzip)..."
pkg install -y git gh unzip || echo "⚠️ Termux dependency check failed."

# 👉 Настройка на git
echo "🔐 Конфигурирай своя GitHub акаунт:"
git config --global user.name "ТВОЕТО_ИМЕ"
git config --global user.email "email@example.com"
gh auth login

# 👉 Изпълнение на Git синхронизация
echo "🚀 Качваме кода в GitHub..."
chmod +x sintra_git_sync_webhook.sh
./sintra_git_sync_webhook.sh

# 👉 Финално съобщение
echo "✅ Инсталацията завърши успешно!"
echo "📁 Всичко е в: $INSTALL_DIR"
echo "🌐 Данните са синхронизирани с GitHub и готови за свързване със Sintra.ai"
