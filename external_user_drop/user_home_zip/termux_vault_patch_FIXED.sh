#!/data/data/com.termux/files/usr/bin/bash

echo "== Termux Vault Patch & INIT Loader =="

# Step 1: Reinstall pip
pkg install -y python
python -m ensurepip --upgrade
python -m pip install --upgrade pip setuptools wheel

# Step 2: Install base tools
pkg install -y git curl wget unzip

# Step 3: Prepare vault directory
mkdir -p ~/vault_core
cd ~/vault_core

# Step 4: Download INIT zip
curl -O https://chat.openai.com/sandbox/vault_INIT.zip

# Step 5: Extract files
unzip -o vault_INIT.zip

# Step 6: Run the Vault System
echo "[*] Launching Vault Core..."
python3 main.py
