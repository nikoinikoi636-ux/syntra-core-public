
# ai_ids.py
def analyze(logs):
    suspicious = []
    for entry in logs:
        if any(term in entry.lower() for term in ['override', 'tamper', 'inject', 'bypass']):
            suspicious.append(entry)
    return {
        "intrusion_signals": suspicious,
        "status": "⚠️ DETECTED" if suspicious else "✅ CLEAN"
    }
