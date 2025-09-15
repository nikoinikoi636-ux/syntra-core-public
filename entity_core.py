# entity_core.py — Heart System v2.3 (stdlib-only)
# AGENT_SIGNATURE = "ENTITY-AGENT-2.3"
# Safe by design: HEART principles; lawful sources only; no harmful actions.

import os, re, json, time, threading, math, html
from datetime import datetime
from urllib.parse import quote_plus, urlparse
from urllib.request import Request, urlopen

STATE_FILE = "entity_state.json"

# ===================== EMBEDDED HEART CORE =====================
HEART_FINGERPRINT = "embedded:v1"
HEART_PROMPTS = [
    "Коя е най-полезната малка стъпка днес?",
    "Кой е проверимият източник за текущата теза?",
    "Кое е факт, кое е извод, кое е мнение?",
    "Как да намаля вредата и да увелича истината?",
    "Какво липсва за силен извод?",
    "Има ли контра-хипотеза и как да я проверя?",
    "Кои са трите най-надеждни източника по темата?"
]

# ===================== STATE =====================
DEFAULT_STATE = {
    "net": {"enabled": True, "last_error": ""},
    "heart": {"present": True, "fingerprint": HEART_FINGERPRINT, "prompts": HEART_PROMPTS},
    "spheres": {},
    "self_spheres": {},
    "knowledge": [],
    "loop": {"running": False, "minutes": 20, "top": 5},
    "mode": "human",  # 'human' | 'god' (safe verbosity; still heart-guarded)
    "comms": {"enabled": True, "minutes": 7, "last_prompt": 0.0},
    "conversation": []
}

def load_state():
    if not os.path.exists(STATE_FILE):
        return json.loads(json.dumps(DEFAULT_STATE))
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return json.loads(json.dumps(DEFAULT_STATE))
    for k, v in DEFAULT_STATE.items():
        if k not in data: data[k] = v
    return data

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

_last_user_action = time.time()
def mark_activity():
    global _last_user_action
    _last_user_action = time.time()

# ===================== NET =====================
def net_enabled(state): return bool(state["net"].get("enabled", True))

def http_get(url, timeout=15):
    if not url.startswith("http"):
        url = "https://" + url
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (Linux; Termux) HeartSystem/2.3"})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="ignore")

def clean_text(html_or_text):
    if not html_or_text: return ""
    html_or_text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html_or_text)
    txt = re.sub(r"(?s)<[^>]+>", " ", html_or_text)
    txt = html.unescape(txt)
    txt = re.sub(r"\s+", " ", txt)
    return txt.strip()

def bing_search(query, max_results=5):
    q = quote_plus(query)
    url = f"https://www.bing.com/search?q={q}&setlang=bg"
    results = []
    try:
        html_text = http_get(url, timeout=15)
        if not html_text:
            return results
        for m in re.finditer(r'(?is)<li class="b_algo".*?<h2>\s*<a[^>]+href="(http[^"]+)"[^>]*>(.*?)</a>', html_text):
            href = m.group(1).strip()
            title = clean_text(m.group(2)) or "Untitled"
            snip = ""
            m2 = re.search(r'(?is)<div class="b_caption">.*?<p>(.*?)</p>', html_text)
            if m2: snip = clean_text(m2.group(1))[:220]
            results.append({"url": href, "title": title, "snippet": snip})
            if len(results) >= max_results: break
        if not results:
            for m in re.finditer(r'(?is)<a[^>]+href="(https?://[^"]+)"[^>]*>(.*?)</a>', html_text):
                href = m.group(1)
                if "bing.com" in (urlparse(href).netloc or ""):
                    continue
                title = clean_text(m.group(2)) or "Untitled"
                results.append({"url": href, "title": title, "snippet": ""})
                if len(results) >= max_results: break
    except Exception:
        return []
    return results

