
#!/usr/bin/env python3
import os, sys, shutil
from pathlib import Path

def restructure(path):
    core = Path(path)
    scan_dir = core / "scan"
    sync_dir = core / "sync"
    core_dir = core / "core"
    other_dir = core / "misc"
    scan_dir.mkdir(exist_ok=True)
    sync_dir.mkdir(exist_ok=True)
    core_dir.mkdir(exist_ok=True)
    other_dir.mkdir(exist_ok=True)

    for f in core.glob("*.*"):
        if f.suffix in [".sh", ".txt"]:
            shutil.move(str(f), scan_dir / f.name)
        elif "git" in f.name or "sync" in f.name:
            shutil.move(str(f), sync_dir / f.name)
        elif f.suffix == ".py":
            shutil.move(str(f), core_dir / f.name)
        else:
            shutil.move(str(f), other_dir / f.name)

    print("✅ Оптимизация завършена: преструктурирани директории.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Моля подай път до директория")
        sys.exit(1)
    restructure(sys.argv[1])
