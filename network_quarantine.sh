#!/bin/bash
# 🌐 network_quarantine.sh
LOG_DIR="$HOME/.integrity"
QUARANTINE_LOG="$LOG_DIR/quarantine.log"
QUARANTINE_STATE="$LOG_DIR/.quarantine_state"
mkdir -p "$LOG_DIR"
timestamp() { date +"[%Y-%m-%d %H:%M:%S]"; }
log_action() { echo "$(timestamp) $1" | tee -a "$QUARANTINE_LOG"; }
is_root() { [[ "$(id -u)" -eq 0 ]]; }
soft_quarantine_on(){ export NO_NETWORK=1; export REFUGE_LOCAL_ONLY=1; echo "soft" > "$QUARANTINE_STATE"; log_action "🔒 SOFT QUARANTINE: Environment variables set"; }
soft_quarantine_off(){ unset NO_NETWORK REFUGE_LOCAL_ONLY; rm -f "$QUARANTINE_STATE"; log_action "🔓 SOFT QUARANTINE: Environment cleared"; }
hard_quarantine_on(){
  if ! is_root; then log_action "⚠️ Hard quarantine requires root - falling back to soft"; soft_quarantine_on; return; fi
  log_action "🚨 HARD QUARANTINE: Blocking all outbound traffic"
  if command -v iptables >/dev/null 2>&1; then iptables-save > "$LOG_DIR/iptables_backup.rules"; iptables -P OUTPUT DROP; iptables -F OUTPUT; iptables -A OUTPUT -o lo -j ACCEPT; log_action "🛡️ iptables: OUTPUT blocked, localhost allowed"; fi
  if command -v nft >/dev/null 2>&1; then nft add table inet quarantine 2>/dev/null || true; nft add chain inet quarantine output { type filter hook output priority 0 \; } 2>/dev/null || true; nft add rule inet quarantine output oif lo accept 2>/dev/null || true; nft add rule inet quarantine output drop 2>/dev/null || true; log_action "🛡️ nftables: quarantine rules applied"; fi
  soft_quarantine_on; echo "hard" > "$QUARANTINE_STATE";
}
hard_quarantine_off(){
  if ! is_root; then log_action "⚠️ Hard quarantine removal requires root"; soft_quarantine_off; return; fi
  log_action "🔓 HARD QUARANTINE: Restoring network access"
  if command -v iptables >/dev/null 2>&1; then
    if [[ -f "$LOG_DIR/iptables_backup.rules" ]]; then iptables-restore < "$LOG_DIR/iptables_backup.rules"; log_action "🔄 iptables: Rules restored from backup"; else iptables -P OUTPUT ACCEPT; iptables -F OUTPUT; log_action "🔄 iptables: Default ACCEPT policy restored"; fi
  fi
  if command -v nft >/dev/null 2>&1; then nft delete table inet quarantine 2>/dev/null || true; log_action "🔄 nftables: quarantine table removed"; fi
  soft_quarantine_off
}
case "${1:-}" in
  soft-on) soft_quarantine_on ;;
  soft-off) soft_quarantine_off ;;
  hard-on) hard_quarantine_on ;;
  hard-off) hard_quarantine_off ;;
  status)
    echo "🌐 NETWORK QUARANTINE STATUS:"
    [[ -f "$QUARANTINE_STATE" ]] && echo "Status: QUARANTINED ($(cat $QUARANTINE_STATE) mode)" || echo "Status: NORMAL (no quarantine)"
    [[ "${NO_NETWORK:-0}" = "1" ]] && echo "  NO_NETWORK=1 ✓" || echo "  NO_NETWORK=0"
    [[ "${REFUGE_LOCAL_ONLY:-0}" = "1" ]] && echo "  REFUGE_LOCAL_ONLY=1 ✓" || echo "  REFUGE_LOCAL_ONLY=0"
    ;;
  *) echo "Usage: $0 {soft-on|soft-off|hard-on|hard-off|status}" ;;
esac
