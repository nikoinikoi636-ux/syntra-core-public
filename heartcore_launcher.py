#!/usr/bin/env python3
# HeartCore Suite v1.2 — SMART BATCH MODE
# Designed for Termux/mobile: launches apps in safe batches instead of 300+ windows at once.

import os, sys, zipfile, pathlib, platform, stat, subprocess, shlex, time, re
from typing import List, Dict

HERE = pathlib.Path(__file__).parent.resolve()
PAYLOAD = HERE / "payload"
APPS = HERE / "apps"
LOGS = HERE / "logs"
APPS.mkdir(exist_ok=True)
LOGS.mkdir(exist_ok=True)

def log(msg: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOGS / "launcher.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")

# ---- Safe extract
def safe_extract(zp: pathlib.Path, dest: pathlib.Path):
    with zipfile.ZipFile(zp, 'r') as z:
        for m in z.namelist():
            p = (dest / pathlib.Path(m)).resolve()
            if not str(p).startswith(str(dest.resolve())):
                raise RuntimeError(f"Zip path traversal blocked: {m}")
        z.extractall(dest)

def extract_all(root: pathlib.Path, out: pathlib.Path):
    c = 0
    for p in root.rglob("*.zip"):
        t = out / p.relative_to(root).with_suffix("")
        t.mkdir(parents=True, exist_ok=True)
        try:
            safe_extract(p, t)
            c += 1
        except Exception as e:
            log(f"[!] Extract fail {p}: {e}")
    return c

# ---- Discovery
def is_exec(p: pathlib.Path) -> bool:
    if p.is_dir(): return False
    sysname = platform.system().lower()
    if sysname.startswith("win"):
        return p.suffix.lower() in [".bat",".cmd",".ps1",".py",".exe"]
    else:
        if p.suffix.lower() in [".sh",".py"]:
            return True
        try:
            st = p.stat()
            return bool(st.st_mode & stat.S_IXUSR)
        except Exception:
            return False

def run_cmd(p: pathlib.Path):
    sysname = platform.system().lower()
    e = p.suffix.lower()
    if sysname.startswith("win"):
        if e in [".bat",".cmd"]:
            return [str(p)]
        if e == ".ps1":
            return ["powershell","-ExecutionPolicy","Bypass","-NoExit","-File",str(p)]
        if e == ".py":
            return [sys.executable, str(p)]
        if e == ".exe":
            return [str(p)]
        return ["cmd","/k",str(p)]
    else:
        if e == ".sh":
            return ["bash", str(p)]
        if e == ".py":
            return [sys.executable, str(p)]
        return [str(p)]

def discover(root: pathlib.Path):
    L = []
    for p in root.rglob("*"):
        if is_exec(p):
            score = 10 if p.stem.lower().startswith(("start","run","launch")) else 0
            L.append({"path": p, "cmd": run_cmd(p), "score": score})
    L.sort(key=lambda x: (-x["score"], str(x["path"])))
    return L

