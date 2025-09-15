import difflib, sys

def compare_versions(current, previous):
    with open(current, "r", encoding="utf-8") as f1, open(previous, "r", encoding="utf-8") as f2:
        current_lines = f1.readlines()
        previous_lines = f2.readlines()

    diff = list(difflib.unified_diff(previous_lines, current_lines, fromfile='previous', tofile='current', lineterm=''))

    with open("sintra_diff_report.json", "w", encoding="utf-8") as f:
        f.writelines(diff)

    print("📄 Разликите са запазени в sintra_diff_report.json")

if __name__ == "__main__":
    compare_versions(sys.argv[1], sys.argv[2])