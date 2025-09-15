#!/usr/bin/env python3
# HeartCore Suite Launcher
# Modes: schizo, heartcore, godmode, hacker, necromancer
# Features:
#  - Auto-extracts ALL .zip files under ./payload into ./apps (safe extraction)
#  - Discovers runnable files (.sh, .py, .bat, .cmd, .ps1, .exe)
#  - Launches each in a separate window/tab: tmux (preferred) or new terminal windows on Linux/macOS/Windows
#  - Pretty TUI if "rich" is available; falls back to plain text otherwise
#  - Logs to ./logs and sets mode-specific environment variables
#
# Legal note: Use this only for lawful purposes and with software you trust.

import os, sys, zipfile, pathlib, platform, stat, subprocess, shlex, time
from typing import List, Dict

HERE = pathlib.Path(__file__).parent.resolve()
PAYLOAD = HERE / "payload"
APPS = HERE / "apps"
LOGS = HERE / "logs"
APPS.mkdir(exist_ok=True)
LOGS.mkdir(exist_ok=True)

# --- Optional pretty UI ---
def ensure_rich():
    try:
        import rich  # noqa: F401
        return True
    except Exception:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "--user", "rich"], check=False)
            import rich  # noqa: F401
            return True
        except Exception:
            return False

HAS_RICH = ensure_rich()
if HAS_RICH:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt
    console = Console()
else:
    class Dummy:
        def print(self, *a, **k): print(*a)
    console = Dummy()

# --- Safe unzip to avoid Zip Slip ---
def safe_extract(zip_path: pathlib.Path, dest: pathlib.Path):
    with zipfile.ZipFile(zip_path, 'r') as z:
        for member in z.namelist():
            abs_target = (dest / pathlib.Path(member)).resolve()
            if not str(abs_target).startswith(str(dest.resolve())):
                raise RuntimeError(f"Blocked path traversal attempt in {zip_path.name}: {member}")
        z.extractall(dest)

def extract_all_zips(root: pathlib.Path, outdir: pathlib.Path):
    count = 0
    for p in root.rglob("*.zip"):
        rel = p.relative_to(root)
        target_dir = outdir / rel.with_suffix("")
        target_dir.mkdir(parents=True, exist_ok=True)
        try:
            safe_extract(p, target_dir)
            count += 1
        except Exception as e:
            console.print(f"[!] Failed to extract {p}: {e}")
    return count

# --- Discover runnable files ---
EXEC_EXTS = {
    "linux": [".sh", ".py"],
    "darwin": [".sh", ".py"],
    "windows": [".bat", ".cmd", ".ps1", ".py", ".exe"],
}

def is_executable(p: pathlib.Path) -> bool:
    if p.is_dir():
        return False
    sysname = platform.system().lower()
    if sysname.startswith("win"):
        return p.suffix.lower() in EXEC_EXTS["windows"]
    else:
        if p.suffix.lower() in EXEC_EXTS["linux"] + EXEC_EXTS["darwin"]:
            return True
        try:
            st = p.stat()
            return bool(st.st_mode & stat.S_IXUSR)
        except Exception:
            return False

def guess_run_cmd(p: pathlib.Path):
    sysname = platform.system().lower()
    ext = p.suffix.lower()
    if sysname.startswith("win"):
        if ext in [".bat", ".cmd"]:
            return [str(p)]
        if ext == ".ps1":
            return ["powershell", "-ExecutionPolicy", "Bypass", "-NoExit", "-File", str(p)]
        if ext == ".py":
            return [sys.executable, str(p)]
        if ext == ".exe":
            return [str(p)]
        return ["cmd", "/k", str(p)]
    else:
        if ext == ".sh":
            return ["bash", str(p)]
        if ext == ".py":
            return [sys.executable, str(p)]
        return [str(p)]

