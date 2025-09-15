#!/usr/bin/env bash
set -uo pipefail
TS="$(date +'%Y-%m-%d_%H-%M-%S')"
OUT="${HOME}/TrinityAudit_${TS}"
mkdir -p "$OUT"

log() { printf "[*] %s\n" "$*" | tee -a "$OUT/_audit.log"; }
have() { command -v "$1" >/dev/null 2>&1; }

log "Trinity Core Audit start @ ${TS}"
log "User: $(id -u -n 2>/dev/null || echo $USER)  UID: $(id -u)  Host: $(uname -a)"

## 0) Среда и базова инфо
{
  echo "=== ENV ==="
  env | sort
  echo
  echo "=== PATH ==="
  echo "$PATH" | tr ':' '\n'
  echo
  echo "=== Shell files ==="
  for f in ~/.bashrc ~/.profile ~/.zshrc ~/.termux/termux.properties; do [ -f "$f" ] && echo "-- $f" && sed -n '1,200p' "$f"; done
} > "$OUT/00_env_and_shell.txt"

## 1) Процеси (CPU/MEM топ, пълни командни линии)
if have ps; then
  ps auxww > "$OUT/10_process_full.txt"
  ps aux --sort=-%cpu | head -n 30 > "$OUT/11_top_cpu.txt"
  ps aux --sort=-%mem | head -n 30 > "$OUT/12_top_mem.txt"
fi
if have top; then top -b -n1 > "$OUT/13_top_snapshot.txt" 2>/dev/null || true; fi

## 2) Стартиращи задачи / демони
{
  echo "=== Cron ==="
  (crontab -l 2>/dev/null || echo "no user crontab")
  echo
  echo "=== Systemd user (ако има) ==="
  if have systemctl; then systemctl --user list-timers --all 2>/dev/null || true; systemctl --user list-units --type=service --state=running 2>/dev/null || true; fi
  echo
  echo "=== Termux:boot/служби ==="
  [ -d ~/.termux/boot ] && { echo "~/.termux/boot:"; ls -la ~/.termux/boot; sed -n '1,200p' ~/.termux/boot/* 2>/dev/null; }
  [ -d ~/../usr/var/service ] && { echo "termux-services:"; ls -la ~/../usr/var/service; }
} > "$OUT/20_startup.txt"

## 3) Мрежа: слушащи портове и активни връзки
if have ss; then
  ss -tulpn > "$OUT/30_listen_ports.txt" 2>/dev/null || true
  ss -tunap > "$OUT/31_active_conns.txt" 2>/dev/null || true
elif have netstat; then
  netstat -tulpn > "$OUT/30_listen_ports.txt" 2>/dev/null || true
  netstat -tunap > "$OUT/31_active_conns.txt" 2>/dev/null || true
fi
# DNS, маршрути
{
  echo "=== DNS ==="
  [ -f /etc/resolv.conf ] && cat /etc/resolv.conf
  echo
  echo "=== Routes ==="
  (ip route 2>/dev/null || route -n 2>/dev/null || true)
} > "$OUT/32_dns_routes.txt"

## 4) Отворени файлове (ако има lsof)
if have lsof; then
  lsof -nP -u "$(id -u -n 2>/dev/null || echo "$USER")" > "$OUT/40_lsof_user.txt" 2>/dev/null || true
fi

## 5) Сигурност на SSH ключове и разрешения
{
  echo "=== ~/.ssh ==="
  if [ -d ~/.ssh ]; then
    ls -l ~/.ssh
    for f in ~/.ssh/id_*; do
      [ -f "$f" ] || continue
      echo
      echo "-- Inspect: $f"
      ls -l "$f"
      (head -n 1 "$f.pub" 2>/dev/null || echo "no pub for $f") 
    done
    [ -f ~/.ssh/authorized_keys ] && { echo; echo "authorized_keys:"; nl -ba ~/.ssh/authorized_keys; }
    [ -f ~/.ssh/config ] && { echo; echo "ssh config:"; sed -n '1,200p' ~/.ssh/config; }
  else
    echo "~/.ssh missing"
  fi
} > "$OUT/50_ssh_keys.txt"

## 6) Последни промени по $HOME (скоро модифицирани/изпълними)
{
  echo "=== Recent modified (48h) ==="
  find "$HOME" -xdev -mtime -2 -type f -printf "%TY-%Tm-%Td %TH:%TM %p\n" 2>/dev/null | sort -r | head -n 500
  echo
  echo "=== Executables in PATH ==="
  IFS=':' read -r -a P_ARR <<< "$PATH"
  for d in "${P_ARR[@]}"; do [ -d "$d" ] && find "$d" -maxdepth 1 -type f -perm -111 -printf "%p\n"; done
  echo
  echo "=== Suspicious writable dirs ==="
  for d in /tmp /var/tmp "$HOME/.local/bin" "$HOME/bin"; do [ -d "$d" ] && { echo "$d:"; ls -la "$d"; }; done
} > "$OUT/60_files_recent_execs.txt"

## 7) Python/Node процеси с пълна команда
{
  echo "=== Python processes ==="
  ps auxww | awk '/python/ && !/awk/ {print}'
  echo
  echo "=== Node processes ==="
  ps auxww | awk '/node/ && !/awk/ {print}'
} > "$OUT/70_interpreters.txt"

## 8) Файлови интегритетни сигнали (хеш на ключови конфигурации)
{
  echo "=== Hashes (SHA256) of key configs if present ==="
  for f in ~/.bashrc ~/.profile ~/.zshrc ~/.ssh/authorized_keys ~/.ssh/config ~/.termux/termux.properties; do
    [ -f "$f" ] && { printf "%-40s " "$f"; sha256sum "$f"; }
  done
} > "$OUT/80_hashes.txt" 2>/dev/null || true

## 9) Обобщение и препоръки (Nyx/Aurion метод)
{
  echo "=== Summary — Nyx/Aurion scan ==="
  echo "- Nyx (напрежение): процеси с висок CPU/MEM, нови изпълними файлове, непознати слушащи портове."
  echo "- Aurion (светлина): провери 10/11/30/31/60 файловете; всичко непознато = флаг."
  echo
  echo "Checklist:"
  echo "1) Прегледай 30_listen_ports.txt — има ли слушащи портове, които не очакваш?"
  echo "2) Прегледай 31_active_conns.txt — постоянни външни IP връзки?"
  echo "3) В 11_top_cpu/12_top_mem — неизвестни процеси с висок ресурс?"
  echo "4) В 60_files_recent_execs — нови скриптове/бинари последните 48ч?"
  echo "5) В 50_ssh_keys — непознати ключове/hosts?"
  echo "6) В 20_startup — cron/termux-boot/услуги, които не си създавал?"
} > "$OUT/90_summary.txt"

log "Packaging report…"
( cd "$(dirname "$OUT")" && tar -czf "${OUT}.tar.gz" "$(basename "$OUT")" )
log "DONE. Report: ${OUT}.tar.gz"
printf "\nReport folder: %s\nArchive: %s.tar.gz\n" "$OUT" "$OUT" | tee -a "$OUT/_audit.log"
