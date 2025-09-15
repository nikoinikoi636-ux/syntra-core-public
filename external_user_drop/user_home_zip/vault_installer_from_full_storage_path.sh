#!/data/data/com.termux/files/usr/bin/bash

echo "[*] Vault Installer - Път от /Download до Termux HOME"
SOURCE="/storage/emulated/0/Download"
TARGET="/storage/emulated/0/Android/data/com.termux/files/home/vault_core"

echo "[*] Създаване на целевата директория: $TARGET"
mkdir -p "$TARGET"

echo "[*] Копиране на файловете от $SOURCE до $TARGET..."
cp -r "$SOURCE"/* "$TARGET"/

cd "$TARGET"

echo "[*] Проверка за vault_INIT.zip..."
if [ -f vault_INIT.zip ]; then
  echo "[*] Разархивиране..."
  unzip -o vault_INIT.zip
fi

echo "[*] Стартиране на Vault Core..."
if [ -f main.py ]; then
  echo "[*] Стартирам main.py"
  python main.py
else
  echo "[!] main.py не е намерен. Провери дали е в ZIP архива или директно в Download."
fi
