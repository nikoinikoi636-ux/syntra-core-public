
#!/usr/bin/env python3
import os, json
from pathlib import Path

def analyze_codebase(base_path):
    report = {
        "total_files": 0,
        "py_files": 0,
        "sh_files": 0,
        "json_files": 0,
        "conf_files": 0,
        "suspicious": [],
    }

    for file in Path(base_path).glob("*"):
        if not file.is_file():
            continue
        report["total_files"] += 1
        ext = file.suffix
        content = file.read_text(errors="ignore")

        if ext == ".py":
            report["py_files"] += 1
            if "os.system" in content or "eval(" in content:
                report["suspicious"].append(str(file))
        elif ext == ".sh":
            report["sh_files"] += 1
        elif ext == ".json":
            report["json_files"] += 1
        elif ext == ".conf":
            report["conf_files"] += 1

    with open("analysis_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print("✅ Анализът е завършен. Отчет: analysis_report.json")

if __name__ == "__main__":
    analyze_codebase(os.path.expanduser("~/bionet_collected_code"))
