#!/data/data/com.termux/files/usr/bin/bash

echo "[*] Vault Installer - From Android Download Folder"
DOWNLOAD_PATH="/sdcard/Download"
TARGET_PATH="$HOME/vault_core"

echo "[*] Creating target directory: $TARGET_PATH"
mkdir -p "$TARGET_PATH"

echo "[*] Copying files from Download to Termux home..."
cp -r "$DOWNLOAD_PATH"/* "$TARGET_PATH"/

cd "$TARGET_PATH"

echo "[*] Unzipping INIT archive (if exists)..."
if [ -f vault_INIT.zip ]; then
  unzip -o vault_INIT.zip
fi

echo "[*] Launching Vault Core..."
if [ -f main.py ]; then
  python main.py
else
  echo "[!] main.py not found. Please check your INIT files."
fi
