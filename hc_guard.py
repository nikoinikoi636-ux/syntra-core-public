#!/usr/bin/env python3
import os, re, subprocess, sys, time

def pids_for(pattern: str):
    out = subprocess.run(["ps","-ef"], capture_output=True, text=True).stdout
    return [int(x.split()[1]) for x in out.splitlines() if re.search(pattern, x) and "grep" not in x]

def is_running(basename: str) -> bool:
    return any(pids_for(rf"python3 .*{re.escape(basename)}"))

def kill_dupes(basename: str, keep_newest=True) -> int:
    pids = pids_for(rf"python3 .*{re.escape(basename)}")
    if len(pids) <= 1: return 0
    pid = max(pids) if keep_newest else min(pids)
    killed = 0
    for p in pids:
        if p != pid:
            try:
                os.kill(p, 9)
                killed += 1
            except Exception:
                pass
    return killed

def wait_until_running(basename: str, timeout=15, poll=0.5) -> bool:
    t0 = time.time()
    while time.time()-t0 < timeout:
        if is_running(basename): return True
        time.sleep(poll)
    return is_running(basename)

def start_once(path: str, log_path: str) -> str:
    base = os.path.basename(path)
    if is_running(base):
        return f"[ok] {base} already running."
    cmd = f'nohup python3 "{path}" >> "{log_path}" 2>&1 &'
    subprocess.run(cmd, shell=True)
    ok = wait_until_running(base, timeout=20)
    return f"[ok] started {base}" if ok else f"[warn] start attempted for {base}; check log."

def main():
    if len(sys.argv) < 2:
        print("usage: hc_guard.py <cmd> [args...]"); sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "is":
        print("YES" if is_running(sys.argv[2]) else "NO")
    elif cmd == "kill-dupes":
        print(kill_dupes(sys.argv[2]))
    elif cmd == "start-once":
        print(start_once(sys.argv[2], sys.argv[3]))
    else:
        print("unknown cmd")
        sys.exit(2)

if __name__ == "__main__":
    main()
