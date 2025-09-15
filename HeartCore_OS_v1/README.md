# HeartCore_OS v1.0

Purpose: Локален, защитен набор от агенти и launcher-и за Android (Termux), Linux, macOS и Windows (WSL). Няма зловреден код. Всичко е защитно и офлайн по подразбиране.

## Съдържание
- `heart_safe_agents.py` — Truth/Integrity/Honor/Balance/Justice агенти (CLI)
- `load_all.sh` — Omni Loader (пуска всички агенти и прави JSON отчети)
- `start_core.sh` — удобен launcher за бързи команди
- `wormhole_bridge.py` — *по желание* качва архив към твой сървър (ти задаваш URL и SECRET)

## Termux (Android)
1. Инсталирай Termux от F-Droid.
2. В Termux:
   ```bash
   pkg update && pkg upgrade -y
   pkg install python git unzip -y
   termux-setup-storage  # дай достъп до /storage/shared
   ```
3. Качи `HeartCore_OS_v1_0.zip` и разархивирай:
   ```bash
   unzip HeartCore_OS_v1_0.zip -d ~/HeartCore_OS_v1
   cd ~/HeartCore_OS_v1
   chmod +x heart_safe_agents.py load_all.sh start_core.sh
   ```

## Примери
```bash
./heart_safe_agents.py truth ~/storage/shared/Documents
./heart_safe_agents.py integrity build ~/storage/shared/Download --manifest manifest.json
./heart_safe_agents.py integrity verify ~/storage/shared/Download --manifest manifest.json
./heart_safe_agents.py honor ~/projects/myrepo
./heart_safe_agents.py balance ~/storage/shared/Documents/finances.csv
./heart_safe_agents.py justice ~/storage/shared/Documents/contract.txt
```

## Omni Loader
```bash
./load_all.sh
# Отчетите са в ./reports/*.json
```

## Wormhole Bridge (по желание)
- Редактирай `wormhole_bridge.py` и замени `REMOTE_ENDPOINT` и `SECRET_KEY` с твоите.
- Пример:
```bash
python3 wormhole_bridge.py ~/storage/shared/Documents --upload
```
> Забележка: без твой URL, скриптът само прави локален архив.

— HeartCore_OS v1.0