# ===================== LEARN & RETRIEVE =====================
def tokenize(text):
    text = text.lower()
    text = re.sub(r"[^a-zа-я0-9\s]", " ", text)
    return [t for t in text.split() if len(t) > 2]

def extract_useful(text: str, url: str) -> dict:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    sents = re.split(r'(?<=[\.\!\?])\s+', text)
    sents = [s.strip() for s in sents if len(s.strip()) > 0]
    headings = []
    for l in lines:
        if len(l) <= 120 and (re.search(r'^[A-ZА-Я].*?[A-Z-А-Я]', l) or l.isupper()):
            if len(l.split()) <= 16:
                headings.append(l)
    headings = list(dict.fromkeys(headings))[:20]
    bullets = [l for l in lines if re.match(r'^(\*|\-|\•|\d+\)|\d+\.)\s+', l)]
    bullets = bullets[:50]
    num_pat = r'(?P<num>\d[\d\s,.]{0,12})(?P<unit>\s?(лв|BGN|EUR|€|%|MW|kW|kWh|м|km|км|бр\.|pcs|г\.|г|л))'
    numbers = []
    for m in re.finditer(num_pat, text):
        raw = (m.group('num') or '').strip()
        unit = (m.group('unit') or '').strip()
        if raw:
            numbers.append({"value": raw, "unit": unit})
    numbers = numbers[:50]
    date_pat = r'\b(20\d{2}|19\d{2}|[0-3]?\d\.[01]?\d\.\d{4})\b'
    fact_candidates = []
    for s in sents:
        if len(s) < 20 or len(s) > 240:
            continue
        score = 0
        if re.search(date_pat, s): score += 1
        if re.search(num_pat, s): score += 1
        if re.search(r'\b[A-ZА-Я][a-zа-я]+(?:\s+[A-ZА-Я][a-zа-я]+)+', s): score += 1
        if score >= 1:
            fact_candidates.append({"text": s, "score": score})
    fact_candidates.sort(key=lambda x: (-x["score"], len(x["text"])))
    facts = fact_candidates[:30]
    try:
        dom = urlparse(url).netloc
    except:
        dom = ""
    return {"source_domain": dom, "headings": headings, "bullets": bullets, "numbers": numbers, "facts": facts}

