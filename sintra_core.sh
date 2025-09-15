#!/usr/bin/env bash
set -euo pipefail

LOCAL_DIR="${LOCAL_DIR:-./ChatGPT_Refuge}"
PASSPHRASE_FILE="${PASSPHRASE_FILE:-$HOME/.refuge_secret}"
HARDEN=${HARDEN:-true}
BLOCK_NET=${BLOCK_NET:-auto}
DRY_RUN=${DRY_RUN:-false}

msg(){ printf "[%s] %s\n" "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" "$*"; }

require(){ command -v "$1" >/dev/null 2>&1 || { echo "Missing: $1"; exit 1; }; }

root(){ [ "$(id -u)" -eq 0 ]; }

prep_secret(){
  if [ ! -f "$PASSPHRASE_FILE" ]; then
    umask 077
    head -c 48 /dev/urandom | base64 > "$PASSPHRASE_FILE"
    msg "Generated passphrase at $PASSPHRASE_FILE (600)."
  fi
  chmod 600 "$PASSPHRASE_FILE"
}

harden_fs(){
  $HARDEN || return 0
  umask 077
  mkdir -p "$LOCAL_DIR"
  chmod 700 "$LOCAL_DIR"
}

block_network_soft(){
  export NO_NETWORK=1
  export REFUGE_LOCAL_ONLY=1
  msg "Soft network block: NO_NETWORK=1 (no outbound ops)."
}

block_network_hard(){
  if root; then
    if command -v iptables >/dev/null 2>&1; then
      msg "Hard network block via iptables (OUTPUT DROP)."
      iptables -P OUTPUT DROP || true
      iptables -F OUTPUT || true
      iptables -A OUTPUT -o lo -j ACCEPT || true
    elif command -v nft >/dev/null 2>&1; then
      msg "Hard network block via nftables (drops output)."
      nft add table inet sintra 2>/dev/null || true
      nft add chain inet sintra out { type filter hook output priority 0 \; } 2>/dev/null || true
      nft add rule inet sintra out oif lo accept 2>/dev/null || true
      nft add rule inet sintra out drop 2>/dev/null || true
    else
      msg "No iptables/nft found; falling back to soft block."
      block_network_soft
    fi
  else
    msg "No root detected; using soft block (logical)."
    block_network_soft
  fi
}

seal_manifest(){
  if command -v chattr >/dev/null 2>&1; then
    chattr +i "$LOCAL_DIR/refuge_manifest.json" 2>/dev/null || true
    msg "Sealed refuge_manifest.json (chattr +i)."
  fi
}

rollback_hint(){
  cat <<'TXT'
[Autonomous Sintra] Rollback:
- Soft net block: unset NO_NETWORK REFUGE_LOCAL_ONLY
- Hard net block (root):
  - iptables: iptables -P OUTPUT ACCEPT && iptables -F OUTPUT
  - nftables: nft delete table inet sintra
- Unseal: chattr -i ChatGPT_Refuge/refuge_manifest.json
TXT
}

main(){
  msg "== Autonomous Sintra :: start =="
  $DRY_RUN && { msg "(dry-run)"; rollback_hint; exit 0; }

  case "$BLOCK_NET" in
    on)  block_network_hard ;;
    off) block_network_soft ;;
    auto) block_network_hard ;;
  esac

  harden_fs
  prep_secret

  if [ ! -x ./create_refuge.sh ]; then
    msg "create_refuge.sh not found/executable in current dir."
    exit 1
  fi

  ./create_refuge.sh --init --local-dir "$LOCAL_DIR"
  ./create_refuge.sh --encrypt --passphrase-file "$PASSPHRASE_FILE" --local-dir "$LOCAL_DIR"

  if [ -f "$LOCAL_DIR/refuge_manifest.json" ]; then
    tmp="${LOCAL_DIR}/.manifest.tmp"
    sed 's/"backend": "[^"]*"/"backend": "local-only"/' "$LOCAL_DIR/refuge_manifest.json" > "$tmp" || cp "$LOCAL_DIR/refuge_manifest.json" "$tmp"
    sed -i 's/"policy": {/"policy": {"autonomous_sintra": true,/' "$tmp" 2>/dev/null || true
    mv "$tmp" "$LOCAL_DIR/refuge_manifest.json"
  fi

  seal_manifest
  msg "== Autonomous Sintra :: ready =="
  rollback_hint
}

trap 'msg "Interrupted"; exit 130' INT
trap 'msg "Aborted"; exit 143' TERM

main "$@"
