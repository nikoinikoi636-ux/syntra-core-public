# Trinity Core — Lucifer Bridge (Apps Script)

## Какво е това?
Готов Google Apps Script за Google Sheets, който добавя меню **Trinity Core** и панел за въвеждане на L1–L5 (Lucifer‑Bridge). Има дневен „nudge“ тригер и седмичен преглед.

## Инсталация (2 мин):
1. Google Drive → New → **Google Sheets** → дайте име (напр. `Trinity Core Log`).
2. В листа: **Extensions → Apps Script**.
3. В `Code.gs` поставете съдържанието от файла `Code.gs` (заменете всичко).
4. Създайте нов HTML файл `Panel` и поставете съдържанието от `Panel.html`.
5. `Save` → Run `onOpen` (ще поиска разрешения) → обратно в Sheets.
6. Меню **Trinity Core**: `Install Triggers` (дневен 12:00 и седмичен неделя 18:00), `Run Lucifer Bridge` за панела.

> Забележка: тригерите не могат да показват UI; изпращат e‑mail (ако е наличен) или записват бележка в листа като напомняне.
