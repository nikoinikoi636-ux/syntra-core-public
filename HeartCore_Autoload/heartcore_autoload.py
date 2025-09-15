#!/usr/bin/env python3
"""heartcore_autoload.py — Autoload Heart Core + modules
Generated: 2025-08-15 21:27 UTC
Usage:
  python3 heartcore_autoload.py [root=.]

It will:
- Ensure HeartRoom_Core/ and Save/ exist
- Copy your HeartCore_* profile into HeartRoom_Core/
- Prepare SelfAwareness module folder
"""
import sys, os, shutil, pathlib

root = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path('.')
core_dir = root / 'HeartRoom_Core'
save_dir = root / 'HeartRoom_Save'
self_dir = core_dir / 'SelfAwareness'

core_dir.mkdir(parents=True, exist_ok=True)
save_dir.mkdir(parents=True, exist_ok=True)
self_dir.mkdir(parents=True, exist_ok=True)

fullops = save_dir / 'HeartCore_FullOps_PeterHristov.md'
basic = save_dir / 'HeartCore_PeterHristov.md'

if fullops.exists():
    profile = fullops
elif basic.exists():
    profile = basic
else:
    print(f'(!) No HeartCore profile in {save_dir}. Place your .md there.'); sys.exit(1)

shutil.copy2(profile, core_dir / profile.name)
print(f'✔ Heart Core loaded from: {profile}')
print(f'✔ Active Core path: {core_dir}')

# Copy Self-Awareness module files if present in current directory
for fname in ['Core_SelfAwareness.md', 'self_awareness_config.yaml', 'self_awareness.py']:
    src = pathlib.Path(fname)
    if src.exists():
        shutil.copy2(src, self_dir / fname)

print("→ Optional: run self-awareness logger:")
print('  cd HeartRoom_Core/SelfAwareness && python3 self_awareness.py observe "Fact 1" "Fact 2" "Fact 3" --intent "First micro-step" --micro "10 min" --tags precious')
print("Toggles: диня (detect) / курва (Z-Code)")
