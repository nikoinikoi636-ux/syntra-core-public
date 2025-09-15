import sys
import os

choice = sys.argv[1] if len(sys.argv) > 1 else "0"

if choice == "1":
    os.system("python3 full_test_runner.py")
elif choice == "2":
    os.system("mkdir -p bionet_collected_code/.bionet/quarantine && chmod -R 777 bionet_collected_code")
elif choice == "3":
    os.system("python3 github_uploader.py")
elif choice == "4":
    os.system("python3 report_generator.py")
elif choice == "5":
    os.system("python3 watcher.py")
elif choice == "6":
    os.system("python3 codeworm_collector.py")
elif choice == "7":
    os.system("python3 sintra_analysis.py")
else:
    print("👋 Изход...")
