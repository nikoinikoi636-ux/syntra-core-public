#!/usr/bin/env bash
# 🔓 unsealer.sh — Controlled Unsealing w/ Integrity Gate

set -euo pipefail

INTEGRITY_DIR="$HOME/.integrity"
LOG_FILE="$INTEGRITY_DIR/unsealer.log"
ALLOWLIST="$INTEGRITY_DIR/allowlist.txt"
SEALED_DIR_DEFAULT="$HOME/sealed"
OUT_DIR_DEFAULT="$HOME/unsealed"
TMP_DIR="$(mktemp -d)"

mkdir -p "$INTEGRITY_DIR" "$OUT_DIR_DEFAULT"
touch "$LOG_FILE" "$ALLOWLIST"

timestamp(){ date +"[%Y-%m-%d %H:%M:%S]"; }
log(){ echo "$(timestamp) $*" | tee -a "$LOG_FILE" >&2; }

usage(){
  cat <<'USAGE'
Usage: unsealer.sh [--dir <sealed_dir> | --file <sealed_file>] [--out <out_dir>] [--dry-run] [--force]
                    [--passphrase-stdin] [--openssl] [--gpg]
USAGE
}

SEALED_PATH=""
SEALED_DIR="$SEALED_DIR_DEFAULT"
OUT_DIR="$OUT_DIR_DEFAULT"
DRY_RUN=0
FORCE=0
PP_STDIN=0
USE_GPG=0
USE_OPENSSL=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dir) SEALED_DIR="${2:-}"; shift 2;;
    --file) SEALED_PATH="${2:-}"; shift 2;;
    --out) OUT_DIR="${2:-}"; shift 2;;
    --dry-run) DRY_RUN=1; shift;;
    --force) FORCE=1; shift;;
    --passphrase-stdin) PP_STDIN=1; shift;;
    --gpg) USE_GPG=1; shift;;
    --openssl) USE_OPENSSL=1; shift;;
    -h|--help) usage; exit 0;;
    *) log "❌ Unknown arg: $1"; usage; exit 1;;
  esac
done

mkdir -p "$OUT_DIR"

# 0) Integrity Gate
if [[ $FORCE -eq 0 ]]; then
  if [[ ! -x ./integrity_checker.sh ]]; then
    log "❌ Missing ./integrity_checker.sh (or not executable)."; exit 2
  fi
  log "🔍 Running integrity_checker.sh…"
  if ! ./integrity_checker.sh >/dev/null 2>&1; then
    log "❌ integrity_checker.sh failed"; exit 3
  fi
  DIFF_FILE="$INTEGRITY_DIR/diff.log"
  if [[ -s "$DIFF_FILE" ]]; then
    log "🛑 Integrity changes detected. See: $DIFF_FILE"; exit 4
  fi
  log "✅ Integrity is clean (empty diff)."
else
  log "⚠️ FORCE mode: skipping integrity gate."
fi

# 1) Collect targets
targets=()
if [[ -n "$SEALED_PATH" ]]; then
  targets+=("$SEALED_PATH")
else
  if [[ ! -d "$SEALED_DIR" ]]; then log "❌ No directory: $SEALED_DIR"; exit 5; fi
  while IFS= read -r -d '' f; do targets+=("$f"); done < <(find "$SEALED_DIR" -type f \( -name '*.gpg' -o -name '*.asc' -o -name '*.enc' -o -name '*.seal' \) -print0)
