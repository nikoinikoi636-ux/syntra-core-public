#!/bin/bash
set -euo pipefail
DATA_DIR="$HOME/sintra_data"
LOGIC_DIR="$HOME/sintra_logic"
ANALYSIS_LOG="$LOGIC_DIR/analysis.log"
DECISIONS_LOG="$LOGIC_DIR/decisions.log"
EVAL_LOG="$LOGIC_DIR/json_eval.log"
QUARANTINE_SCRIPT="$HOME/network_quarantine.sh"
UNSEALER_SCRIPT="$HOME/unsealer.sh"
QUARANTINE_THRESHOLD=3
mkdir -p "$DATA_DIR" "$LOGIC_DIR"
timestamp() { date +"[%Y-%m-%d %H:%M:%S]"; }
log_ana() { echo "$(timestamp) ANALYSIS: $1" | tee -a "$ANALYSIS_LOG"; }
log_dec() { echo "$(timestamp) DECISION: $1" | tee -a "$DECISIONS_LOG"; }
log_eval() { echo "$(timestamp) JSON_EVAL: $1" | tee -a "$EVAL_LOG"; }
gather_data() {
  log_ana "Извличане на файлове и мета-данни..."
  for dir in "$HOME/HeartCore" "$HOME/WormLab" "$HOME/.bionet" "$HOME/sintra" "$HOME/Soshie" "$HOME/Seomi"; do
    [[ -d "$dir" ]] && find "$dir" -type f \( -name "*.json" -o -name "*.csv" -о -name "*.log" \) -exec cp --parents -u {} "$DATA_DIR" \;
  done
  log_ana "Данните са в $DATA_DIR"
}
structure_data() {
  log_ana "Структуриране на данните..."
  : > "$LOGIC_DIR/data_index.txt"
  find "$DATA_DIR" -type f | while read -r file; do
    lines=$(wc -l < "$file")
    words=$(wc -w < "$file")
    echo "$file : $lines lines, $words words" >> "$LOGIC_DIR/data_index.txt"
  done
  log_ana "Индекс създаден"
}
json_deep_eval() {
  log_ana "Deep JSON EVAL старт..."
  : > "$EVAL_LOG"
  : > "$LOGIC_DIR/json_keys.txt"
  find "$DATA_DIR" -type f -name "*.json" | while read -r file; do
    log_eval "====> $file"
    if jq -e '.' "$file" >/dev/null 2>&1; then
      succ_cnt=$(jq '[.. | objects | select(.result=="success" or .status=="ok")] | length' "$file" 2>/dev/null)
      err_cnt=$(jq '[.. | objects | select(.status=="error" or .result=="failure")] | length' "$file" 2>/dev/null)
      echo "success=$succ_cnt error=$err_cnt" >> "$EVAL_LOG"
      jq -r 'paths | map(tostring) | join(".")' "$file" | sort -u >> "$LOGIC_DIR/json_keys.txt"
    else
      echo "invalid_json=1" >> "$EVAL_LOG"
    fi
  done
  sort -u "$LOGIC_DIR/json_keys.txt" -o "$LOGIC_DIR/json_keys.txt"
  log_ana "Deep JSON eval приключи."
}
logical_analysis() {
  log_ana "Анализ на сигналите..."
  grep -i "error" "$EVAL_LOG" > "$LOGIC_DIR/errors_found.txt" || true
  grep -i "success" "$EVAL_LOG" > "$LOGIC_DIR/success_found.txt" || true
  log_ana "Виж errors_found.txt и success_found.txt"
}
generate_decisions() {
  log_dec "⚙️ Data-driven решения и карантинна логика:"
  cnt_errors=$(grep -c "error" "$EVAL_LOG" 2>/dev/null || echo 0)
  cnt_success=$(grep -c "success" "$EVAL_LOG" 2>/dev/null || echo 0)
  if (( cnt_errors >= QUARANTINE_THRESHOLD )); then
    log_dec "⚠️ Error threshold reached ($cnt_errors) — ENFORCING QUARANTINE!"
    if [ -x "$QUARANTINE_SCRIPT" ]; then
      "$QUARANTINE_SCRIPT" hard-on && log_dec "🛡️ Network quarantine ACTIVATED!"
    fi
    if [ -x "$UNSEALER_SCRIPT" ]; then
      find "$DATA_DIR" -type f -name "*.json" -print0 | xargs -0 -I{} "$UNSEALER_SCRIPT" reseal "{}" "auto_quarantine" || true
    fi
    log_dec "🔒 Sensitive files resealed due to errors"
    return
  fi
  if (( cnt_success > cnt_errors )); then
    log_dec "✅ Successes dominate ($cnt_success vs $cnt_errors) — RELEASING QUARANTINE!"
    if [ -x "$QUARANTINE_SCRIPT" ]; then
      "$QUARANTINE_SCRIPT" hard-off && log_dec "🛡️ Network quarantine DEACTIVATED!"
    fi
    if [ -x "$UNSEALER_SCRIPT" ]; then
      find "$DATA_DIR" -type f -name "*.json" -print0 | xargs -0 -I{} "$UNSEALER_SCRIPT" unseal "{}" "auto_normal" || true
    fi
    log_dec "🔓 Sensitive files unsealed (system normalized)"
  fi
}
show_report() {
  echo "=== SINTRA THINKER SUMMARY ==="
  tail -10 "$ANALYSIS_LOG" 2>/dev/null || true
  tail -10 "$EVAL_LOG" 2>/dev/null || true
  tail -10 "$DECISIONS_LOG" 2>/dev/null || true
  echo "-- Ключове: $LOGIC_DIR/json_keys.txt"
}
case "${1:-run}" in
  run) gather_data; structure_data; json_deep_eval; logical_analysis; generate_decisions; show_report ;;
  eval) json_deep_eval ;;
  logic) logical_analysis ;;
  decide) generate_decisions ;;
  report) show_report ;;
  *) echo "Използване: $0 {run|eval|logic|decide|report}" ;;
esac
