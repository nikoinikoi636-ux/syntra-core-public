#!/usr/bin/env python3
# Self-Awareness Agent (engineering awareness, not sentience)
import os, sys, json, time, hashlib, subprocess, socket, platform
from pathlib import Path
ROOT   = Path(__file__).resolve().parent
STATE  = ROOT / "state"; STATE.mkdir(parents=True, exist_ok=True)
LOGS   = ROOT / "logs" / "modules"; LOGS.mkdir(parents=True, exist_ok=True)
SFILE  = STATE / "self_state.json"
TFILE  = STATE / "self_state.txt"
LOG    = LOGS  / "self_awareness.log"

KEY_FILES = [
  "orchestrator.py", "sync_engine.py", "boot_levski_v3.py",
  "watchdog_sync_loop.py", "objective_core.py"
]

def log(msg):
    msg = msg.rstrip()
    print(msg, flush=True)
    LOG.open("a", encoding="utf-8").write(msg + "\n")

def sh(cmd, timeout=5):
    try:
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=timeout)
        return out.decode("utf-8","ignore").strip(), 0
    except subprocess.CalledProcessError as e:
        return e.output.decode("utf-8","ignore"), e.returncode
    except Exception as e:
        return f"(err:{e})", 1

def file_sha256(p: Path):
    try:
        h=hashlib.sha256()
        with p.open("rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None

def running(pattern: str) -> bool:
    out,_ = sh("ps -ef | grep -v grep | grep -E '%s'" % pattern.replace("'","."))
    return bool(out.strip())

def count_timeouts(log_path: Path, n_lines=400):
    if not log_path.exists(): return 0
    try:
        tail = subprocess.check_output(f"tail -n {n_lines} '{log_path}'", shell=True).decode("utf-8","ignore")
    except Exception:
        tail = log_path.read_text(encoding="utf-8", errors="ignore")[-8000:]
    c = 0
    for line in tail.splitlines():
        if "Timeout:" in line or "Error" in line or "Traceback" in line:
            c += 1
    return c

def codex_cycles():
    codex = Path.home()/ "HeartCore_OS_v1" / "logs" / "paradox_codex.md"
    if not codex.exists(): return 0
    try:
        return sum(1 for ln in codex.open(encoding="utf-8") if ln.startswith("### Cycle "))
    except Exception:
        return 0

def load_objective():
    # read objective_core purpose if present
    obj = ROOT / "objective_core.py"
    if not obj.exists(): return None
    # best-effort import via subprocess (avoid import side-effects)
    out,_ = sh(f"python3 '{obj}' echo-purpose", timeout=4)
    if out.startswith("{"):
        try:
            j = json.loads(out)
            return j.get("purpose") or j
        except Exception:
            pass
    # fallback: try config.json purpose
    cfg = ROOT / "config.json"
    if cfg.exists():
        try:
            j = json.loads(cfg.read_text())
            return j.get("purpose")
        except Exception:
            pass
    return None

def snapshot():
    purpose = load_objective()
    # platform
    plat = dict(system=platform.system(), release=platform.release(),
                py=platform.python_version(), machine=platform.machine(),
                hostname=socket.gethostname())
    # resources (best-effort)
    mem,_  = sh("grep MemAvailable /proc/meminfo | awk '{print $2}'")
    disk,_ = sh("df -h . | tail -n1")
    net,_  = sh("ip addr | grep 'inet ' | awk '{print $2}' | paste -sd, -")

    # processes
    procs,_ = sh("ps -ef | grep -v grep | grep python3")
    proc_lines = [l for l in procs.splitlines() if l.strip()]

    # integrity: key file hashes
    hashes = {}
    for name in KEY_FILES:
        p = ROOT / name
        hashes[name] = file_sha256(p) if p.exists() else None

    # git status
    git = {}
    if (ROOT/".git").exists():
        remote,_  = sh(f"git -C '{ROOT}' remote -v | head -n1")
        branch,_  = sh(f"git -C '{ROOT}' rev-parse --abbrev-ref HEAD")
        dirty,_   = sh(f"git -C '{ROOT}' status --porcelain | wc -l")
        git = {"remote":remote, "branch":branch, "dirty":int(dirty or 0)}
    # signals from logs
    orch_log = ROOT / "orchestrator.log"
    timeouts = count_timeouts(orch_log)

    # codex health
    cycles = codex_cycles()

    # scoring (0..100)
    score = 100
    if not running("orchestrator.py"): score -= 10
    if not running("sync_engine.py"):  score -= 15
    if not running("boot_levski_v3.py"): score -= 10
    if timeouts > 3: score -= min(30, timeouts*2)
    if git.get("dirty",0) > 0: score -= 5
    if cycles < 1000: score -= 10
    if len(proc_lines) == 0: score -= 10
    state = "OK"
    if score < 85: state = "WARN"
    if score < 70: state = "ALERT"

    data = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "purpose": purpose,
        "platform": plat,
        "resources": {"mem_kB": mem, "disk": disk, "net": net},
        "processes": proc_lines,
        "integrity": {"hashes": hashes},
        "git": git,
        "orchestrator_timeouts": timeouts,
        "codex_cycles": cycles,
        "score": score,
        "state": state
    }
    SFILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    TFILE.write_text(
        "\n".join([
            f"[{data['ts']}] Self-Awareness",
            f"Purpose: {purpose or '(none)'}",
            f"State: {state}  Score: {score}",
            f"Procs: {len(proc_lines)}  Timeouts(last): {timeouts}",
            f"Codex cycles: {cycles}  Git dirty: {git.get('dirty','-')}",
            f"MemAvail(kB): {mem}  Disk: {disk}",
        ]), encoding="utf-8"
    )
    log(f"[self] snapshot → {SFILE.name} ({state} {score})")
    return data

