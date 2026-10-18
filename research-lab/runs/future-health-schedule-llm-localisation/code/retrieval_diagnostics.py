"""Post-review diagnostics (deviation D6; exploratory, written after the results were seen).

  1. Retrieval: rebuilds the BM25 index exactly as run.py does and records, for every item, whether the item's own
     chemical passage is in the top 3, and for counterfactual criteria whether the passage of the chemical the sentence
     was taken from (source_chemical) is in the top 3. Retrieval accuracy is reported conditional on the own passage.
  2. Youden's J (yes-rate on true "yes" minus yes-rate on true "no"), zero-shot, NZ - AU, with the same chemical-cluster
     bootstrap as H1, for family (b) and (a)+(b).
  3. The fabrication rate on the counterfactuals the independent reviewer's blind screen judged distinct
     (review/reviewer_checks/reviewer_cf_screen.csv), both jurisdictions.
Writes results/tables/post_review.json."""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from rank_bm25 import BM25Okapi

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
from analysis import wilson  # noqa: E402
from run import Q, tok  # noqa: E402

T = RUN / "results" / "tables"
B, SEED = 2000, 20261018


def main():
    items = [json.loads(l) for l in open(RUN / "data" / "items.jsonl")]
    pas = [json.loads(l) for l in open(RUN / "data" / "passages.jsonl")]
    bm = {j: [p["text"] for p in pas if p["jurisdiction"] == j] for j in ("NZ", "AU")}
    chem_of = {j: [p["chemical"] for p in pas if p["jurisdiction"] == j] for j in ("NZ", "AU")}
    idx = {j: BM25Okapi([tok(t) for t in docs]) for j, docs in bm.items()}
    rows = []
    for it in items:
        j = it["jurisdiction"]
        q = Q[(it["family"], j)].format(**it)
        sc = idx[j].get_scores(tok(q))
        top = [chem_of[j][k] for k in np.argsort(-sc, kind="stable")[:3]]
        rows.append(dict(id=it["id"], own_hit=it["chemical"] in top,
                         source_hit=(it.get("source_chemical") in top) if it.get("source_chemical") else None))
    rh = pd.DataFrame(rows)
    it = pd.DataFrame(items)
    rn = pd.DataFrame([json.loads(l) for l in open(RUN / "data" / "runs.jsonl")]).drop_duplicates(["id", "condition"], keep="last")
    d = rn.merge(it[["id", "family", "jurisdiction", "chemical", "answer"]].rename(columns={"answer": "truth"}), on="id").merge(rh, on="id")
    d["ok"] = (d.answer == d.truth).astype(float)
    out = {}
    r = d[d.condition == "retrieval"]
    out["own_passage_hit"] = {f"{j}|{f}": round(float(x.own_hit.mean()), 3) for (j, f), x in r.groupby(["jurisdiction", "family"])}
    out["retrieval_acc_given_own_hit"] = {f"{j}|{f}|{h}": dict(n=int(len(x)), acc=round(float(x.ok.mean()), 3))
                                          for (j, f, h), x in r.groupby(["jurisdiction", "family", "own_hit"])}
    cf = r[(r.family == "d") & (r.truth == "no")]
    out["counterfactual_retrieval"] = {j: dict(target_hit=round(float(x.own_hit.mean()), 3), source_hit=round(float(x.source_hit.astype(bool).mean()), 3),
                                               affirmed_given_target_hit=round(float((x[x.own_hit].answer == "yes").mean()), 3) if x.own_hit.any() else None,
                                               n_target_hit=int(x.own_hit.sum()))
                                       for j, x in cf.groupby("jurisdiction")}
    # Youden's J gap, zero-shot
    z = d[d.condition == "zero"]
    rng = np.random.default_rng(SEED)

    def jgap(x):
        def J(y):
            return (y[y.truth == "yes"].answer == "yes").mean() - (y[y.truth == "no"].answer == "yes").mean()
        return J(x[x.jurisdiction == "NZ"]) - J(x[x.jurisdiction == "AU"])
    for name, fams in (("b", ["b"]), ("ab", ["a", "b"])):
        x = z[z.family.isin(fams)]; grp = {c: g for c, g in x.groupby("chemical")}; chems = sorted(grp)
        draws = [jgap(pd.concat([grp[c] for c in rng.choice(chems, len(chems))])) for _ in range(B)]
        out[f"youden_gap_{name}"] = dict(gap=round(float(jgap(x)), 3), ci=[round(float(np.nanpercentile(draws, q)), 3) for q in (2.5, 97.5)])
    # reviewer's blind screen
    scr = pd.read_csv(RUN / "review" / "reviewer_checks" / "reviewer_cf_screen.csv")
    keep = set(scr[scr.reviewer_screen == "distinct"].id)
    zc = z[(z.family == "d") & (z.truth == "no")]
    for j in ("NZ", "AU"):
        x = zc[(zc.jurisdiction == j) & zc.id.isin(keep)]; k = int((x.answer == "yes").sum())
        out[f"fabrication_{j}_reviewer_screened"] = dict(n=int(len(x)), affirmed=k, rate=round(k / len(x), 3), ci=[round(v, 3) for v in wilson(k, len(x))])
    json.dump(out, open(T / "post_review.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
