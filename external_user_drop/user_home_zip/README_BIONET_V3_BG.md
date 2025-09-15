
# Sofia Sentinel BioNet v3 — Quickstart (BG)

## Стартиране
```bash
python3 sofia_sentinel_bionet_v3.py help
```

## Типичен флоу
```bash
# 1) Инициализация върху текущата директория (или задайте друга)
python3 sofia_sentinel_bionet_v3.py bionet init

# 2) Периодично сканиране (имунен отговор + огледални копия)
python3 sofia_sentinel_bionet_v3.py bionet scan

# 3) Карта на организма (органи/възли + слаби места)
python3 sofia_sentinel_bionet_v3.py bionet graph

# 4) Централен сигнал по "вени" към всички клетки
python3 sofia_sentinel_bionet_v3.py signal send heartbeat "Stay vigilant"

# 5) Проверка на inbox на конкретен възел
python3 sofia_sentinel_bionet_v3.py node inbox path/to/file.py

# 6) Диференциране спрямо backup, възстановяване, карантина
python3 sofia_sentinel_bionet_v3.py integrity diff path/to/file.py
python3 sofia_sentinel_bionet_v3.py integrity restore path/to/file.py
python3 sofia_sentinel_bionet_v3.py integrity quarantine path/to/file.py

# 7) Пълен "skeleton" backup (zip)
python3 sofia_sentinel_bionet_v3.py backup now
```

## Идеята
- **Brain**: registry.json + командите управляват общото състояние.
- **Veins**: signals.jsonl + mailboxes/ за разнасяне на съобщения.
- **Bones**: bone_repo/ + backups/ пазят огледални копия и zip архиви.
- **Immune**: при подозрение → карантина + възстановяване от Bones.
- **Organs**: класификация на файлове по ролята им (Neural/Liver/Skin/Tissue).

Всичко е дефанзивно и локално. Няма офанзивни/вредни действия.
