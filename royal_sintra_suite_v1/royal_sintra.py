#!/usr/bin/env python3
import argparse, sys
from pathlib import Path
from royal_sintra.core.collectors import collect
from royal_sintra.core.normalizer import normalize
from royal_sintra.core.sanitizer import sanitize
from royal_sintra.core.analyzer import analyze
from royal_sintra.core.bridge import bridge_push
from royal_sintra.core.heart import join_heart
from royal_sintra.core.watcher import watch
from royal_sintra.core.policy import scan_tree
from royal_sintra.core.return_channel import pull_rules, apply_policy_config


def main():
    p = argparse.ArgumentParser(prog="royal_sintra", description="Royal Sintra Suite v1 — defensive triage + heart node + bridge")
    sub = p.add_subparsers(dest="cmd", required=True)

    pc = sub.add_parser("collect"); pc.add_argument("--paths", nargs="+", required=True); pc.add_argument("--base", default="."); pc.add_argument("--max-size-mb", type=int, default=5)
    pn = sub.add_parser("normalize"); pn.add_argument("--evidence", required=True)
    ps = sub.add_parser("sanitize"); ps.add_argument("--evidence", required=True)
    pa = sub.add_parser("analyze");  pa.add_argument("--evidence", required=True); pa.add_argument("--rules", default="royal_sintra/heart_rules/indicators.yml")

    pb = sub.add_parser("bridge-push"); pb.add_argument("--evidence", required=True); pb.add_argument("--repo", required=True); pb.add_argument("--branch", default="sintra-sync")

    pj = sub.add_parser("join-heart"); pj.add_argument("--name", required=True); pj.add_argument("--tags", default=""); pj.add_argument("--base", default=".")

    pw = sub.add_parser("watch"); pw.add_argument("--paths", nargs="+", required=True); pw.add_argument("--rules", default="royal_sintra/heart_rules/indicators.yml"); pw.add_argument("--base", default="."); pw.add_argument("--interval", type=int, default=600); pw.add_argument("--max-size-mb", type=int, default=5)

    
    pp = sub.add_parser("policy-scan"); pp.add_argument("--path", required=True); pp.add_argument("--policy", default="royal_sintra/heart_rules/heart_rules_balanced.json"); pp.add_argument("--out", default="evidence")

    pr = sub.add_parser("pull-rules"); pr.add_argument("--repo-dir", required=True); pr.add_argument("--dest", default="royal_sintra/heart_rules")

    sp = sub.add_parser("set-policy"); sp.add_argument("--config", required=True); sp.add_argument("--active", default="royal_sintra/heart_rules/ACTIVE_POLICY.txt")

    ap = sub.add_parser("autopilot"); ap.add_argument("--paths", nargs="+", required=True); ap.add_argument("--rules", default="royal_sintra/heart_rules/indicators.yml"); ap.add_argument("--base", default="."); ap.add_argument("--max-size-mb", type=int, default=5); ap.add_argument("--push-repo", default=""); ap.add_argument("--branch", default="sintra-sync")

    args = p.parse_args()

    if args.cmd == "collect":
        ev = collect(args.paths, Path(args.base), max_size_mb=args.max_size_mb)
        print(ev)
    elif args.cmd == "normalize":
        out = normalize(Path(args.evidence))
        print(out)
    elif args.cmd == "sanitize":
        out = sanitize(Path(args.evidence))
        print(out)
    elif args.cmd == "analyze":
        a, s = analyze(Path(args.evidence), Path(args.rules))
        print(a); print(s)
    elif args.cmd == "bridge-push":
        bridge_push(Path(args.evidence), args.repo, args.branch)
    elif args.cmd == "join-heart":
        reg, sig = join_heart(Path(args.base), args.name, args.tags)
        print(reg); print(sig)
    elif args.cmd == "watch":
        watch(Path(args.base), args.paths, Path(args.rules), interval_sec=args.interval, max_size_mb=args.max_size_mb)

    elif args.cmd == "policy-scan":
        out = scan_tree(Path(args.path).expanduser(), Path(args.out), Path(args.policy))
        print(out)
    elif args.cmd == "pull-rules":
        copied = pull_rules(Path(args.repo_dir), Path(args.dest))
        print("copied:", ",".join(copied))
    elif args.cmd == "set-policy":
        target = apply_policy_config(Path(args.config), Path(args.active))
        print("active:", target)
    elif args.cmd == "autopilot":
        ev = collect(args.paths, Path(args.base), max_size_mb=args.max_size_mb)
        normalize(ev)
        sanitize(ev)
        analyze(ev, Path(args.rules))
        if args.push_repo:
            bridge_push(ev, args.push_repo, args.branch)
        print("AUTOPILOT DONE:", ev)

    else:
        p.print_help()

if __name__ == "__main__":
    main()
