
# Sofia Sentinel v1.0 — Unified Orchestrator (BG)

## Старт
```bash
python3 sofia_sentinel_v1_0.py
```

## Основни модули
- **Advisor**: директни препоръки
- **Roles**: приоритети и статуси
- **Memory**: JSON с auto-save
- **BioNet**: организъм (registry, mailboxes, bones/backups, quarantine, immune scan)
- **Titan**: multi-baseline, snapshots, honeyfiles/canary, verify/restore/quarantine, failsafe seal/purge
- **Phase 1**: multi-baseline mgmt, selective purge (по префикс), авто snapshot след purge, heartbeat с auto-verify+honey, inject_code gate, fetch whitelist, профили + rollback

## Команди (вътре в приложението)
```
help
status
think <текст>
advise <тема>

memory save|load|clear
roles
role info|enable|disable|set-priority <име> [стойност]

config set <ключ> <стойност>
config profile apply <strict|balanced|creative>
config rollback

bionet init
bionet scan
bionet graph
bionet signal <topic> <message>
node inbox <relpath>

titan baseline list
titan baseline set <label>
titan baseline keep <N>
titan clone [N]
titan snapshot
titan verify
titan honey init
titan honey check
titan restore <rel>
titan failsafe seal
titan failsafe purge [path_prefix]

heartbeat start
heartbeat stop
heartbeat status
heartbeat interval <сек>

fetch <url>
inject_code
```

## Типичен флоу
```
status
bionet init
titan clone
titan failsafe seal
heartbeat start
titan verify
# при нужда:
titan failsafe purge
```
