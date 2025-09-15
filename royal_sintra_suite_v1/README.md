# 👑 Royal Sintra Suite v1

**Цел:** Единна „царска“ програма за локален офлайн триаж и анализ на логове + Heart Node регистър + Git мост + watcher.
Работи и в **Termux (Android)**, и в **Linux**. Минимални зависимости.

## 🚀 Бърз старт
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 1) Събиране
python royal_sintra.py collect --paths ~/sintra_logic /var/log --max-size-mb 5

# 2) Нормализация
python royal_sintra.py normalize --evidence <evidence_dir>

# 3) Санитизация на тайни
python royal_sintra.py sanitize --evidence <evidence_dir>

# 4) Анализ
python royal_sintra.py analyze --evidence <evidence_dir>

# 5) (По желание) Git мост
python royal_sintra.py bridge-push --evidence <evidence_dir> --repo git@github.com:USER/PRIVATE_REPO.git --branch sintra-sync

# 6) Heart Node регистрация
python royal_sintra.py join-heart --name "Sintra@Phone" --tags termux,guardian
```

## 📦 Какво прави
- **collect** → `evidence/<ts>/{raw,meta}` копира четими файлове (<5MB по подразбиране) + SHA256
- **normalize** → `normalized.jsonl` (ts/level/source/msg)
- **sanitize** → `sanitized/**` с редактирани ключове/токени
- **analyze** → `anomalies.json` + `summary.md` по `heart_rules/indicators.yml`
- **bridge-push** → качва безопасните артефакти в частно Git repo (по желание)
- **join-heart** → поддържа `.bionet/registry.json` и `signals.jsonl`
- **watch** → периодично изпълнява цикъла (offline; polling)

## 🔧 Termux бележки
```bash
pkg update && pkg install python git -y
termux-setup-storage
# после както е горе
```

## ⚖️ Безопасност
- Няма `os.system`; няма „скрити“ изпълнения. Само файлови операции и, по желание, `git` през subprocess.
- Профили за политики: `heart_rules/heart_rules_{calm,balanced,aggressive}.json`.