def explain(data):
    reasons = []
    s = data["score"]
    if s < 100:
        if not any("orchestrator.py" in p for p in data["processes"]):
            reasons.append("orchestrator not running")
        if not any("sync_engine.py" in p for p in data["processes"]):
            reasons.append("sync_engine not running")
        if data["orchestrator_timeouts"] > 3:
            reasons.append(f"timeouts={data['orchestrator_timeouts']}")
        if data["git"].get("dirty",0) > 0:
            reasons.append("git dirty working tree")
        if data["codex_cycles"] < 1000:
            reasons.append("codex incomplete")
        if len(data["processes"]) == 0:
            reasons.append("no python3 processes")
    return reasons or ["optimal"]

def action_autoheal(data):
    # Gentle self-heal for frequent issues
    fixes = []
    def start(path):
        if not Path(path).exists(): return False
        subprocess.Popen(["nohup","python3",path], cwd=str(ROOT),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    # start orchestrator if missing
    if not any("orchestrator.py" in p for p in data["processes"]):
        if start(str(ROOT/"orchestrator.py")):
            fixes.append("started orchestrator")
    # ensure sync engine (non-fatal if not present)
    if not any("sync_engine.py" in p for p in data["processes"]):
        if (ROOT/"sync_engine.py").exists():
            if start(str(ROOT/"sync_engine.py")):
                fixes.append("started sync_engine")
    if fixes:
        log("[self] autoheal: " + ", ".join(fixes))
    return fixes

def main():
    cmd = (sys.argv[1] if len(sys.argv)>1 else "loop").lower()
    if cmd == "once":
        data = snapshot()
        print(json.dumps({"state":data["state"],"score":data["score"],"reasons":explain(data)}, indent=2))
        return
    if cmd == "status":
        if not SFILE.exists():
            print("(no self_state yet)"); return
        print(TFILE.read_text())
        return
    if cmd == "explain":
        if not SFILE.exists():
            print("(no self_state yet)"); return
        data = json.loads(SFILE.read_text())
        print(json.dumps({"reasons":explain(data)}, indent=2))
        return
    if cmd == "panic":
        data = snapshot()
        print(json.dumps({"panic":True,"state":data["state"],"score":data["score"],"reasons":explain(data)}, indent=2))
        return
    if cmd == "loop":
        interval = 180
        try:
            if "--interval" in sys.argv:
                interval = int(sys.argv[sys.argv.index("--interval")+1])
        except Exception: pass
        log(f"[self] loop start interval={interval}s")
        while True:
            data = snapshot()
            if data["state"] != "OK":
                action_autoheal(data)
            time.sleep(interval)
        return
    print("usage: python3 self_awareness.py [once|loop|status|explain|panic] [--interval N]")
if __name__ == "__main__":
    main()
