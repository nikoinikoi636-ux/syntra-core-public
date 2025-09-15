#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS="$ROOT/workspace"
ZIPDIR="$ROOT/packs/zips"
OUTDIR="$WS/packs"
LOGDIR="$WS/logs"
MANIFEST="$ROOT/manifest.json"

mkdir -p "$OUTDIR" "$LOGDIR"

echo "[*] Writing checksums..."
> "$WS/CHECKSUMS.sha256"
shopt -s nullglob
for z in "$ZIPDIR"/*.zip; do
  name="$(basename "$z")"
  echo "[*] Extracting: $name"
  target="$OUTDIR/${name%.zip}"
  rm -rf "$target"
  mkdir -p "$target"
  unzip -q "$z" -d "$target"
  sha256sum "$z" >> "$WS/CHECKSUMS.sha256"
done

echo "[*] Done. Packs extracted to: $OUTDIR"
echo "[*] Checksums saved to: $WS/CHECKSUMS.sha256"