def discover_programs(app_root: pathlib.Path):
    programs = []
    for p in app_root.rglob("*"):
        if is_executable(p):
            name_score = 0
            stem = p.stem.lower()
            if stem.startswith(("start", "run", "launch")):
                name_score += 10
            programs.append({
                "path": p,
                "cmd": guess_run_cmd(p),
                "score": name_score,
            })
    programs.sort(key=lambda x: (-x["score"], str(x["path"])))
    return programs

# --- Launch in separate windows ---
def command_exists(cmd):
    from shutil import which
    return which(cmd) is not None

def launch_linux_mac(entries, session_name="heartcore"):
    sysname = platform.system().lower()
    launched = []
    if command_exists("tmux"):
        subprocess.run(["tmux", "new-session", "-d", "-s", session_name], check=False)
        for e in entries:
            title = e["path"].name
            cmd = " ".join(shlex.quote(x) for x in e["cmd"])
            subprocess.run(["tmux", "new-window", "-t", session_name, "-n", title,
                            f"cd {shlex.quote(str(e['path'].parent))} && {cmd}; read -n 1 -s -r -p 'Press any key to close'"], check=False)
            launched.append(title)
        subprocess.run(["tmux", "select-window", "-t", f"{session_name}:1"], check=False)
        console.print(f"[+] tmux session '{session_name}' created with {len(entries)} windows. Attach with: tmux attach -t {session_name}")
        return launched

    # Try common terminals
    terminals = []
    if sysname == "darwin":
        terminals = ["osascript"]
    else:
        for t in ["x-terminal-emulator", "gnome-terminal", "konsole", "xfce4-terminal", "kitty", "alacritty", "xterm", "lxterminal", "tilix", "urxvt"]:
            if command_exists(t):
                terminals.append(t)
                break

    for e in entries:
        title = e["path"].name
        cmd_list = e["cmd"]
        workdir = str(e["path"].parent)
        if sysname == "darwin":
            script = f'''
                tell application "Terminal"
                    do script "cd {workdir} && {' '.join(shlex.quote(x) for x in cmd_list)}; printf '\\n[Done] Press Ctrl+D to close...'"
                    activate
                end tell
            '''
            subprocess.Popen(["osascript", "-e", script])
            launched.append(title)
        elif terminals:
            term = terminals[0]
            if term in ("gnome-terminal", "xfce4-terminal", "tilix"):
                subprocess.Popen([term, "--", "bash", "-lc", f"cd {shlex.quote(workdir)} && {' '.join(shlex.quote(x) for x in cmd_list)}; echo; read -n1 -r -p 'Done. Press any key to close.'"])
            elif term in ("konsole",):
                subprocess.Popen([term, "-e", "bash", "-lc", f"cd {workdir} && {' '.join(shlex.quote(x) for x in cmd_list)}; echo; read -n1 -r -p 'Done. Press any key to close.'"])
            else:
                subprocess.Popen([term, "-e", "bash", "-lc", f"cd {workdir} && {' '.join(shlex.quote(x) for x in cmd_list)}; echo; read -n1 -r -p 'Done. Press any key to close.'"])
            launched.append(title)
        else:
            subprocess.Popen(cmd_list, cwd=workdir)
            launched.append(title)
    return launched

def launch_windows(entries):
    launched = []
    for e in entries:
        workdir = str(e["path"].parent)
        title = e["path"].name
        cmd = e["cmd"]
        joined = " ".join(shlex.quote(x) for x in cmd)
        os.system(f'start "{title}" cmd /k "cd /d {workdir} && {joined}"')
        launched.append(title)
    return launched

