# Sofia + GodMode v1 — Quickstart (BG)

## Стартиране
```bash
python3 sofia_godmode_v1.py
```

## Бързи команди
- `status` — виж текущ статус
- `god level 2` — по-прoактивен режим
- `think План: ...` — добави мисъл/план в паметта
- `memory save` / `memory load` — persist на паметта
- `set keyword свобода` — промени ключовата дума
- `search_keyword` — търси ключовата дума в текущата директория
- `analyze_file sofia_autonomous_rebuild.py` — бърз анализ на файл
- `config set net_allowed true` + `fetch https://example.com` — активирай нет и извлечи URL (внимавай!)
- `plugins` / `run my_plugin ...` — система за плъгини (по избор)

## Структура
- Конфигурация и памет: `~/.sofia/`
- Лог: `~/.sofia/sofia.log`
- Плъгини: `./plugins/*.py` с функция `run(args, ctx)`

## Бележки за безопасност
- Нет достъпът е **изключен по подразбиране**. Включвай го съзнателно.
- Търсенето е ограничено по размер (по подразбиране 512 KB) — променя се с `config set search_max_kb 1024`.
- `inject_code` изпълнява код в текущия процес — ползвай само доверен код.