fi
[[ ${#targets[@]} -gt 0 ]] || { log "ℹ️ No sealed files found."; exit 0; }

# 2) Allowlist check
allow_match(){
  local path="$1"
  [[ ! -s "$ALLOWLIST" ]] && return 1
  while IFS= read -r rule; do
    [[ -z "$rule" || "$rule" =~ ^# ]] && continue
    if [[ "$rule" == regex:* ]]; then
      local rx="${rule#regex:}"
      [[ "$path" =~ $rx ]] && return 0
    else
      shopt -s nocaseglob nullglob
      if [[ "$path" == $rule ]]; then shopt -u nocaseglob nullglob; return 0; fi
      shopt -u nocaseglob nullglob
    fi
  done < "$ALLOWLIST"
  return 1
}

# 3) Backend select
backend=""
if [[ $USE_GPG -eq 1 ]]; then backend="gpg"
elif [[ $USE_OPENSSL -eq 1 ]]; then backend="openssl"
elif command -v gpg >/dev/null 2>&1; then backend="gpg"
elif command -v openssl >/dev/null 2>&1; then backend="openssl"
else log "❌ Neither gpg nor openssl found."; exit 6; fi
log "🔐 Backend: $backend"

PASSPHRASE=""
if [[ $PP_STDIN -eq 1 ]]; then read -r PASSPHRASE; fi

unseal_one(){
  local src="$1"
  local rel out dstdir
  rel="$(realpath --relative-to="$(dirname "$SEALED_DIR")" "$src" 2>/dev/null || basename "$src")"
  out="${rel%.*}"
  dstdir="$OUT_DIR/$(dirname "$out")"
  mkdir -p "$dstdir"
  local outfile="$OUT_DIR/$out"

  if [[ $FORCE -eq 0 ]]; then
    if ! allow_match "$src"; then log "⛔ Deny (not in allowlist): $src"; return 10; fi
  fi

  if [[ $DRY_RUN -eq 1 ]]; then
    log "📝 DRY-RUN: $src → $outfile"; return 0
  fi

  case "$backend" in
    gpg)
      if [[ $PP_STDIN -eq 1 ]]; then
        if ! gpg --batch --yes --passphrase-fd 0 --output "$outfile" --decrypt "$src" <<<"$PASSPHRASE"; then
          log "❌ GPG decrypt fail: $src"; return 11; fi
      else
        if ! gpg --batch --yes --output "$outfile" --decrypt "$src"; then
          log "❌ GPG decrypt fail: $src"; return 11; fi
      fi
      ;;
    openssl)
      local cipher="aes-256-cbc"
      if [[ $PP_STDIN -eq 1 ]]; then
        if ! printf '%s' "$PASSPHRASE" | openssl enc -d -"${cipher}" -salt -pbkdf2 -in "$src" -out "$outfile" -pass stdin; then
          log "❌ OpenSSL decrypt fail: $src"; return 12; fi
      else
        read -rsp "🔑 OpenSSL passphrase for $src: " pass && echo
        if ! printf '%s' "$pass" | openssl enc -d -"${cipher}" -salt -pbkdf2 -in "$src" -out "$outfile" -pass stdin; then
          log "❌ OpenSSL decrypt fail: $src"; return 12; fi
      fi
      ;;
  esac

  if [[ -f "${src}.sha256" ]]; then
    local expected actual
    expected="$(cut -d' ' -f1 < "${src}.sha256")"
    actual="$(sha256sum "$outfile" | awk '{print $1}')"
    if [[ "$expected" != "$actual" ]]; then
      log "🛑 Hash mismatch: $outfile"; mv "$outfile" "$TMP_DIR/$(basename "$outfile").quarantine"; return 13
    fi
  fi

  if [[ -f "${src}.sig" && -d "$INTEGRITY_DIR/pubkeys" && "$backend" == "gpg" ]]; then
    gpg --batch --quiet --import "$INTEGRITY_DIR"/pubkeys/*.asc >/dev/null 2>&1 || true
    if ! gpg --batch --verify "${src}.sig" "$outfile" >/dev/null 2>&1; then
      log "🛑 Signature verification failed: $outfile"; mv "$outfile" "$TMP_DIR/$(basename "$outfile").bad-signature"; return 14
    fi
  fi

  log "✅ Unsealed: $src → $outfile"
  return 0
}

ERR=0
for f in "${targets[@]}"; do
  unseal_one "$f" || ERR=$((ERR+1))
done

if [[ $DRY_RUN -eq 1 ]]; then
  log "ℹ️ DRY-RUN done."
elif [[ $ERR -gt 0 ]]; then
  log "⚠️ Finished with warnings/errors: $ERR"
else
  log "🎉 All files unsealed successfully."
fi

rm -rf "$TMP_DIR"
exit 0