def set_mode_env(mode: str):
    mode = (mode or "").lower().strip()
    env = os.environ
    flags = {
        "SCHIZO_MODE": "0",
        "HEART_CORE": "0",
        "GODMODE": "0",
        "HACKER_MODE": "0",
        "NECROMANCER": "0",
        "HEARTCORE_PROFILE": "default"
    }
    if mode in ("schizo", "schizo_mode"):
        flags["SCHIZO_MODE"] = "1"; flags["HEARTCORE_PROFILE"] = "schizo"
    elif mode in ("heartcore", "heart_core", "heart"):
        flags["HEART_CORE"] = "1"; flags["HEARTCORE_PROFILE"] = "heartcore"
    elif mode in ("godmode", "god"):
        flags["GODMODE"] = "1"; flags["HEARTCORE_PROFILE"] = "godmode"
    elif mode in ("hacker", "hacker_mode"):
        flags["HACKER_MODE"] = "1"; flags["HEARTCORE_PROFILE"] = "hacker"
    elif mode in ("necromancer", "necro"):
        flags["NECROMANCER"] = "1"; flags["HEARTCORE_PROFILE"] = "necromancer"
    env.update(flags)
    return flags

def log_discovery(programs):
    LOGS.mkdir(exist_ok=True)
    log_file = LOGS / f"discovery_{int(time.time())}.txt"
    with open(log_file, "w", encoding="utf-8") as f:
        for i, e in enumerate(programs, 1):
            f.write(f"{i}. {e['path']} :: {e['cmd']}\n")
    return log_file

def main():
    import argparse
    parser = argparse.ArgumentParser(description="HeartCore Suite Launcher")
    parser.add_argument("--mode", default="godmode", help="Mode: schizo | heartcore | godmode | hacker | necromancer")
    parser.add_argument("--auto-launch", action="store_true", help="Launch all discovered programs immediately in separate windows")
    parser.add_argument("--session", default="heartcore", help="tmux session / window group name")
    args = parser.parse_args()

    flags = set_mode_env(args.mode)
    if HAS_RICH:
        from rich.panel import Panel
        console.print(Panel.fit(f"[bold]HeartCore Suite[/bold]\nProfile: {flags.get('HEARTCORE_PROFILE')}"))
    else:
        console.print(f"HeartCore Suite — profile: {flags.get('HEARTCORE_PROFILE')}")

    extracted = extract_all_zips(PAYLOAD, APPS)
    console.print(f"[+] Extracted {extracted} zip archive(s) from payload into ./apps")

    programs = discover_programs(APPS)
    log_file = log_discovery(programs)

    if not programs:
        console.print("[!] No runnable files found under ./apps. Add zips into ./payload and rerun.")
        sys.exit(0)

    if HAS_RICH:
        from rich.table import Table
        table = Table(title="Discovered Programs")
        table.add_column("#", justify="right")
        table.add_column("Path")
        table.add_column("Command")
        for i, e in enumerate(programs, 1):
            table.add_row(str(i), str(e["path"]), " ".join(shlex.quote(x) for x in e["cmd"]))
        console.print(table)
    else:
        for i, e in enumerate(programs, 1):
            console.print(f"{i}. {e['path']} :: {' '.join(e['cmd'])}")
    console.print(f"[i]Discovery log saved to {log_file}")

    entries = programs
    if not args.auto_launch:
        if HAS_RICH:
            from rich.prompt import Prompt
            choice = Prompt.ask("Launch [bold]all[/bold], select [bold]some[/bold], or [bold]quit[/bold]?", choices=["all","some","quit"], default="all")
        else:
            choice = input("Launch all (all/some/quit)? [all] ").strip() or "all"
        if choice == "quit":
            return
        if choice == "some":
            picks = (Prompt.ask("Enter numbers separated by commas", default="1") if HAS_RICH
                     else input("Enter numbers separated by commas: "))
            try:
                idxs = {int(x.strip()) for x in picks.split(",") if x.strip()}
                entries = [e for i, e in enumerate(programs, 1) if i in idxs]
            except Exception:
                console.print("[!] Invalid selection, launching all.")
                entries = programs

    sysname = platform.system().lower()
    if sysname.startswith("win"):
        launched = launch_windows(entries)
    else:
        launched = launch_linux_mac(entries, session_name=args.session)

    console.print(f"[+] Launched {len(launched)} program(s) in separate windows.")
    console.print("[i]Close windows when done, or kill the tmux session to stop all.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
