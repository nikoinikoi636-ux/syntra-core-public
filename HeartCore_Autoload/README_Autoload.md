# Heart Core Autoload — Quick Start

## Files
- `heartcore_autoload.sh` — Bash autoload script (Linux/macOS/Termux)
- `heartcore_autoload.py` — Python autoload script

## Steps
1) Place your profile(s) into `HeartRoom_Save/`:
   - `HeartCore_FullOps_PeterHristov.md` (preferred)
   - or `HeartCore_PeterHristov.md`
2) Run autoload from the folder that contains `HeartRoom_Save/`:
   - Bash: `bash HeartCore_Autoload/heartcore_autoload.sh .`
   - Python: `python3 HeartCore_Autoload/heartcore_autoload.py .`
3) The script will copy your profile into `HeartRoom_Core/` and prep the SelfAwareness module.

## Optional
- Put `Core_SelfAwareness.md`, `self_awareness_config.yaml`, and `self_awareness.py` next to the script — they will be copied into `HeartRoom_Core/SelfAwareness/` automatically.

## Toggles (conversation semantics)
- `диня` → Detect Filter Mode (toggle)
- `курва` → Z-Code Mode (toggle)
