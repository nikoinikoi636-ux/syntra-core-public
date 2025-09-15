#!/usr/bin/env python3
# sofia_sentinel_heart_cli.py — Companion CLI: `bionet heart set|find|pick` for v1.0 projects.
import os, sys, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.join(HERE, "join_heart_node_v2.py")

def main():
    if not os.path.isfile(V2):
        print("Missing join_heart_node_v2.py next to this CLI."); sys.exit(1)
    args = sys.argv[1:]
    if not args:
        print("Usage:\n  python3 sofia_sentinel_heart_cli.py heart set <path|.>\n  python3 sofia_sentinel_heart_cli.py heart find [--pattern \"a,b,.py\"] [--max 12]\n  python3 sofia_sentinel_heart_cli.py heart pick <N>")
        sys.exit(0)
    cmd = args[0].lower()
    if cmd != "heart":
        print("Only 'heart' subcommand is supported."); sys.exit(1)
    sub = args[1].lower() if len(args)>=2 else ""
    if sub == "set":
        target = args[2] if len(args)>=3 else "."
        if os.path.isdir(target):
            subprocess.run([sys.executable, V2, "--set-dir", target], check=False)
        else:
            subprocess.run([sys.executable, V2, target], check=False)
    elif sub == "find":
        rest = args[2:]
        subprocess.run([sys.executable, V2] + rest, check=False)
    elif sub == "pick":
        if len(args)<3: print("Provide index: pick <N>"); sys.exit(1)
        subprocess.run([sys.executable, V2, "--pick", args[2]], check=False)
    else:
        print("Usage:\n  heart set <path|.>\n  heart find [--pattern \"a,b,.py\"] [--max 12]\n  heart pick <N>")
if __name__ == "__main__":
    main()
