import time
from pathlib import Path
from .collectors import collect
from .normalizer import normalize
from .sanitizer import sanitize
from .analyzer import analyze

def watch(base: Path, paths, rules_path: Path, interval_sec: int = 600, max_size_mb: int = 5):
    print(f"[watch] interval={interval_sec}s; max_size_mb={max_size_mb}")
    while True:
        try:
            ev = collect(paths, base, max_size_mb=max_size_mb)
            normalize(ev)
            sanitize(ev)
            analyze(ev, rules_path)
            print(f"[watch] cycle OK: {ev}")
        except Exception as e:
            print(f"[watch] error: {e}")
        time.sleep(interval_sec)
