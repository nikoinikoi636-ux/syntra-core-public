import re, json, datetime
from pathlib import Path

LEVEL_MAP = {
    "CRITICAL":"CRITICAL","ALERT":"ALERT","EMERGENCY":"EMERGENCY",
    "ERROR":"ERROR","ERR":"ERROR","FAIL":"ERROR","FAILED":"ERROR","FATAL":"ERROR",
    "WARN":"WARN","WARNING":"WARN","DENIED":"WARN","UNAUTHORIZED":"WARN",
    "INFO":"INFO","NOTICE":"INFO",
    "DEBUG":"DEBUG","TRACE":"DEBUG"
}
LEVEL_KEYS = sorted(LEVEL_MAP.keys(), key=len, reverse=True)

TS_PATTERNS = [
    (re.compile(r'(?P<ts>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+\-]\d{2}:?\d{2})?)'), "%iso%"),
    (re.compile(r'(?P<ts>[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})'), "%b %d %H:%M:%S"),
    (re.compile(r'\[(?P<ts>\d{1,2}/[A-Z][a-z]{2}/\d{4}:\d{2}:\d{2}:\d{2}\s+[+\-]\d{4})\]'), "%d/%b/%Y:%H:%M:%S %z"),
]

def infer_level(line:str)->str:
    up = line.upper()
    for k in LEVEL_KEYS:
        if k in up:
            return LEVEL_MAP[k]
    return "INFO"

def parse_ts(line:str, file_mtime:float):
    for rx, fmt in TS_PATTERNS:
        m = rx.search(line)
        if not m: 
            continue
        ts = m.group("ts")
        if fmt == "%iso%":
            if ts.endswith("Z"):
                return ts
            if re.match(r'.*[+\-]\d{2}\d{2}$', ts):
                ts = ts[:-2] + ":" + ts[-2:]
            return ts
        else:
            try:
                year = datetime.datetime.utcnow().year
                dt = datetime.datetime.strptime(ts, fmt)
                dt = dt.replace(year=year)
                return dt.isoformat() + "Z"
            except Exception:
                continue
    return datetime.datetime.utcfromtimestamp(file_mtime).isoformat() + "Z"

def normalize(ev_dir: Path) -> Path:
    raw_dir = ev_dir / "raw"
    out_jsonl = ev_dir / "normalized.jsonl"
    count = 0
    with out_jsonl.open("w", encoding="utf-8") as out:
        for f in raw_dir.rglob("*"):
            if f.is_file():
                try:
                    data = f.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                mtime = f.stat().st_mtime
                source = str(f).replace(str(ev_dir), "").lstrip("/")
                for idx, line in enumerate(data.splitlines()):
                    line_stripped = line.strip()
                    if not line_stripped:
                        continue
                    rec = {
                        "ts": parse_ts(line_stripped, mtime),
                        "level": infer_level(line_stripped),
                        "source": source,
                        "lineno": idx + 1,
                        "msg": line_stripped
                    }
                    out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    count += 1
    return out_jsonl
