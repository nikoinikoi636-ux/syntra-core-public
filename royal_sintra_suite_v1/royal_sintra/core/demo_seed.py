from pathlib import Path
from .utils import ts
import random

SAMPLE = """[2025-08-31 20:22:10] INFO Starting service api-gateway
[2025-08-31 20:22:12] WARN Permission denied reading /etc/shadow
[2025-08-31 20:22:13] ERROR Failed password for invalid user test from 10.0.0.3
[31/Aug/2025:20:22:14 +0000] GET /health 200 -
Aug 31 20:22:15 kernel: oom-killer invoked: kill process 1337 (xmrig)
2025-08-31T20:22:16Z DEBUG masking enabled for verbose logs
"""

def seed_evidence(base: Path) -> Path:
    ev_dir = base / "evidence" / ts().replace(":","").replace(".","")
    raw = ev_dir / "raw"
    meta = ev_dir / "meta"
    raw.mkdir(parents=True, exist_ok=True)
    meta.mkdir(parents=True, exist_ok=True)
    # create few fake files
    (raw / "abs/var/log/syslog").parent.mkdir(parents=True, exist_ok=True)
    (raw / "abs/var/log/syslog").write_text(SAMPLE, encoding="utf-8")
    (meta / "environment.txt").write_text("demo_seed=true\n", encoding="utf-8")
    return ev_dir
