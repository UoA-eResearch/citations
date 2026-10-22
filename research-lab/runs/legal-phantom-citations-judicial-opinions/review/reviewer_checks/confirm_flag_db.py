"""Confirmation pass: re-derive analysis.flag_vs_database() without the degenerate database captions.

norm_name() keeps only [a-z0-9], so a Cyrillic caption (e.g. "ООО «Точка опоры» v. ООО «ЦСС»") normalises to "v",
and party_score() then falls through to token_set_ratio("v", name), which is 100 for any corpus name containing a
standalone "v". This script (1) counts such captions among the "US in-window" rows, (2) recomputes the best
date-free name match for each of the 43 flag clusters against captions with at least one real token, and
(3) for clusters that fail the 85 threshold, lists every database row (all 2,203, any country, any date) that shares
a distinctive token with the cluster name, so the "in the database" claim can be checked by hand.
"""
import csv, json, sys
from pathlib import Path
import numpy as np
from rapidfuzz import fuzz

RUN = Path("/mnt/citations/research-lab/runs/legal-phantom-citations-judicial-opinions")
sys.path.insert(0, str(RUN / "code"))
from match_charlotin import NON_US, WIN_FROM, WIN_TO, MATCH  # noqa: E402
from namenorm import norm_name, party_score, tokens_of  # noqa: E402

rows_all = list(csv.DictReader(open(RUN / "data" / "raw" / "charlotin.csv", encoding="utf-8")))
db = [r for r in rows_all if not NON_US.search(r["Court"] + " " + r.get("State(s)", ""))
      and WIN_FROM <= (r["Date"] or "") <= WIN_TO]
degenerate = [r for r in db if not (tokens_of(norm_name(r["Case Name"])))]
print("US in-window rows (matcher's filter):", len(db))
print("rows whose caption has no indexable token:", len(degenerate))
for r in degenerate:
    print("   ", repr(norm_name(r["Case Name"])), "|", r["Case Name"][:50], "|", r["Court"][:40], "|", r.get("State(s)"), r["Date"])
states = {}
for r in db:
    states[r.get("State(s)", "")] = states.get(r.get("State(s)", ""), 0) + 1
print("State(s) values among the 'US' rows:", states)

names = np.load(RUN / "data" / "index" / "names.npy", allow_pickle=True)
ids = np.load(RUN / "data" / "index" / "cluster_meta.npz")["ids"]
pos = {int(c): i for i, c in enumerate(ids)}
fvd = list(csv.DictReader(open(RUN / "results" / "tables" / "flag_vs_database.csv")))
good = [(r, norm_name(r["Case Name"])) for r in db if tokens_of(norm_name(r["Case Name"]))]
out = []
for f in fvd:
    c = int(f["cluster_id"])
    nm = norm_name(str(names[pos[c]]))
    best = max(((party_score(fuzz, d, nm), i) for i, (r, d) in enumerate(good)), default=(0, None))
    rec = {"cluster_id": c, "name": nm, "by_cluster": f["by_cluster"] == "True", "reported_by_name": f["by_name"] == "True",
           "reported_best": f["best_case"], "recomputed_best_score": round(best[0], 1),
           "recomputed_best_case": good[best[1]][0]["Case Name"] if best[1] is not None else "",
           "recomputed_best_court_date": (good[best[1]][0]["Court"] + " " + good[best[1]][0]["Date"]) if best[1] is not None else "",
           "by_name_recomputed": best[0] >= MATCH}
    if not rec["by_cluster"] and not rec["by_name_recomputed"]:
        toks = {t for t in tokens_of(nm) if len(t) >= 5 and t not in {"county", "state", "school", "schools", "bank",
                "national", "association", "department", "services", "company", "corporation", "insurance", "united",
                "states", "trustees", "board", "city", "human", "group", "trustee", "holders", "behalf", "indiana",
                "oregon", "america", "digital", "staffing", "financial", "mortgage", "solutions", "information",
                "children", "individuals", "their", "detroit", "safety", "engineering", "environment", "buildings",
                "wells", "fargo", "clinton", "fund", "funding", "federal", "credit", "union", "university", "health",
                "system", "legal", "capital", "investments", "foundation", "holdings"}}
        hits = []
        for r in rows_all:
            dn = norm_name(r["Case Name"])
            if toks & tokens_of(dn):
                hits.append({"case": r["Case Name"][:90], "court": r["Court"][:40], "date": r["Date"], "party": r["Party(ies)"],
                             "score": round(party_score(fuzz, dn, nm), 1)})
        hits.sort(key=lambda h: -h["score"])
        rec["hand_search_tokens"] = sorted(toks)
        rec["hand_search_hits"] = hits[:8]
    out.append(rec)

print("\n=== recomputed name match for the 43 flag clusters ===")
for r in out:
    print(f"{r['cluster_id']} cl={int(r['by_cluster'])} rep_name={int(r['reported_by_name'])} recomputed={r['recomputed_best_score']:5.1f} name_ok={int(r['by_name_recomputed'])} | {r['name'][:55]} | {r['recomputed_best_case'][:50]} | {r['recomputed_best_court_date'][:30]}")
    if "hand_search_hits" in r:
        print("      tokens:", r["hand_search_tokens"])
        for h in r["hand_search_hits"]:
            print(f"      {h['score']:5.1f} {h['case'][:70]} | {h['court']} {h['date']} | {h['party']}")
n_cl = sum(r["by_cluster"] for r in out)
n_nm = sum((not r["by_cluster"]) and r["by_name_recomputed"] for r in out)
n_rep = sum((not r["by_cluster"]) and r["reported_by_name"] for r in out)
print(f"\nby cluster {n_cl}; by name only: reported {n_rep}, recomputed {n_nm}; unresolved by code {len(out) - n_cl - n_nm}")
json.dump({"us_in_window": len(db), "degenerate_captions": len(degenerate), "states": states, "clusters": out},
          open(RUN / "review" / "reviewer_checks" / "confirm_flag_db.json", "w"), indent=1, ensure_ascii=False)
