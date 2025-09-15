#!/usr/bin/env bash
set -euo pipefail

# Пакети (без feedparser)
pip install --upgrade requests beautifulsoup4 PyYAML typing_extensions soupsieve

# Директории
mkdir -p "$HOME/WorkingProgram/harvest" \
         "$HOME/WorkingProgram/HeartCore/logic" \
         "$HOME/WorkingProgram/HeartCore/notes"

# sources.yml (whitelist)
cat > "$HOME/WorkingProgram/harvest/sources.yml" <<'YAML'
interval_minutes: 60
max_items_per_source: 25
user_agent: "HeartCoreHarvester/1.0 (+PHOENIX_NODE_BG)"
sources:
  - name: EUFunds_BG
    type: rss
    url: "https://www.eufunds.bg/bg/rss.xml"
    tags: ["eu", "funds", "bg"]

  - name: Varna_Municipality
    type: html
    url: "https://varna.bg/"
    selector: "a"
    domain_allow: ["varna.bg"]
    tags: ["varna", "municipality"]

  - name: OIC_Varna
    type: rss
    url: "https://oic-varna.eu/feed/"
    tags: ["oic", "varna", "eu"]

  - name: Bulgarian_Gov
    type: rss
    url: "https://www.gov.bg/bg/rss"
    tags: ["gov", "bg"]
YAML

# harvester.py — без feedparser (чист RSS през xml.etree)
cat > "$HOME/WorkingProgram/harvest/harvester.py" <<'PY'
#!/usr/bin/env python3
import argparse, json, hashlib, time, re, sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup
import yaml
import xml.etree.ElementTree as ET

def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def ensure_dir(p: Path): p.mkdir(parents=True, exist_ok=True)

def clean_text(html_or_text: str) -> str:
    soup = BeautifulSoup(html_or_text, "html.parser")
    for tag in soup(["script","style","noscript"]): tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    return re.sub(r"\s+", " ", text).strip()

def fetch(url: str, ua: str) -> str:
    r = requests.get(url, headers={"User-Agent": ua}, timeout=25)
    r.raise_for_status(); return r.text

def within_domain(url: str, allowed):
    if not allowed: return True
    host = urlparse(url).netloc.lower()
    return any(host.endswith(d) for d in allowed)

def save_line(path: Path, rec: dict):
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

def rss_items(xml_text: str):
    # Поддържа RSS 2.0 (<item>) и Atom (<entry>)
    root = ET.fromstring(xml_text)
    # попытка за RSS
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        summary = (item.findtext("description") or "").strip()
        yield {"title": title, "link": link, "summary": summary}
    # Atom
    for entry in root.findall(".//{http://www.w3.org/2005/Atom}entry"):
        title = (entry.findtext("{http://www.w3.org/2005/Atom}title") or "").strip()
        link_el = entry.find("{http://www.w3.org/2005/Atom}link")
        link = (link_el.get("href") if link_el is not None else "").strip()
        summary = (entry.findtext("{http://www.w3.org/2005/Atom}summary") or "").strip()
        content = entry.findtext("{http://www.w3.org/2005/Atom}content") or ""
        if (not summary) and content: summary = content
        yield {"title": title, "link": link, "summary": summary}

def process_rss(src, cfg, kb_path: Path, seen_path: Path):
    try:
        xml_text = fetch(src["url"], cfg["user_agent"])
    except Exception as e:
        print(f"[WARN] RSS fetch failed {src['name']}: {e}", file=sys.stderr)
        return 0
    seen = set(seen_path.read_text().splitlines()) if seen_path.exists() else set()
    count = 0
    for it in rss_items(xml_text):
        url = it.get("link") or ""
        if not url: continue
        h = sha256(url)
        if h in seen: continue
        # опитай да вземеш пълната страница
        try:
            html = fetch(url, cfg["user_agent"]); text = clean_text(html)
        except Exception:
            text = clean_text((it.get("title","")+" "+it.get("summary","")).strip())
        rec = {
            "source": src["name"],
            "type": "rss",
            "url": url,
            "title": it.get("title",""),
            "tags": src.get("tags",[]),
            "fetched_utc": utc_now(),
            "content": text[:20000],
            "content_sha256": sha256(text[:20000])
        }
        save_line(kb_path, rec)
        with seen_path.open("a") as s: s.write(h+"\n")
        count += 1
        if count >= cfg.get("max_items_per_source", 25): break
    return count

