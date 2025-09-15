import re, shutil
from pathlib import Path

PATTERNS = [
    (re.compile(r'AKIA[0-9A-Z]{16}'), 'AKIA[REDACTED]'),
    (re.compile(r'(?i)aws_secret_access_key\s*=\s*([A-Za-z0-9/+=]{30,})'), 'aws_secret_access_key=[REDACTED]'),
    (re.compile(r'gh[pousr]_[A-Za-z0-9]{30,}'), 'gh[REDACTED]_TOKEN'),
    (re.compile(r'(?i)authorization:\s*Bearer\s+[A-Za-z0-9\-\._~\+\/]+=*'), 'Authorization: Bearer [REDACTED]'),
    (re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----', re.S), '[REDACTED PRIVATE KEY]'),
    (re.compile(r'(?i)(password|passwd|pwd)\s*[:=]\s*[^,\s]{4,}'), r'\1=[REDACTED]'),
    (re.compile(r'(?i)(token|secret|api_key|apikey)\s*[:=]\s*[A-Za-z0-9\-_\.]{6,}'), r'\1=[REDACTED]'),
]

def sanitize_text(text:str)->str:
    out = text
    for rx, repl in PATTERNS:
        out = rx.sub(repl, out)
    return out

def sanitize(ev_dir: Path) -> Path:
    raw = ev_dir / "raw"
    sani = ev_dir / "sanitized"
    if sani.exists():
        shutil.rmtree(sani)
    sani.mkdir(parents=True, exist_ok=True)
    for f in raw.rglob("*"):
        if f.is_dir():
            continue
        rel = f.relative_to(raw)
        dest = sani / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = f.read_text(encoding="utf-8", errors="ignore")
            data = sanitize_text(data)
            dest.write_text(data, encoding="utf-8")
        except Exception:
            shutil.copy2(str(f), str(dest))
    return sani