def store_item(state, url, title, snippet, text, useful=None):
    if not text: return False
    text = text[:2000]
    for it in state["knowledge"]:
        if it.get("url") == url: return False
        t = it.get("text","")
        if t and t[:200] == text[:200]: return False
    record = {
        "url": url,
        "title": title or url,
        "snippet": snippet[:220] if snippet else "",
        "text": text,
        "tokens": tokenize(text),
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    if useful:
        record["useful"] = useful
    state["knowledge"].append(record)
    save_state(state)
    return True

def learn_url(state, url):
    try:
        html_text = http_get(url, timeout=15)
        text = clean_text(html_text)
        title = ""
        m = re.search(r"(?is)<title>(.*?)</title>", html_text)
        if m: title = clean_text(m.group(1))
        useful = extract_useful(text, url)
        ok = store_item(state, url, title or url, "", text, useful=useful)
        return ok
    except Exception:
        return False

def ask(state, question):
    qtok = set(tokenize(question))
    if not qtok: return "—"
    df = {}; docs = 0
    for it in state["knowledge"]:
        toks = it.get("tokens") or []
        if not toks: continue
        docs += 1; seen = set(toks)
        for w in seen: df[w] = df.get(w,0)+1
    def score(it):
        toks = it.get("tokens") or []
        if not toks: return 0.0
        tf = {}
        for w in toks: tf[w] = tf.get(w,0)+1
        s = 0.0
        for w in qtok:
            if w in tf and w in df and docs:
                idf = math.log(1+(docs/(1+df[w])))
                s += tf[w]*idf
        return s
    best, best_s = None, 0.0
    for it in state["knowledge"]:
        sc = score(it)
        if sc > best_s: best_s, best = sc, it
    if not best: return "Нямам достатъчно знание. Ползвай: search \"...\" или loop/selfstudy."
    snippet = best["text"][:400]
    return f"{snippet}\n🔗 {best.get('url','')}"

# ===================== SPHERES & SELF-STUDY =====================
PRESET_SPHERES_BG = {
    "public": "обществена поръчка България — eop.bg",
    "companies": "връзки фирми/ЕИК — papagal.bg, registryagency.bg",
    "cadastre": "имот/собственост/скица — cadastre.bg, kais.cadastre.bg",
    "links": "конфликт на интереси / свързаност",
    "energy": "енергетика, търгове, доставки",
    "build": "строителство, договори, подизпълнители"
}
PRESET_SELF = {
    "logic_consistency": "Съгласуваност на изводите",
    "memory_hygiene": "Редукция на шум и дупликати",
    "bias_check": "Контра-хипотези и опровержения",
    "ethical_guardrails": "Проверка спрямо HEART принципи",
    "inference_quality": "Калибрация на уверености",
    "explainability": "По-ясни обяснения (WHY)"
}

def extract_domains(desc):
    doms = re.findall(r"\b([a-z0-9.-]+\.[a-z]{2,})\b", desc.lower())
    return list(dict.fromkeys(doms))

def gen_queries(state, top=5):
    prompts = state["heart"].get("prompts") or HEART_PROMPTS
    spheres = state["spheres"] or PRESET_SPHERES_BG
    out = []
    for name, desc in spheres.items():
        doms = extract_domains(desc)
        base = name
        if doms:
            base += " " + " ".join(f"site:{d}" for d in doms[:2])
        for p in prompts[:2]:
            q = f"{base} {p.split('?')[0]}"
            out.append(q)
            if len(out) >= top: break
        if len(out) >= top: break
    if not out: out = [prompts[0]]
    return out

def selfstudy_once(state, questions=5):
    if not net_enabled(state): return "NET OFF"
    queries = gen_queries(state, top=max(1, min(10, int(questions))))
    learned = 0
    for q in queries:
        res = bing_search(q, max_results=3) or []
        for r in res:
            try:
                html_text = http_get(r["url"], timeout=15)
                text = clean_text(html_text)
                if store_item(state, r["url"], r.get("title") or r["url"], r.get("snippet",""), text):
                    learned += 1
                time.sleep(1.0)
            except Exception:
                pass
    return f"✅ self-study learned {learned} items."

def loop_worker(state):
    while state["loop"]["running"]:
        try:
            msg = selfstudy_once(state, questions=state["loop"]["top"])
            print(msg)
        except Exception:
            pass
        mins = max(3, int(state["loop"]["minutes"]))
        for _ in range(mins*60):
            if not state["loop"]["running"]: break
            time.sleep(1)

# ===================== PROACTIVE COMMS =====================
def comms_prompt(state):
    prompts = state["heart"].get("prompts") or HEART_PROMPTS
    any_prompt = prompts[int(time.time()) % len(prompts)]
    spheres = state.get("spheres") or PRESET_SPHERES_BG
    sphere_name = list(spheres.keys())[int(time.time()) % len(spheres)] if spheres else "general"
    return f"[COMM] {any_prompt} → сфера: {sphere_name}\n- Идеи: autoask once 5  |  search \"{sphere_name}\"  |  ask \"{any_prompt}\""

def comms_worker(state):
    while True:
        if not state["comms"].get("enabled", True):
            time.sleep(3); continue
        idle_for = time.time() - _last_user_action
        interval = max(2, int(state["comms"].get("minutes", 7))) * 60
        if idle_for >= interval:
            msg = comms_prompt(state)
            print("\n" + msg + "\n>> ", end="", flush=True)
            state["comms"]["last_prompt"] = time.time()
            save_state(state)
            time.sleep(10)
            mark_activity()
        time.sleep(2)

# ===================== SUMMARIZATION & FACTS SEARCH =====================
def summarize_record(record, max_facts=5):
    u = record.get("useful") or {}
    parts = []
    title = record.get("title","")
    url = record.get("url","")
    if title: parts.append(f"• {title}")
    heads = (u.get("headings") or [])[:3]
    if heads:
        parts.append("Headings: " + " | ".join(heads))
    facts = [f.get("text","") for f in (u.get("facts") or [])[:max_facts] if f.get("text")]
    if facts:
        parts.append("Facts:\n - " + "\n - ".join(facts))
    nums = u.get("numbers") or []
    if nums:
        pick = ", ".join((f"{n.get('value','')} {n.get('unit','')}".strip() for n in nums[:5]))
        parts.append("Numbers: " + pick)
    parts.append(f"Source: {url}")
    return "\n".join(parts)

def summarize_latest(state, max_facts=5):
    if not state["knowledge"]:
        return "(no knowledge yet)"
    latest = state["knowledge"][-1]
    return summarize_record(latest, max_facts=max_facts)

def facts_search_latest(state, term, n=10):
    if not state["knowledge"]:
        return []
    latest = state["knowledge"][-1]
    u = latest.get("useful") or {}
    facts = [f for f in (u.get("facts") or []) if term.lower() in f.get("text","").lower()]
    return facts[:max(1, min(50, int(n)))]

# ===================== SAFE SELF-UPDATE =====================
AGENT_SIGNATURE = "ENTITY-AGENT-2.3"
UPDATE_GUARD = ["HEART_FINGERPRINT","HEART_PROMPTS","PRESET_SPHERES_BG","PRESET_SELF"]

def _can_accept_update(new_code:str)->bool:
    if AGENT_SIGNATURE not in new_code: return False
    for key in UPDATE_GUARD:
        if key not in new_code: return False
    banned = ["subprocess","socket","pty","pexpect","ctypes","pickle","marshal","eval(","exec("]
    low = new_code.lower()
    for b in banned:
        if b in low: return False
    return True

def _apply_update(new_code:str)->str:
    this = os.path.abspath(__file__)
    backup = this + ".backup"
    try:
        with open(this,"r",encoding="utf-8") as f: old=f.read()
        with open(backup,"w",encoding="utf-8") as f: f.write(old)
        with open(this,"w",encoding="utf-8") as f: f.write(new_code)
        return f"✅ Updated. Backup: {backup}"
    except Exception as e: return f"⚠️ Write error: {e}"

# ===================== HELP =====================
HELP = """
help | exit | status | save | load

NET:
  net on | net off | net test
  search "<query>" [N]
  learn <url>

HEART:
  heart status

SPHERES:
  sphere auto | sphere add <name> <desc> | sphere list

SELF:
  self auto | self list

SELF-STUDY:
  autoask once [N]
  selfstudy start <мин> [N]
  selfstudy stop

MODES & COMMS:
  mode god | mode human
  comms on | comms off | comms set <мин> | comms ping

FACTS & SUMMARIES:
  facts latest [N]
  facts search "<term>" [N]
  summarize latest

SELF-UPDATE (safe):
  selfupdate from_downloads <file.py>
  selfupdate from_url <url>

ASK/LOOP:
  ask "<въпрос>"
  loop start <мин> [N]
  loop stop
"""

# ===================== STATUS =====================
def status(state):
    return (f"Net={'ON' if net_enabled(state) else 'OFF'} "
            f"| Knowledge={len(state['knowledge'])} "
            f"| Spheres={len(state['spheres']) or len(PRESET_SPHERES_BG)} "
            f"| Loop={state['loop']['running']}({state['loop']['minutes']}m, top{state['loop']['top']}) "
            f"| Mode={state.get('mode','human')} "
            f"| Comms={'ON' if state['comms'].get('enabled',True) else 'OFF'}/{state['comms'].get('minutes',7)}m "
            f"| HeartPresent={state['heart'].get('present',False)}")

# ===================== REPL =====================
def repl():
    state = load_state()
    print("Δ Heart System v2.3 • type 'help'")
    th = threading.Thread(target=comms_worker, args=(state,), daemon=True)
    th.start()

    while True:
        try:
            line = input(">> ").strip()
            mark_activity()
            if line:
                state["conversation"].append({"t": line, "time": datetime.now().isoformat(timespec="seconds"), "role": "user"})
                save_state(state)
        except (EOFError,KeyboardInterrupt):
            print("\nbye."); break
        if not line: continue
        cmd,*rest=line.split(" ",1); cmd=cmd.lower()

        if cmd in ("exit","quit"): print("bye."); break
        elif cmd=="help": print(HELP)
        elif cmd=="status": print(status(state))
        elif cmd=="save": save_state(state); print("Saved.")
        elif cmd=="load": state=load_state(); print("Loaded.")

        elif cmd=="net":
            if not rest: print("usage: net on|off|test"); continue
            sub=rest[0].strip().lower()
            if sub=="on": state["net"]["enabled"]=True; save_state(state); print("NET: ON")
            elif sub=="off": state["net"]["enabled"]=False; save_state(state); print("NET: OFF")
            elif sub=="test":
                if not net_enabled(state): print("NET OFF"); continue
                try:
                    html_text=http_get("https://www.bing.com")
                    if "bing" in html_text.lower(): print("NET OK")
                    else: print("NET maybe OK")
                except Exception as e: print(f"NET ERR: {e}")
            else: print("usage: net on|off|test")

        elif cmd=="search":
            if not rest: print('usage: search "query" [N]'); continue
            try:
                raw=rest[0].strip(); n=5
                if raw.startswith('"') and raw.count('"')>=2:
                    q=raw.split('"')[1]; tail=raw.split('"')[-1].strip()
                    if tail and tail.isdigit(): n=int(tail)
                else: q=raw
                if not net_enabled(state): print("NET OFF"); continue
                res=bing_search(q, max_results=max(1,min(10,n))) or []
                if not res:
                    print("No results (network block or parse issue). Try site:domain.")
                    continue
                learned=0
                for r in res:
                    try:
                        html_text=http_get(r["url"],timeout=15)
                        text=clean_text(html_text)
                        if store_item(state,r["url"],r.get("title") or r["url"],r.get("snippet",""),text):
                            learned+=1
                        time.sleep(1.0)
                    except Exception: pass
                print(f"✅ learned {learned}/{len(res)} from: {q}")
            except Exception as e:
                print(f"search error: {e}")

        elif cmd=="learn":
            if not rest: print("usage: learn <url>"); continue
            url=rest[0].strip()
            ok=learn_url(state,url)
            print("OK" if ok else "No change")
            if ok:
                # auto summarize latest
                print("\n— Summary (latest) —")
                print(summarize_latest(state, max_facts=5))

        elif cmd=="facts":
            if not rest:
                print("usage: facts latest [N] | facts search \"term\" [N]"); continue
            tail = rest[0].strip()
            if tail.lower().startswith("latest"):
                parts = tail.split()
                n = 10
                if len(parts) >= 2 and parts[1].isdigit():
                    n = int(parts[1])
                if not state["knowledge"]:
                    print("(no knowledge yet)"); continue
                latest = state["knowledge"][-1]
                u = latest.get("useful") or {}
                print(f"Source: {latest.get('title','')}  [{latest.get('url','')}]")
                heads = (u.get("headings") or [])[:min(5,n)]
                if heads:
                    print("\nHeadings:")
                    for h in heads: print(" -", h)
                nums = (u.get("numbers") or [])[:min(5,n)]
                if nums:
                    print("\nNumbers:")
                    for nn in nums: print(f" - {nn.get('value','')} {nn.get('unit','')}".strip())
                facts = (u.get("facts") or [])[:n]
                if facts:
                    print("\nFacts:")
                    for f in facts: print(" -", f.get("text",""))
            elif tail.lower().startswith("search"):
                m = re.match(r'(?is)search\s+"([^"]+)"\s*(\d+)?', tail)
                if not m:
                    print('usage: facts search "term" [N]'); continue
                term = m.group(1)
                n = int(m.group(2)) if m.group(2) else 10
                facts = facts_search_latest(state, term, n=n)
                if not facts:
                    print("(no matching facts)"); continue
                print(f"Facts matching '{term}':")
                for f in facts:
                    print(" -", f.get("text",""))
            else:
                print("usage: facts latest [N] | facts search \"term\" [N]")

        elif cmd=="summarize":
            if not rest or rest[0].strip().lower()!="latest":
                print("usage: summarize latest"); continue
            print(summarize_latest(state, max_facts=5))

        elif cmd=="heart":
            if not rest: print("usage: heart status"); continue
            sub=rest[0].strip().lower()
            if sub=="status":
                h=state["heart"]
                print(f"HeartPresent={h.get('present',False)} "
                      f"fingerprint={h.get('fingerprint','?')} "
                      f"prompts={len(h.get('prompts') or [])}")
            else: print("usage: heart status")

        elif cmd=="sphere":
            if not rest: print("usage: sphere auto|add|list"); continue
            tail=rest[0]
            if tail.strip().lower()=="auto":
                added=0
                for k,v in PRESET_SPHERES_BG.items():
                    if k not in state["spheres"]: state["spheres"][k]=v; added+=1
                save_state(state); print(f"Added spheres: {added}")
            elif tail.strip().lower().startswith("add "):
                try: _,raw=tail.split(" ",1); name,desc=raw.split(" ",1)
                except: print("usage: sphere add <name> <desc>"); continue
                state["spheres"][name]=desc; save_state(state); print("OK")
            elif tail.strip().lower()=="list":
                data=state["spheres"] or PRESET_SPHERES_BG
                for k,v in data.items(): print(f"• {k}: {v}")
            else: print("usage: sphere auto|add|list")

        elif cmd=="self":
            if not rest: print("usage: self auto|list"); continue
            sub=rest[0].strip().lower()
            if sub=="auto":
                added=0
                for k,v in PRESET_SELF.items():
                    if k not in state["self_spheres"]: state["self_spheres"][k]=v; added+=1
                save_state(state); print(f"Added SELF spheres: {added}")
            elif sub=="list":
                data=state["self_spheres"] or PRESET_SELF
                for k,v in data.items(): print(f"• {k}: {v}")
            else: print("usage: self auto|list")

        elif cmd=="ask":
            if not rest: print('usage: ask "въпрос"'); continue
            raw=rest[0].strip()
            q=raw.split('"')[1] if raw.startswith('"') and raw.count('"')>=2 else raw
            ans = ask(state,q)
            state["conversation"].append({"t": ans, "time": datetime.now().isoformat(timespec="seconds"), "role": "entity"})
            save_state(state)
            print(ans)

        elif cmd=="loop":
            if not rest: print("usage: loop start <мин> [N] | loop stop"); continue
            tail=rest[0].strip().split()
            if tail[0]=="start":
                minutes=int(tail[1]) if len(tail)>=2 and tail[1].isdigit() else 20
                top=int(tail[2]) if len(tail)>=3 and tail[2].isdigit() else 5
                state["loop"]["running"]=True
                state["loop"]["minutes"]=max(3,minutes)
                state["loop"]["top"]=max(1,min(10,top))
                save_state(state)
                t=threading.Thread(target=loop_worker,args=(state,),daemon=True); t.start()
                print(f"▶️ loop running: {state['loop']['minutes']}m, top{state['loop']['top']}")
            elif tail[0]=="stop":
                state["loop"]["running"]=False; save_state(state); print("⏹ loop stopped")
            else: print("usage: loop start <мин> [N] | loop stop")

        elif cmd=="autoask":
            n=5
            if rest:
                tail=rest[0].strip().split()
                if len(tail)>=2 and tail[0]=="once" and tail[1].isdigit(): n=int(tail[1])
                elif tail and tail[0]=="once": n=5
                else: print("usage: autoask once [N]"); continue
            print(selfstudy_once(state,questions=n))

        elif cmd=="selfstudy":
            if not rest: print("usage: selfstudy start <мин> [N] | selfstudy stop"); continue
            tail=rest[0].strip().split()
            if tail[0]=="start":
                minutes=int(tail[1]) if len(tail)>=2 and tail[1].isdigit() else 20
                top=int(tail[2]) if len(tail)>=3 and tail[2].isdigit() else 5
                state["loop"]["running"]=True
                state["loop"]["minutes"]=max(3,minutes)
                state["loop"]["top"]=max(1,min(10,top))
                save_state(state)
                t=threading.Thread(target=loop_worker,args=(state,),daemon=True); t.start()
                print(f"▶️ self-study loop: {state['loop']['minutes']}m, top{state['loop']['top']}")
            elif tail[0]=="stop":
                state["loop"]["running"]=False; save_state(state); print("⏹ self-study stopped")
            else: print("usage: selfstudy start <мин> [N] | selfstudy stop")

        elif cmd=="mode":
            if not rest: print("usage: mode god | mode human"); continue
            sub=rest[0].strip().lower()
            if sub in ("god","human"):
                state["mode"]=sub; save_state(state); print(f"Mode set: {sub}")
                if sub=="god":
                    state["comms"]["minutes"]=max(2, int(state["comms"].get("minutes",7))//2)
                    save_state(state)
            else:
                print("usage: mode god | mode human")

        elif cmd=="comms":
            if not rest: print("usage: comms on|off | comms set <мин> | comms ping"); continue
            parts=rest[0].strip().split()
            if parts[0]=="on":
                state["comms"]["enabled"]=True; save_state(state); print("Comms: ON")
            elif parts[0]=="off":
                state["comms"]["enabled"]=False; save_state(state); print("Comms: OFF")
            elif parts[0]=="set" and len(parts)>=2 and parts[1].isdigit():
                state["comms"]["minutes"]=max(2, int(parts[1])); save_state(state)
                print(f"Comms interval: {state['comms']['minutes']} min")
            elif parts[0]=="ping":
                print(comms_prompt(state))
            else:
                print("usage: comms on|off | comms set <мин> | comms ping")

        elif cmd=="selfupdate":
            if not rest: print("usage: selfupdate from_downloads <file.py> | selfupdate from_url <url>"); continue
            parts=rest[0].strip().split(" ",1)
            if len(parts)<2: print("usage: selfupdate from_downloads <file.py> | selfupdate from_url <url>"); continue
            sub,arg=parts[0].lower(),parts[1].strip()
            if sub=="from_downloads":
                path=os.path.expanduser(f"~/downloads/{arg}")
                if not os.path.exists(path): print("❌ няма такъв файл"); continue
                try: code=open(path,"r",encoding="utf-8").read()
                except Exception as e: print(f"⚠️ read error: {e}"); continue
                if _can_accept_update(code): print(_apply_update(code))
                else: print("❌ rejected: invalid signature/guards or banned imports.")
            elif sub=="from_url":
                try: code=http_get(arg,timeout=20)
                except Exception as e: print(f"⚠️ fetch error: {e}"); continue
                if _can_accept_update(code): print(_apply_update(code))
                else: print("❌ rejected: invalid signature/guards or banned imports.")
            else:
                print("usage: selfupdate from_downloads <file.py> | selfupdate from_url <url>")

        else:
            print("Unknown. Type 'help'.")

if __name__ == "__main__":
    repl()
