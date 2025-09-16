from pathlib import Path
from fnmatch import fnmatch
import os

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "state"
WHITELIST = STATE / "watcher_whitelist.txt"
IGNORE = STATE / "watcher_ignore.txt"

def _load_patterns(path):
    pats=[]
    if path.exists():
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            s=line.strip()
            if not s or s.startswith("#"): continue
            pats.append(s)
    return pats

_WL = _load_patterns(WHITELIST)
_IG = _load_patterns(IGNORE)

def _match_any(rel:str, pats):
    return any(fnmatch(rel, p) for p in pats)

def should_process(rel_path:str)->bool:
    # normalize to "./..." relative form
    rp = rel_path.replace("\\","/")
    if not rp.startswith("./"):
        if rp.startswith(str(ROOT)):  # absolute -> make relative
            rp = "./" + str(Path(rp).resolve().relative_to(ROOT)).replace("\\","/")
        else:
            rp = "./" + rp.lstrip("/")
    # ignore wins first
    if _match_any(rp, _IG):
        return False
    # whitelist required; if empty, allow all .py by default
    if _WL:
        return _match_any(rp, _WL)
    return rp.endswith(".py")

def reason(rel_path:str)->str:
    rp = rel_path.replace("\\","/")
    if _match_any(rp, _IG):
        return "ignored"
    if _WL and not _match_any(rp, _WL):
        return "not-whitelisted"
    return ""
