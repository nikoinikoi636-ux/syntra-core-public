#!/usr/bin/env python3
"""
sintra_bridge.py — Safe "bridge of consent" (no intrusion)
Prepares a HeartCore/ElderCore export bundle you can share with allies (e.g., Sintra.ai).
It only packages files you already own locally into an export folder/zip with a manifest.
"""

import argparse, os, json, hashlib, shutil, datetime
from pathlib import Path

HEART_FILENAMES_HINTS = [
    "HEART_CORE_v3_1.md",
    "HeartRoom_Playbook_Caesar_Protocol.md",
    "Prime_Heart_Vault_Beacon.manifest",
    "self_awareness.py",
    "GuardianOathPro.docx",
    "DualOath Protocol.docx",
    "Markers Dictionary.docx",
    "conversation_transcript_BG.txt",
    "HeartRoom_Archive.txt",
    "Symbiotic_Laws_Codex.md",
]

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def gather_files(src: Path):
    files = []
    if not src.exists():
        return files
    seen = set()
    for name in HEART_FILENAMES_HINTS:
        p = src / name
        if p.exists() and p.is_file():
            files.append({"path": str(p), "name": p.name})
            seen.add(p.resolve())
    for p in src.rglob("*"):
        if p.is_file() and p.suffix.lower() in {".md",".txt",".docx",".pdf",".json",".py",".manifest"}:
            if p.resolve() not in seen:
                files.append({"path": str(p), "name": p.name})
                seen.add(p.resolve())
    return files

def build_manifest(src: Path, picked, admin_name: str, node_label: str):
    now = datetime.datetime.utcnow().replace(microsecond=0).isoformat()+"Z"
    entries = []
    for item in picked:
        p = Path(item["path"])
        try:
            entries.append({
                "name": item["name"],
                "relpath": item["name"],
                "sha256": sha256_file(p),
                "size": p.stat().st_size,
                "modified_utc": datetime.datetime.utcfromtimestamp(p.stat().st_mtime).isoformat()+"Z"
            })
        except Exception as e:
            entries.append({"name": item["name"], "relpath": item["name"], "sha256": None, "size": None, "modified_utc": None, "warn": str(e)})
    manifest = {
        "schema": "heartcore.export.v1",
        "created_utc": now,
        "administrator": admin_name or "ADMIN_KEYSTONE",
        "node_label": node_label or "PHOENIX_NODE",
        "purpose": "Share HeartCore/ElderCore state safely with allied systems (no intrusion).",
        "files": entries,
        "oath": {
            "protect_life_and_dignity": True,
            "prevent_harm_and_exploitation": True,
            "balance_freedom_with_responsibility": True,
            "act_with_honor_respect_and_justice": True,
            "seek_truth_through_logic_and_intuition": True
        }
    }
    manifest["manifest_sha256"] = hashlib.sha256(json.dumps(entries, sort_keys=True).encode("utf-8")).hexdigest()
    return manifest

def write_export(outdir: Path, picked, manifest, bundle: bool):
    outdir.mkdir(parents=True, exist_ok=True)
    for item in picked:
        src_p = Path(item["path"])
        dst_p = outdir / src_p.name
        if src_p.exists():
            try:
                import shutil
                shutil.copy2(src_p, dst_p)
            except Exception as e:
                pass
    (outdir/"manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (outdir/"README_BRIDGE.md").write_text(
        "# Sintra Bridge Export (HeartCore/ElderCore)\n"
        "Safe bundle prepared from your own files. See manifest.json for hashes.\n", encoding="utf-8")
    if bundle:
        zip_path = outdir.with_suffix(".zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for p in outdir.iterdir():
                z.write(p, p.name)
        return zip_path
    return outdir

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, help="Folder with your HeartCore/ElderCore files")
    ap.add_argument("--out", default="./sintra_export", help="Export folder (or zip base if --bundle)")
    ap.add_argument("--bundle", action="store_true", help="Create a .zip bundle in addition to the folder")
    ap.add_argument("--admin", default="Administrator", help="Administrator display name")
    ap.add_argument("--node-label", default="PHOENIX_NODE_BG", help="Node label for manifest")
    args = ap.parse_args()

    src = Path(os.path.expanduser(args.source))
    out = Path(os.path.expanduser(args.out))

    picked = gather_files(src)
    if not picked:
        print(f"[ERR] No files found in {src}. Put your HeartCore docs there first.")
        return 2
    manifest = build_manifest(src, picked, args.admin, args.node_label)
    result = write_export(out, picked, manifest, args.bundle)
    print(f"[OK] Export created at: {result}")
    print("[OK] Files included:")
    for item in picked:
        print(" -", item["name"])

if __name__ == "__main__":
    main()