def process_html(src, cfg, kb_path: Path, seen_path: Path):
    try:
        html = fetch(src["url"], cfg["user_agent"])
    except Exception as e:
        print(f"[WARN] HTML fetch failed {src['name']}: {e}", file=sys.stderr)
        return 0
    soup = BeautifulSoup(html, "html.parser")
    selector = src.get("selector","a")
    raw_links = []
    for a in soup.select(selector):
        href = a.get("href") or ""
        if href.startswith("#") or href.startswith("mailto:"): continue
        full = urljoin(src["url"], href)
        if not within_domain(full, src.get("domain_allow")): continue
        raw_links.append(full)
    links = list(dict.fromkeys(raw_links))
    seen = set(seen_path.read_text().splitlines()) if seen_path.exists() else set()
    count = 0
    for url in links:
        h = sha256(url)
        if h in seen: continue
        try:
            page = fetch(url, cfg["user_agent"])
            text = clean_text(page)
        except Exception:
            continue
        rec = {
            "source": src["name"],
            "type": "html",
            "url": url,
            "title": "",
            "tags": src.get("tags",[]),
            "fetched_utc": utc_now(),
            "content": text[:20000],
            "content_sha256": sha256(text[:20000])
        }
        save_line(kb_path, rec)
        with seen_path.open("a") as s: s.write(h+"\n")
        count += 1
        if count >= cfg.get("max_items_per_source", 25): break
    return count

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seen", required=True)
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    out = Path(args.out); seen = Path(args.seen)
    ensure_dir(out.parent); ensure_dir(seen.parent)
    if not seen.exists(): seen.write_text("", encoding="utf-8")

    total = 0
    for src in cfg.get("sources", []):
        try:
            if src["type"] == "rss":
                total += process_rss(src, cfg, out, seen)
            elif src["type"] == "html":
                total += process_html(src, cfg, out, seen)
        except Exception as e:
            print(f"[WARN] {src.get('name')} err: {e}", file=sys.stderr)
        time.sleep(0.4)
    print(f"[OK] harvested={total} @ {utc_now()} -> {out}")
if __name__ == "__main__":
    main()
PY
chmod +x "$HOME/WorkingProgram/harvest/harvester.py"

# ingest_local.py
cat > "$HOME/WorkingProgram/harvest/ingest_local.py" <<'PY'
#!/usr/bin/env python3
import argparse, json, hashlib
from datetime import datetime, timezone
from pathlib import Path

def utc_now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
def sha256b(b: bytes):
    import hashlib; return hashlib.sha256(b).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--notes-dir", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    notes = Path(args.notes-dir) if hasattr(args, "notes-dir") else Path(args.notes_dir)  # safeguard
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)

    for p in notes.rglob("*"):
        if not p.is_file(): continue
        if p.suffix.lower() not in [".md",".txt",".json"]: continue
        data = p.read_bytes()
        try:
            text = data.decode("utf-8", errors="ignore")
        except Exception:
            text = ""
        rec = {
            "source": "LOCAL_NOTES",
            "type": "local",
            "path": str(p),
            "title": p.name,
            "tags": ["local","notes"],
            "fetched_utc": utc_now(),
            "content": text[:20000],
            "content_sha256": sha256b(data)
        }
        with out.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False)+"\n")
    print(f"[OK] local ingest -> {out}")
if __name__ == "__main__":
    main()
PY
chmod +x "$HOME/WorkingProgram/harvest/ingest_local.py"

echo "[OK] Setup complete."
