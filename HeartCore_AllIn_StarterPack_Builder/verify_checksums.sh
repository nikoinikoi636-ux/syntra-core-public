#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS="$ROOT/workspace"
cd "$WS"

if [[ ! -f CHECKSUMS.sha256 ]]; then
  echo "No CHECKSUMS.sha256 found. Run ./install.sh first."
  exit 1
fi

sha256sum -c CHECKSUMS.sha256
