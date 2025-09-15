
import argparse, json, sys
from frame_shifter.pipeline import FrameShifter, load_config

def main():
    ap = argparse.ArgumentParser(description="Frame Shifter — Heart/Mirror/Symbolic/Entity/Elder pipeline")
    ap.add_argument("-c", "--config", help="Path to config JSON (optional)")
    ap.add_argument("-i", "--input", help="Path to input file (or read stdin if omitted)")
    ap.add_argument("-o", "--output", help="Where to write transformed text (optional)")
    args = ap.parse_args()

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

    # Print meta to stderr (so stdout stays clean when piping)
    sys.stderr.write("\n--- META ---\n")
    sys.stderr.write(json.dumps(result["steps"], ensure_ascii=False, indent=2) + "\n")

if __name__ == "__main__":
    main()
