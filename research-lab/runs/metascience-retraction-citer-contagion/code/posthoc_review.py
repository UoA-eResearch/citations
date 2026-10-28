"""POST HOC (after independent review, finding 1): where the gap between exposed works and their controls opens, and
what design A's "jump at T" is. The study's own matching code (analyse.py, posthoc.py); no new data. Depth 1.

  1. Preregistered pairs (the analysed ones, published by T-3): the raw exposed-minus-control gap in log1p citations
     by event year, to see where it opens relative to the matching year T-2.
  2. Designs A and B: change in the gap from T-1, by event year, split by when the exposed work was published
     (T-2, T-3, T-4 or earlier).
  3. The same exposed works under both control groups: the A and B effects on depth-1 works matched in both.
  4. Levels, preregistered pairs: exposed and control log1p citations by event year (which side moves).
  5. Exposed works against their whole candidate pools (clean, and not-yet-treated), unmatched: log1p cumulative
     citations to T+4, exposed minus the pool mean.
  All means are retraction-weighted (within retraction, then across), as in the study.

  posthoc_review.py -> results/tables/posthoc_review.json, results/tables/gap_profiles.csv
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
I = RUN / "data" / "interim"
sys.path.insert(0, str(RUN / "code"))
import analyse as A  # noqa: E402
import posthoc as PH  # noqa: E402


def gaps(pairs, cites, design):
    out = []
    for e, c in pairs:
        age = e.T - e.year
        if e.depth != 1 or (design == "preregistered" and age < 3):   # the preregistered DiD drops T-2 works
            continue
        ce, cc = cites.get(e.wid, {}), cites.get(c, {})
        g = {t: np.log1p(ce.get(t, 0)) - np.log1p(cc.get(t, 0)) for t in range(e.T - 4, e.T + 5)}
        pub = "T-2" if age == 2 else "T-3" if age == 3 else "T-4 or earlier"
        for k in range(-4, 5):
            if e.T + k >= e.year + 1:
                t = e.T + k
                out.append((design, e.wid, e.ret, e.cls, pub, k, g[t], g[t] - g[e.T - 1], np.log1p(ce.get(t, 0)), np.log1p(cc.get(t, 0))))
    return pd.DataFrame(out, columns=["design", "wid", "ret", "cls", "published", "k", "gap", "change_from_Tm1", "exposed", "control"])


def pool_gap(E, P, cites):
    """Depth 1: exposed log1p(cumulative citations to T+4) minus the mean over its whole candidate pool."""
    cand = P.groupby("exposed").cand.apply(list)
    cum = lambda c, T: np.log1p(sum(n for y, n in c.items() if y <= T + 4))
    rows = [(e.ret, cum(cites.get(e.wid, {}), e.T) - np.mean([cum(cites.get(c, {}), e.T) for c in cand.loc[e.wid]]))
            for e in E[E.depth == 1].itertuples() if e.wid in cand.index]
    d = pd.DataFrame(rows, columns=["ret", "gap"])
    return {"exposed_works": len(d), "retractions": int(d.ret.nunique()), "gap": round(float(d.groupby("ret").gap.mean().mean()), 4)}


def weighted(G, by, col):
    return G.groupby(by + ["ret"])[col].mean().groupby(by).agg(["mean", "count"]).reset_index()


def effects(G):
    """Per pair: mean change from T-1 over T+1..T+4 (the design-A/B effect)."""
    R = G[G.k >= 1].groupby(["wid", "ret", "cls"]).change_from_Tm1.mean().rename("did").reset_index()
    return R.assign(depth=1)


def main():
    rng = np.random.default_rng(A.SEED + 21)
    E, P, cites = A.load()
    G = [gaps(A.match(E, P, cites), cites, "preregistered"), gaps(PH.match_t1(E, P, cites), cites, "design_A")]
    cites_b = dict(cites)
    for w, g in pd.read_parquet(I / "cites_nyt.parquet").groupby("wid"):
        cites_b[w] = dict(zip(g.cyear.astype(int), g.n.astype(int)))
    G.append(gaps(PH.match_t1(E, pd.read_parquet(I / "candidates_nyt.parquet"), cites_b), cites_b, "design_B"))
    G = pd.concat(G, ignore_index=True)
    prof = pd.concat([weighted(G, ["design", "k"], "gap").assign(published="all", measure="gap"),
                      weighted(G, ["design", "k"], "change_from_Tm1").assign(published="all", measure="change_from_Tm1"),
                      weighted(G, ["design", "published", "k"], "change_from_Tm1").assign(measure="change_from_Tm1")])
    prof.to_csv(A.TAB / "gap_profiles.csv", index=False)

    out = {"pool_gap_clean": pool_gap(E, P, cites),
           "pool_gap_not_yet_treated": pool_gap(E, pd.read_parquet(I / "candidates_nyt.parquet"), cites_b)}
    pub = {"A": json.loads((A.TAB / "posthoc.json").read_text())["depth1"]["effect"],
           "B": json.loads((A.TAB / "posthoc_b.json").read_text())["depth1"]["effect"]}
    RA, RB = effects(G[G.design == "design_A"]), effects(G[G.design == "design_B"])
    for name, R in (("A", RA), ("B", RB)):                       # reproduction check against the published effect
        est = float(A.ret_means(R).did.mean())
        assert abs(est - pub[name]) < 5e-5, (name, est, pub[name])
    both = set(RA.wid) & set(RB.wid)
    out["same_works"] = {"exposed_works": len(both)}
    for name, R in (("design_A_clean_controls", RA), ("design_B_not_yet_treated_controls", RB)):
        est, ci, n = A.boot_mean(A.ret_means(R[R.wid.isin(both)]), rng)
        out["same_works"][name] = {"effect": round(est, 4), "ci": [round(x, 4) for x in ci], "retractions": n}
    sub = G[G.design != "preregistered"]
    for d in ("design_A", "design_B"):
        x = weighted(sub[sub.design == d], ["published", "k"], "change_from_Tm1")
        n = sub[(sub.design == d) & (sub.k == 0)].groupby("published").size()
        out[f"{d}_change_from_Tm1_by_published"] = {
            p: {"pairs": int(n.get(p, 0)), **{f"T{k:+d}": round(float(x[(x.published == p) & (x.k == k)]["mean"].iloc[0]), 4) for k in range(0, 5)}}
            for p in ("T-2", "T-3", "T-4 or earlier")}
    g = weighted(G[G.design == "preregistered"], ["k"], "gap")
    out["preregistered_raw_gap_by_event_year"] = {f"T{k:+d}" if k else "T": round(float(g[g.k == k]["mean"].iloc[0]), 4) for k in range(-4, 5)}
    pre = G[G.design == "preregistered"]
    full = pre.groupby("wid").k.transform("count") == 9                  # balanced panel: published by T-5
    lv = {c: weighted(pre[full], ["k"], c) for c in ("exposed", "control")}
    out["preregistered_levels_balanced_panel"] = {"pairs": int(pre[full].wid.nunique()), **{
        f"T{k:+d}" if k else "T": {c: round(float(lv[c][lv[c].k == k]["mean"].iloc[0]), 3) for c in lv} for k in range(-4, 5)}}
    (A.TAB / "posthoc_review.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
