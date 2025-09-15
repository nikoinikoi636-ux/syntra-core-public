
import argparse, json, sys
from frame_shifter.pipeline import FrameShifter, load_config
from frame_shifter.shadow_pipeline import ShadowShifter, load_config as load_shadow_config

def main():
    ap = argparse.ArgumentParser(description="Frame Shifter — normal/shadow modes")
    ap.add_argument("-c", "--config", help="Path to config JSON (optional)")
    ap.add_argument("-i", "--input", help="Path to input file (or read stdin if omitted)")
    ap.add_argument("-o", "--output", help="Where to write transformed text (optional)")
    ap.add_argument("--mode", choices=["normal","shadow"], default="normal", help="Processing mode")
    args = ap.parse_args()

    if args.mode == "shadow":
        cfg = load_shadow_config(args.config)
        fs = ShadowShifter(cfg)
    else:
        cfg = load_config(args.config)
        fs = FrameShifter(cfg)

    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    result = fs.shift(text)
    out_text = result["output"]

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out_text)
    else:
        sys.stdout.write(out_text)

    # meta to stderr
    sys.stderr.write("\n--- META ---\n")
    sys.stderr.write(json.dumps(result["steps"], ensure_ascii=False, indent=2) + "\n")

if __name__ == "__main__":
    main()
