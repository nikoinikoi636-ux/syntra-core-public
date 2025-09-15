import shutil, zipfile
from pathlib import Path

downloads = Path.home() / "downloads"
target_dir = Path.home() / "WorkingProgram" / "HeartCore"

def move_and_unzip():
    for file in downloads.iterdir():
        if file.suffix == ".zip":
            print(f"🧩 Unzipping: {file.name}")
            try:
                with zipfile.ZipFile(file, 'r') as zip_ref:
                    zip_ref.extractall(target_dir)
                print(f"✅ Extracted to {target_dir}")
                file.unlink()
            except Exception as e:
                print(f"⛔ Failed to unzip {file.name}: {e}")

        elif file.suffix == ".sh":
            try:
                print(f"📥 Moving script: {file.name}")
                shutil.move(str(file), target_dir / file.name)
            except Exception as e:
                print(f"⛔ Error moving {file.name}: {e}")

if __name__ == "__main__":
    move_and_unzip()