# ---- Resource sensing (Linux/Android)
def mem_available_mb() -> int:
    try:
        with open("/proc/meminfo","r") as f:
            data = f.read()
        m = re.search(r"MemAvailable:\s+(\d+)\s+kB", data)
        if m:
            kb = int(m.group(1)); return max(1, kb // 1024)
    except Exception:
        pass
    return 512  # conservative fallback

def cpu_count() -> int:
    try:
        return os.cpu_count() or 2
    except Exception:
        return 2

def smart_batch_size() -> int:
    # Heuristic: allow ~1 window per 120MB available, cap by CPU*3, clamp 1..25
    avail = mem_available_mb()
    cpu = cpu_count()
    by_mem = max(1, avail // 120)
    by_cpu = max(1, cpu * 3)
    sz = min(by_mem, by_cpu, 25)
    return max(1, sz)

# ---- tmux helpers
def tmux_exists():
    from shutil import which
    return which("tmux") is not None

def tmux_session_exists(name: str) -> bool:
    try:
        r = subprocess.run(["tmux","has-session","-t",name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return r.returncode == 0
    except Exception:
        return False

def tmux_ensure(name: str):
    if not tmux_session_exists(name):
        subprocess.run(["tmux","new-session","-d","-s",name,"bash"], check=False)

def spawn_tmux_window(session: str, title: str, workdir: str, cmd: str):
    subprocess.run(["tmux","new-window","-t",session,"-n",title,
                    f"cd {shlex.quote(workdir)} && {cmd}; echo; read -n1 -r -p 'Done. Press any key'"], check=False)

def spawn_terminal(workdir: str, cmd_list: list):
    # Best-effort terminals on Linux/Android
    from shutil import which
    for t in ["x-terminal-emulator","gnome-terminal","konsole","xfce4-terminal","kitty","alacritty","xterm","lxterminal","tilix","urxvt"]:
        if which(t):
            if t in ("gnome-terminal","xfce4-terminal","tilix"):
                subprocess.Popen([t,"--","bash","-lc",f"cd {shlex.quote(workdir)} && {' '.join(shlex.quote(x) for x in cmd_list)}; echo; read -n1 -r -p 'Done'"])
            else:
                subprocess.Popen([t,"-e","bash","-lc",f"cd {workdir} && {' '.join(shlex.quote(x) for x in cmd_list)}; echo; read -n1 -r -p 'Done'"])
            return True
    # Fallback: background process
    subprocess.Popen(cmd_list, cwd=workdir)
    return True

def set_mode_env(mode: str):
    mode = (mode or '').lower().strip()
    flags = {"SCHIZO_MODE":"0","HEART_CORE":"0","GODMODE":"0","HACKER_MODE":"0","NECROMANCER":"0","HEARTCORE_PROFILE":"default"}
    if mode in ("schizo","schizo_mode"): flags.update(SCHIZO_MODE="1", HEARTCORE_PROFILE="schizo")
    elif mode in ("heartcore","heart_core","heart"): flags.update(HEART_CORE="1", HEARTCORE_PROFILE="heartcore")
    elif mode in ("godmode","god"): flags.update(GODMODE="1", HEARTCORE_PROFILE="godmode")
    elif mode in ("hacker","hacker_mode"): flags.update(HACKER_MODE="1", HEARTCORE_PROFILE="hacker")
    elif mode in ("necromancer","necro"): flags.update(NECROMANCER="1", HEARTCORE_PROFILE="necromancer")
    os.environ.update(flags)
    return flags

def main():
    import argparse
    p = argparse.ArgumentParser(description="HeartCore Suite v1.2 — SMART BATCH MODE")
    p.add_argument("--mode", default="godmode")
    p.add_argument("--session", default="heartcore")
    p.add_argument("--batch", type=int, default=None, help="Manual batch size (programs per wave)")
    p.add_argument("--smart-batch", action="store_true", help="Auto-compute safe batch size based on RAM/CPU")
    p.add_argument("--stagger", type=float, default=1.0, help="Delay between spawns inside a batch (seconds)")
    p.add_argument("--wave", type=int, default=1, help="Which wave to launch (1-based). Use to resume next waves.")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    set_mode_env(args.mode)
    log("[*] Extracting payload...")
    ex = extract_all(PAYLOAD, APPS)
    log(f"[+] Extracted {ex} zip(s)")

    progs = discover(APPS)
    if not progs:
        log("[!] No runnable files in ./apps"); return

    total = len(progs)
    # Compute batch size
    bsz = args.batch if args.batch else (smart_batch_size() if args.smart_batch else 10)
    bsz = max(1, bsz)
    waves = (total + bsz - 1) // bsz
    wave = max(1, min(args.wave, waves))
    start = (wave - 1) * bsz
    end = min(total, start + bsz)
    slice_entries = progs[start:end]

    log(f"[i] Total discovered: {total}. Batch size: {bsz}. Waves: {waves}. Launching wave {wave} [{start+1}..{end}]")

    if args.dry_run:
        for i, e in enumerate(slice_entries, start+1):
            log(f"{i}. {e['path']} :: {' '.join(e['cmd'])}")
        log("[i] Dry run end."); return

    sysname = platform.system().lower()
    launched = 0
    if sysname.startswith("win"):
        # Windows: spawn cmd windows
        for e in slice_entries:
            wd = str(e["path"].parent); title = e["path"].name
            joined = " ".join(shlex.quote(x) for x in e["cmd"])
            os.system(f'start "{title}" cmd /k "cd /d {wd} && {joined}"')
            launched += 1
            if args.stagger > 0: time.sleep(args.stagger)
    else:
        if tmux_exists():
            tmux_ensure(args.session)
            for e in slice_entries:
                title = e["path"].name
                cmd = " ".join(shlex.quote(x) for x in e["cmd"])
                spawn_tmux_window(args.session, title, str(e["path"].parent), cmd)
                launched += 1
                if args.stagger > 0: time.sleep(args.stagger)
            log(f"[+] tmux session '{args.session}' now has +{launched} window(s). Attach with: tmux attach -t {args.session}")
        else:
            for e in slice_entries:
                spawn_terminal(str(e["path"].parent), e["cmd"])
                launched += 1
                if args.stagger > 0: time.sleep(args.stagger)

    log(f"[+] Launched {launched} program(s) in wave {wave}/{waves}.")
    if wave < waves:
        log(f"[→] To launch the next wave: re-run with --wave {wave+1} (or use --smart-batch to auto-size).")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("[i] Interrupted")
