#!/usr/bin/env python3
"""
filter_guard.py — lightweight prefilter for watcher/sync tools.

Exports:
  should_process(path: str) -> bool
  reason(path: str) -> str  (optional: why it was filtered)

- Ignores: temp/backup artifacts, compiled/cache, logs, zips/tars, large files (>10MB),
           timestamps dumps like "20250830-233149_*.py", duplicate/numbered copies "(1).py",
           venv/node_modules/.git, screenshots/downloads, etc.
- Allows: core *.py, *.json, *.sh in the HeartCore root tree by default.
- Optional whitelist file: state/watcher_whitelist.txt (one glob per line)
- Optional ignore file:    state/watcher_ignore.txt   (one glob per line)
"""
from __future__ import annotations
from pathlib import Path
import fnmatch, os

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "state"
WHITELIST = STATE / "watcher_whitelist.txt"
IGNORELIST = STATE / "watcher_ignore.txt"

MAX_BYTES = 10 * 1024 * 1024  # 10MB cap

# built-in ignores (globs or path parts)
IGNORE_PARTS = {
    ".git", "__pycache__", ".mypy_cache", ".pytest_cache", ".idea",
    "node_modules", "logs", "downloads", "bionet_collected_code",
    "sentinel-lab", "syntra-core-private_temp", ".sofia", ".sofia_v1",
}

IGNORE_GLOBS = [
    "*.pyc", "*.pyo", "*.log", "*.tmp", "*.swp", "*.bak", "*.old",
    "*.zip", "*.tar", "*.tar.gz", "*.rar", "*.7z",
    "*.png", "*.jpg", "*.jpeg", "*.gif", "*.mp4", "*.mov", "*.webm",
    "* (1).*", "* (2).*", "* (3).*",
    "20????????-??????_*",   # timestamped replicated dumps
    "*_dryrun_report.json",
    "*_heart_rules_*.json",
    "requirements*.txt", "requirements*.in",
    "test_*.py", "tests/**", "conftest.py",
]

ALLOW_GLOBS = [
    "*.py", "*.sh", "*.json", "*.md", "*.txt",
]

def _load_patterns(p: Path) -> list[str]:
    if not p.exists(): return []
    return [line.strip() for line in p.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")]

USER_ALLOW = _load_patterns(WHITELIST)
USER_IGNORE = _load_patterns(IGNORELIST)

def _match_any(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pat) for pat in patterns)

def reason(path: str) -> str:
    rel = str(Path(path))
    p = Path(path)
    # Size gate
    try:
        if p.is_file() and p.stat().st_size > MAX_BYTES:
            return f"too-large>{MAX_BYTES}B"
    except Exception:
        pass
    # User ignores
    if _match_any(rel, USER_IGNORE): return "user-ignore"
    # Built-in part filters
    for part in p.parts:
        if part in IGNORE_PARTS: return f"ignored-part:{part}"
    # Built-in glob ignores
    if _match_any(rel, IGNORE_GLOBS): return "ignored-glob"
    # Allowlist overrides
    if USER_ALLOW and not _match_any(rel, USER_ALLOW):
        return "not-in-user-allowlist"
    # If no user allowlist, fall back to allow globs
    if not _match_any(rel, ALLOW_GLOBS):
        return "not-in-allow-globs"
    return ""  # empty string => OK

def should_process(path: str) -> bool:
    return reason(path) == ""
