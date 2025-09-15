#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS="$ROOT/workspace"
OUTDIR="$WS/packs"
LOGDIR="$WS/logs"
MANIFEST="$ROOT/manifest.json"

DRY_RUN=false
ASSUME_YES=false

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
    --yes) ASSUME_YES=true ;;
    *) echo "Unknown arg: $arg" ; exit 2 ;;
  esac
done

if [[ ! -d "$OUTDIR" ]]; then
  echo "No packs found. Run ./install.sh first."
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "[!] jq not found; using basic parser. For best results: apt/brew install jq"
fi

ts() { date +"%Y-%m-%d_%H-%M-%S"; }

launch_cmd() {
  local packdir="$1"
  local entry="$2"
  local log="$3"

  local cmd=""
  case "$entry" in
    *.sh)  cmd="bash \"$packdir/$entry\"" ;;
    *.py)  cmd="python3 \"$packdir/$entry\"" ;;
    *.ps1) cmd="pwsh -File \"$packdir/$entry\"" ;;
    *.bat) cmd="cmd /c \"$packdir\\$entry\"" ;;
    Makefile) cmd="make -C \"$packdir\"" ;;
    *) cmd="" ;;
  esac
  echo "$cmd"
}

PACKS=()
while IFS= read -r -d '' d; do
  PACKS+=("$d")
done < <(find "$OUTDIR" -mindepth 1 -maxdepth 1 -type d -print0 | sort -z)

if [[ ${#PACKS[@]} -eq 0 ]]; then
  echo "No extracted packs in $OUTDIR"
  exit 0
fi

echo "[*] Discovered ${#PACKS[@]} pack(s)."

have_tmux=false
if command -v tmux >/dev/null 2>&1; then
  have_tmux=true
fi

SESSION="heartcore_$(ts)"
pane_idx=0

for pack in "${PACKS[@]}"; do
  packname="$(basename "$pack")"

  # Find a sensible entrypoint inside the pack folder
  # preference order: start*.sh/py, run*.sh/py, launch*.sh/py, main.py, Makefile
  entry=""
  while IFS= read -r f; do
    entry="$f"; break
  done < <(printf "%s\n" \
      "$(find "$pack" -maxdepth 3 -type f -iname 'start*.sh' -o -iname 'start*.py' -o -iname 'run*.sh' -o -iname 'run*.py' -o -iname 'launch*.sh' -o -iname 'launch*.py' -o -iname 'main.py' -o -name 'Makefile' 2>/dev/null | head -n 1)")

  if [[ -z "$entry" ]]; then
    echo "[?] No obvious entrypoint in $packname; skipping."
    continue
  fi

  rel="${entry#$pack/}"
  cmd="$(launch_cmd "$pack" "$rel" "$LOGDIR/$packname-$(ts).log")"

  if [[ -z "$cmd" ]]; then
    echo "[?] Unrecognized entrypoint type for $packname: $rel"
    continue
  fi

  echo "[>] $packname :: $rel"
  if $DRY_RUN; then
    echo "    CMD: $cmd"
    continue
  fi

  if ! $ASSUME_YES; then
    read -r -p "Start this module? [$packname] (y/N) " ans
    case "${ans,,}" in
      y|yes) ;;
      *) echo "    Skipped."; continue ;;
    esac
  fi

  mkdir -p "$LOGDIR"

  if $have_tmux; then
    if ! tmux has-session -t "$SESSION" 2>/dev/null; then
      tmux new-session -d -s "$SESSION" "$cmd 2>&1 | tee \"$LOGDIR/$packname-$(ts).log\""
    else
      tmux split-window -t "$SESSION" "$cmd 2>&1 | tee \"$LOGDIR/$packname-$(ts).log\""
      tmux select-layout -t "$SESSION" tiled >/dev/null
    fi
  else
    bash -lc "$cmd 2>&1 | tee \"$LOGDIR/$packname-$(ts).log\"" &
    disown || true
  fi
done

if $have_tmux && ! $DRY_RUN; then
  echo "[*] Attach to tmux session: tmux attach -t \"$SESSION\""
else
  echo "[*] Launched processes in background (no tmux). Check logs in $LOGDIR"
fi
