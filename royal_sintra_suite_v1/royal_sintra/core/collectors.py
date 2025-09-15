from pathlib import Path
from typing import List
import os, shutil, subprocess
from .utils import ts, sha256_file

DEFAULT_EXCLUDES = [".git", ".bionet", ".titan", "__pycache__", "node_modules"]

def collect(paths: List[str], base: Path, max_size_mb: int = 5) -> Path:
    ev_dir = base / "evidence" / ts().replace(":","").replace(".","")
    raw_dir = ev_dir / "raw"
    meta_dir = ev_dir / "meta"
    raw_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)

    (meta_dir / "environment.txt").write_text(
        f"timestamp_utc={ts()}\n"
        f"pwd={os.getcwd()}\n"
    , encoding="utf-8")

    collected = []
    max_bytes = max_size_mb * 1024 * 1024

    def should_skip(p: Path) -> bool:
        parts = p.parts
        return any(x in parts for x in DEFAULT_EXCLUDES)

    for p in paths:
        pth = Path(p).expanduser()
        if pth.is_file():
            if pth.stat().st_size <= max_bytes and not should_skip(pth):
                dest = raw_dir / "abs" / pth.as_posix().lstrip("/")
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(pth), str(dest))
                collected.append(str(pth))
        elif pth.exists():
            for f in pth.rglob("*"):
                if f.is_file() and f.stat().st_size <= max_bytes and not should_skip(f):
                    dest = raw_dir / ("abs" if f.is_absolute() else "rel") / f.as_posix().lstrip("/")
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        shutil.copy2(str(f), str(dest))
                        collected.append(str(f))
                    except Exception:
                        pass

    (meta_dir / "collected_files.txt").write_text("\n".join(collected), encoding="utf-8")

    # Hashes
    sha_path = meta_dir / "sha256sums.txt"
    with sha_path.open("w", encoding="utf-8") as out:
        for f in raw_dir.rglob("*"):
            if f.is_file():
                try:
                    out.write(f"{sha256_file(f)}  {f.relative_to(raw_dir)}\n")
                except Exception:
                    continue

    return ev_dir
