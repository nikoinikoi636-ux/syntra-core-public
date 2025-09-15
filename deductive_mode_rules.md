# Deductive Mode — HeartClean (Operational Add‑On)
Generated: 2025-08-15 22:16 UTC

**Goal:** Turn raw facts → defensible conclusions via strict deduction. No leaps, no rumors.

## Core Loop (D.E.D.U.C.E.)
1) **Define** a precise hypothesis (H): e.g., "Entities X and Y act in concert on tenders in sector S."
2) **Expectations** (E): If H is true, we should see {"E1: shared addresses"}, {"E2: repeated co‑bids"}, {"E3: tender edits favoring duo"}, etc.
3) **Data**: Pull only public records (TRR/Registry Agency, EOP/SEAP, KAIS, media with documents).
4) **Unify**: Normalize to CSV (entities/links/procurement/properties).
5) **Check**: Test E1..È; mark pass/fail; count falsifiers.
6) **Explain**: Draft a short argument with citations + a "falsify" section (what would disprove it).

## Indicators → Tests
- **ADDRESS_CLUSTER** → ≥3 EIKs share one address across ≥2 years ⇒ verify via TR and archived copies.
- **CO_BIDDER_LOOP** → same suppliers co‑bid ≥3 times, limited competition ⇒ pull EOP results + dates.
- **EXCESSIVE_MODS** → contract modified ≥2× or >20% value ⇒ parse EOP mod logs.
- **TIMED_TRANSFER** → ownership changes ±60d around big awards ⇒ TR event timeline vs award dates.
- **REVENUE_STAFF_MISMATCH** → spike in revenue without staff change ⇒ GFO vs NSI.
- **UNDERVALUED_TRANSFER** → property price ≪ market comps (if public) ⇒ KAIS + notaries (public excerpts).

## Output Artifacts
- **DEDUCTIVE_SCORECARD.csv** — ranked entities by evidence-backed risk signals.
- **HYPOTHESES.md** — template-filled with tests & falsifiers.
- **NEXT_ACTIONS.md** — concrete pulls (which doc where).

> Ethics: Facts ≠ guilt. Use "indicator suggests", "evidence shows", not accusations. Hand off to institutions.