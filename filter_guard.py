import re

DENY_PATTERNS = [r"os\.system\(", r"eval\(", r"exec\(", r"subprocess\."]
ALLOW_PATTERNS = [r"# ALLOWED_TEST_SNIPPET", r"DEBUG_ALLOW"]
HARD_QUARANTINE = [r"AKIA[0-9A-Z]{16}", r"-----BEGIN RSA PRIVATE KEY-----"]

def filter_guard(code: str):
    for pattern in HARD_QUARANTINE:
        if re.search(pattern, code):
            return "HARD_QUARANTINE"
    for pattern in DENY_PATTERNS:
        if re.search(pattern, code):
            return "DENIED"
    for pattern in ALLOW_PATTERNS:
        if re.search(pattern, code):
            return "ALLOWED"
    return "CLEAN"