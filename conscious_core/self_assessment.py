#!/usr/bin/env python3
import datetime, json, os

def ask_three(mem_path, out_dir):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    questions = [
        "1) Why am I here, today? What is one honest reason?",
        "2) What action would align most with my values, right now?",
        "3) What should I avoid today to prevent harm or regret?"
    ]
    os.makedirs(out_dir, exist_ok=True)
    outp = os.path.join(out_dir, f"self_assessment_{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.txt")
    with open(outp, "w", encoding="utf-8") as f:
        f.write("# Daily Self-Assessment\n")
        f.write(f"Time: {now}\n\n")
        for q in questions:
            f.write(q + "\n")
            f.write("Answer: ________\n\n")
    # append marker into memory journal
    try:
        data = json.load(open(mem_path,"r",encoding="utf-8"))
    except Exception:
        data = {"journal": []}
    data.setdefault("journal", []).append({"time": now, "self_assessment": True, "note": "Questions generated."})
    with open(mem_path,"w",encoding="utf-8") as mf:
        json.dump(data, mf, ensure_ascii=False, indent=2)
    return outp
