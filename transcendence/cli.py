#!/usr/bin/env python3
import argparse, sys, json, os, pathlib, datetime
from pathlib import Path
from transcendence_engine import TranscendenceEngine
from design_smith import generate_project

APP_DIR = Path(__file__).parent
STATE_DIR = APP_DIR / ".state"
STATE_DIR.mkdir(exist_ok=True)

def cmd_plan(args):
    eng = TranscendenceEngine(state_dir=STATE_DIR)
    plan = eng.propose_plan()
    print(json.dumps(plan, indent=2, ensure_ascii=False))

def cmd_evaluate(args):
    eng = TranscendenceEngine(state_dir=STATE_DIR)
    report = eng.evaluate_once()
    print(json.dumps(report, indent=2, ensure_ascii=False))

def cmd_scaffold(args):
    spec_path = Path(args.spec)
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    result = generate_project(spec_path, out_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))

def cmd_learn(args):
    eng = TranscendenceEngine(state_dir=STATE_DIR)
    fb = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "rating": args.rating,
        "notes": args.notes
    }
    eng.record_feedback(fb)
    print("Recorded feedback.")

def main():
    p = argparse.ArgumentParser(description="Transcendence Kit CLI (safe, offline, human-in-loop)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s1 = sub.add_parser("plan", help="Propose next evolution plan (no execution)")
    s1.set_defaults(func=cmd_plan)

    s2 = sub.add_parser("evaluate", help="Run a single self-evaluation cycle (no network)")
    s2.set_defaults(func=cmd_evaluate)

    s3 = sub.add_parser("scaffold", help="Design a system from YAML spec into a new project folder")
    s3.add_argument("--spec", required=True, help="YAML spec file")
    s3.add_argument("--out", required=True, help="Output directory")
    s3.set_defaults(func=cmd_scaffold)

    s4 = sub.add_parser("learn", help="Append human feedback to the evolution log")
    s4.add_argument("--rating", type=int, default=3)
    s4.add_argument("--notes", default="")
    s4.set_defaults(func=cmd_learn)

    args = p.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
