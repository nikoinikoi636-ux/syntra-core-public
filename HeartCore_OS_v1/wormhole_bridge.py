#!/usr/bin/env python3
# file: wormhole_bridge.py
import os, sys, hashlib, json, tarfile
from pathlib import Path
from datetime import datetime
try:
    import requests
except Exception:
    requests = None

ARCHIVE_NAME = "singularity.tar.gz"
REMOTE_ENDPOINT = "https://example.com/upload"  # <-- смени с твоя
SECRET_KEY = "CHANGE_ME"                        # <-- смени с твоя

def sha256_file(p: Path):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def compress_dir(path: Path, archive_name=ARCHIVE_NAME):
    with tarfile.open(archive_name, "w:gz") as tar:
        tar.add(path, arcname=path.name)
    return Path(archive_name)

def upload_file(f: Path):
    if requests is None:
        print("requests не е наличен. Инсталирай с: pip install requests")
        return 0, "requests missing"
    files = {"file": open(f, "rb")}
    headers = {"X-Auth": SECRET_KEY}
    r = requests.post(REMOTE_ENDPOINT, files=files, headers=headers, timeout=60)
    return r.status_code, r.text

def main():
    if len(sys.argv) < 2:
        print("Usage: wormhole_bridge.py <directory> [--upload]")
        sys.exit(1)
    root = Path(sys.argv[1])
    do_upload = "--upload" in sys.argv[2:]
    if not root.exists():
        print("No such directory:", root)
        sys.exit(1)

    print(f"🌀 Creating singularity archive from: {root}")
    arc = compress_dir(root)
    checksum = sha256_file(arc)
    meta = {
        "created": datetime.utcnow().isoformat() + "Z",
        "file": str(arc),
        "sha256": checksum,
        "size": arc.stat().st_size
    }
    print(json.dumps(meta, indent=2, ensure_ascii=False))

    if do_upload:
        print("🚀 Uploading to wormhole endpoint...")
        code, text = upload_file(arc)
        print("Response:", code, text)

if __name__ == "__main__":
    main()
