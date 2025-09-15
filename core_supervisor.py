import hashlib, os, time

def file_fingerprint(path):
    try:
        with open(path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except: return None

def monitor(path, interval=5):
    last_hash = file_fingerprint(path)
    print(f"🔐 Monitoring integrity of {path}...")
    while True:
        time.sleep(interval)
        current_hash = file_fingerprint(path)
        if current_hash != last_hash:
            print("⚠️ ALERT: File integrity violation detected!")
            last_hash = current_hash

if __name__ == "__main__":
    monitor("script.py")