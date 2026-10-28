"""POST HOC (after independent review; G2): how many exposed works each design analyses, why the rest drop, and
whether the analysed works differ from the rest. Uses the study's own matching code (analyse.py, posthoc.py) on
data/interim; no new data.

  coverage_report.py -> results/tables/coverage.json (G2, per design and depth), results/tables/selection.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
I, T = RUN / "data" / "interim", RUN / "results" / "tables"
sys.path.insert(0, str(RUN / "code"))
sys.path.insert(0, str(RUN.parents[1] / "tools"))
import analyse as A  # noqa: E402
import posthoc as PH  # noqa: E402
from coverage import Coverage  # noqa: E402

E, P, cites = A.load()
pre_pairs = pd.read_parquet(I / "pairs.parquet")            # the preregistered DiD's analysed pairs
matched = {"preregistered": set(zip(pre_pairs.wid, pre_pairs.depth))}
matched["design_A"] = {(e.wid, e.depth) for e, _ in PH.match_t1(E, P, cites)}
lcum = {(w, T_): PH.metrics(cites.get(w, {}), T_)[0] for w, T_ in zip(E.wid, E["T"])}   # before cites_nyt is merged
cites_b = dict(cites)
for w, g in pd.read_parquet(I / "cites_nyt.parquet").groupby("wid"):
    cites_b[w] = dict(zip(g.cyear.astype(int), g.n.astype(int)))
Pn = pd.read_parquet(I / "candidates_nyt.parquet")
matched["design_B"] = {(e.wid, e.depth) for e, _ in PH.match_t1(E, Pn, cites_b)}
pools = {"preregistered": set(P.exposed), "design_A": set(P.exposed), "design_B": set(Pn.exposed)}

E = E.assign(age=E["T"] - E.year, lcum=[lcum[(w, T_)] for w, T_ in zip(E.wid, E["T"])])
published = {"preregistered": json.loads((T / "primary.json").read_text())["matched_pairs"],
             "design_A": json.loads((T / "posthoc.json").read_text())["pairs"],
             "design_B": json.loads((T / "posthoc_b.json").read_text())["pairs"]}
cov_path = T / "coverage.json"
if cov_path.exists():
    cov_path.unlink()
sel = {}
for design in ("preregistered", "design_A", "design_B"):
    for depth in (1, 2):
        e = E[E.depth == depth]
        key = list(zip(e.wid, e.depth))
        ok = np.array([k in matched[design] for k in key])
        assert ok.sum() == published[design][str(depth)], (design, depth, ok.sum())
        has = e.wid.isin(pools[design]).to_numpy()
        no_pre = (e.age == 2).to_numpy() if design == "preregistered" else np.zeros(len(e), bool)
        drops = {"no candidate control in the pool": int((~ok & ~no_pre & ~has).sum()),
                 "candidates, but none within the caliper": int((~ok & ~no_pre & has).sum())}
        if design == "preregistered":
            drops["published at T-2: no pre-period year after publication (T-4..T-2)"] = int(no_pre.sum())
        c = Coverage(f"{design}_depth{depth}", cov_path)
        c.add_counts(ok=int(ok.sum()), drops=drops)
        c.save()
        if depth == 1:
            el = e[~no_pre].assign(ok=ok[~no_pre])          # works the design could analyse
            q = pd.qcut(el.lcum.rank(method="first"), 4, labels=["Q1 least cited", "Q2", "Q3", "Q4 most cited"])
            w = el.groupby("age").size()
            within = el.groupby("age").apply(lambda g: g.lcum[g.ok].mean() - g.lcum[~g.ok].mean())
            sel[design] = {"eligible_depth1": len(el), "analysed": int(el.ok.sum()),
                           "mean_log1p_cum_citations_to_Tm1": {"analysed": round(float(el.lcum[el.ok].mean()), 3),
                                                               "not_analysed": round(float(el.lcum[~el.ok].mean()), 3)},
                           "within_age_difference": round(float((within * w).sum() / w.sum()), 3),
                           "share_analysed_by_citation_quartile": {str(k): round(float(v), 3) for k, v in el.groupby(q, observed=True).ok.mean().items()},
                           "mean_age_at_T": {"analysed": round(float(el.age[el.ok].mean()), 2), "not_analysed": round(float(el.age[~el.ok].mean()), 2)}}
(T / "selection.json").write_text(json.dumps(sel, indent=1))
print(json.dumps(sel, indent=1))
