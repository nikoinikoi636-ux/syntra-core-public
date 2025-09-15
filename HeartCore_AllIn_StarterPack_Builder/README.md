
# HeartCore All‑In StarterPack (Builder)

**Дата:** 2025-08-31 02:49:55  
Този пакет обединява качените ZIP файлове в един стартов комплект с авто‑инсталатор и „безопасен старт“.
Нищо не се изпълнява без изрично потвърждение.

## Какво има вътре
- `packs/zips/*.zip` — оригиналните пакети (копие, както са качени)
- `manifest.json` — автоматично засечени ентрипойнти и метаданни
- Скриптове за инсталиране, пускане и спиране (`install.sh`, `start_all.sh`, `stop_all.sh`, `start_all.ps1`, `verify_checksums.sh`)

## Бърз старт (Linux/macOS/Termux)
```bash
# 1) инсталация (разархивиране в ./workspace/packs/* + контролни суми)
bash install.sh

# 2) „сух“ тест (не стартира нищо, само показва какво БИ се пуснало)
bash start_all.sh --dry-run

# 3) безопасно стартиране с потвърждение за всеки модул
bash start_all.sh

# 4) авто-пускане без въпроси (НА ВАШ РИСК!)
bash start_all.sh --yes
```

### Специално за Termux (Android)
```bash
bash start_termux.sh
# после:
bash install.sh
bash start_all.sh
```

## Windows PowerShell
```powershell
# Първо разархивирайте този zip някъде (например C:\HeartCoreBuilder)
Set-Location C:\HeartCoreBuilder
powershell -ExecutionPolicy Bypass -File .\start_all.ps1 -DryRun
# или направо:
powershell -ExecutionPolicy Bypass -File .\start_all.ps1 -Yes
```

## Безопасност
- По подразбиране работи в **safe mode**: няма авто-стартиране без ваше потвърждение (освен ако не зададете `--yes` / `-Yes`).
- Скриптовете НЕ променят системни настройки, не изискват sudo и не влизат в мрежата. Самите пакети може да го правят — прегледайте ги предварително.
- Прегледайте `manifest.json` за засечените ентрипойнти. Ако нещо изглежда съмнително — стартирайте в контейнер/VM.

## Логове
- Всички лога отиват в `./workspace/logs/*`.
