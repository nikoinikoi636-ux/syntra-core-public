
# Sentinel Titan v4 — Defensive Failsafe (BG)

## Стартиране
```bash
python3 sofia_sentinel_titan_v4.py help
```

## Препоръчан флоу
```bash
# 1) Активирай Titan и запиши политика (харднинг)
python3 sofia_sentinel_titan_v4.py titan enable
python3 sofia_sentinel_titan_v4.py titan harden

# 2) Направи 3 read-only клона на директорията (локални защитни копия)
python3 sofia_sentinel_titan_v4.py titan clone

# 3) Създай honeyfiles + canary и провери ги
python3 sofia_sentinel_titan_v4.py titan honey init
python3 sofia_sentinel_titan_v4.py titan honey check

# 4) Snapshot (zip) за архив
python3 sofia_sentinel_titan_v4.py titan snapshot

# 5) Верификация спрямо последния клон
python3 sofia_sentinel_titan_v4.py titan verify

# 6) Възстановяване на файл от клон
python3 sofia_sentinel_titan_v4.py titan restore path/to/file.py
```
Всичко е локално и дефанзивно: няма мрежови действия, няма офанзивни "капанчета".
