# sitecustomize.py (fixed proxy wrapper)
import os, io, json, time, hashlib, builtins, inspect, threading
from datetime import datetime

LOG_DIR = os.environ.get("OBSERVER_LOG_DIR", os.path.join(os.getcwd(), "observer_logs"))
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FN = os.path.join(LOG_DIR, f"observer_{int(time.time())}.jsonl")
_lock = threading.Lock()

_orig_open = builtins.open

def _caller():
    for f in inspect.stack()[2:]:
        fn = f.filename
        if "sitecustomize.py" not in fn:
            return {"file": fn, "func": f.function, "line": f.lineno}
    return {"file": None, "func": None, "line": None}

def _log(event):
    event["ts"] = datetime.utcnow().isoformat() + "Z"
    with _lock:
        with _orig_open(LOG_FN, "a", encoding="utf-8") as lf:
            lf.write(json.dumps(event, ensure_ascii=False) + "\n")

class FileProxy:
    def __init__(self, f, path, mode):
        self._f = f
        self._path = path
        self._mode = mode
    def read(self, *a, **kw):
        data = self._f.read(*a, **kw)
        try: size = len(data)
        except Exception: size = None
        _log({"type":"read", "path":self._path, "mode":self._mode, "caller":_caller(), "size":size})
        return data
    def write(self, b, *a, **kw):
        n = self._f.write(b, *a, **kw)
        _log({"type":"write", "path":self._path, "mode":self._mode, "caller":_caller(), "size":n})
        return n
    def __getattr__(self, x):
        return getattr(self._f, x)
    def __iter__(self):
        return iter(self._f)
    def __enter__(self):
        return self
    def __exit__(self, *exc):
        return self._f.__exit__(*exc)

def _hash_if_small(path):
    try:
        if os.path.isfile(path) and os.path.getsize(path) <= 1_000_000:
            with _orig_open(path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        pass
    return None

def _observed_open(path, mode="r", *a, **kw):
    caller = _caller()
    h = _hash_if_small(path) if "r" in mode and "w" not in mode and "a" not in mode else None
    _log({"type": "open", "path": str(path), "mode": mode, "caller": caller, "sha256": h})
    f = _orig_open(path, mode, *a, **kw)
    # Wrap for both text and binary to log read/write sizes
    return FileProxy(f, str(path), mode)

builtins.open = _observed_open
