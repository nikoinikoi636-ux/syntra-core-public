import os
import shutil

def scan_and_collect(home, destination):
    for root, dirs, files in os.walk(home):
        for file in files:
            if file.endswith('.py'):
                source_path = os.path.join(root, file)
                rel_path = os.path.relpath(source_path, home)
                target_path = os.path.join(destination, rel_path)
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                try:
                    shutil.copy2(source_path, target_path)
                except PermissionError as e:
                    print(f"PermissionError: {e}")

home = os.path.expanduser("~")
destination = os.path.join(home, "bionet_collected_code/.bionet/quarantine")
os.makedirs(destination, exist_ok=True)
os.system("chmod -R 777 " + os.path.dirname(destination))
scan_and_collect(home, destination)
print("✅ Сканиране и копиране завършено.")
