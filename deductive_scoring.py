#!/usr/bin/env python3
# deductive_scoring.py — rank entities & generate hypothesis skeletons from out_kit CSVs
import csv, os, argparse, collections, datetime, json

def read_csv(path):
    if not os.path.exists(path): return []
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def norm_id(v): return (v or "").strip()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="indir", default="../HeartClean_Harvester/out_kit")
    args = ap.parse_args()
    indir = args.indir

    ents = read_csv(os.path.join(indir, "entities.csv"))
    rels = read_csv(os.path.join(indir, "relationships.csv"))
    procs = read_csv(os.path.join(indir, "procurement.csv"))
    risks = read_csv(os.path.join(indir, "risk_findings.csv"))

    # Build degree & indicators per entity (EIK-level where possible)
    score = collections.defaultdict(lambda: {"degree":0,"indicators":set(),"addresses":set(),"cpv":set(),"awards":0})
    eik_to_name = {}

    for e in ents:
        eik = norm_id(e.get("eik"))
        name = e.get("entity_name","")
        addr = e.get("registered_address","").strip()
        if eik:
            eik_to_name[eik] = name or eik_to_name.get(eik, "")
            if addr: score[eik]["addresses"].add(addr)

    for r in rels:
        a = norm_id(r.get("from_id"))
        b = norm_id(r.get("to_id"))
        if a: score[a]["degree"] += 1
        if b: score[b]["degree"] += 1

    for p in procs:
        for eik in (p.get("supplier_eik","") or "").split(";"):
            ek = norm_id(eik)
            if ek:
                score[ek]["awards"] += 1
                cpv = (p.get("cpv","") or "").strip()
                if cpv: score[ek]["cpv"].add(cpv)

    for r in risks:
        key = r.get("item_id") or r.get("evidence_links") or ""
        ind = r.get("indicator","").strip()
        # if item_id happens to be an EIK, capture; else attach to all seen
        tgt = r.get("item_id","")
        if tgt and tgt in score:
            score[tgt]["indicators"].add(ind)
        else:
            # global indicator — skip assigning
            pass

    rows = []
    for eik, s in score.items():
        rows.append({
            "eik": eik,
            "name_hint": eik_to_name.get(eik,""),
            "degree": s["degree"],
            "awards": s["awards"],
            "cpv_count": len(s["cpv"]),
            "address_count": len(s["addresses"]),
            "indicator_count": len(s["indicators"]),
            "risk_score": s["degree"]*1.5 + s["awards"]*2 + len(s["cpv"])*0.5 + len(s["addresses"])
        })
    rows.sort(key=lambda r: r["risk_score"], reverse=True)

    out_csv = os.path.join(indir, "DEDUCTIVE_SCORECARD.csv")
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["eik","name_hint","degree","awards","cpv_count","address_count","indicator_count","risk_score"])
        wr.writeheader()
        for r in rows: wr.writerow(r)

    # Hypotheses file (skeletons for top 10)
    top = rows[:10]
    lines = ["# Hypotheses (skeletons)\nGenerated: " + datetime.datetime.utcnow().isoformat()+"Z\n"]
    for r in top:
        eik = r["eik"]; name = r["name_hint"] or "(unknown name)"
        lines += [
            f"\n## H:{eik} {name}",
            "- Claim: Possible coordination or undue advantage in tenders.",
            "- Expectations:",
            "  - E1: Repeated co-bids or sole-source awards in CPV seen above.",
            "  - E2: Ownership/management overlaps around award dates.",
            "  - E3: Address/asset overlaps (TR/KAIS).",
            "- Tests: Pull EOP award/mod logs; TR ownership timeline; KAIS addresses match.",
            "- Falsifiers: Competitors vary; no temporal overlap; addresses unrelated.",
            "- Next Docs: EOP notice PDFs; TR event history; archived company pages."
        ]
    with open(os.path.join(indir, "HYPOTHESES.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # Next actions file
    nxt = [
        "# Next Actions",
        "- For top 5 EIKs in DEDUCTIVE_SCORECARD.csv:",
        "  1) Pull EOP award + modification history (PDFs)",
        "  2) Export TR event timelines (ownership/director changes)",
        "  3) KAIS: check address matches and property encumbrances",
        "  4) Media: search for documented reports (attach URLs + screenshots + SHA256)",
    ]
    with open(os.path.join(indir, "NEXT_ACTIONS.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(nxt))

    print("Wrote:", out_csv, "HYPOTHESES.md", "NEXT_ACTIONS.md")

if __name__ == "__main__":
    main()