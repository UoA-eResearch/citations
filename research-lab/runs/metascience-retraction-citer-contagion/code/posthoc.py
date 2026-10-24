"""Post hoc (after primary.json showed a pre-trend: exposed works outgrow controls between T-2 and T-1).

Re-match on the trajectory up to T-1 (log1p cumulative citations by T-1, log1p citations in T-1 and in T-2; caliper
0.25 on each) and measure divergence after the retraction: mean difference over T+1..T+4 minus the difference in T-1.
-> results/tables/posthoc.json, event_profile_t1.csv
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyse as A  # noqa: E402


def metrics(c, T):
    cum = sum(n for y, n in c.items() if y <= T - 1)
    return np.log1p(cum), np.log1p(c.get(T - 1, 0)), np.log1p(c.get(T - 2, 0))


def match_t1(E, P, cites):
    cand = P.groupby("exposed").cand.apply(list)
    pairs = []
    for e in E.itertuples():
        if e.wid not in cand.index or e.year > e.T - 2:
            continue
        m0 = np.array(metrics(cites.get(e.wid, {}), e.T))
        best, bd = None, np.inf
        for c in cand.loc[e.wid]:
            m = np.array(metrics(cites.get(c, {}), e.T))
            if np.all(np.abs(m - m0) <= A.CAL):
                d = float(((m - m0) ** 2).sum())
                if d < bd:
                    best, bd = c, d
        if best is not None:
            pairs.append((e, best))
    return pairs


def rows(pairs, cites):
    out, prof = [], []
    for e, c in pairs:
        ce, cc = cites.get(e.wid, {}), cites.get(c, {})
        diff = {t: np.log1p(ce.get(t, 0)) - np.log1p(cc.get(t, 0)) for t in range(e.T - 4, e.T + 5)}
        eff = np.mean([diff[t] for t in range(e.T + 1, e.T + 5)]) - diff[e.T - 1]
        out.append({"ret": e.ret, "depth": e.depth, "cls": e.cls, "did": eff})
        for k in range(-4, 5):
            if e.T + k >= e.year + 1:
                prof.append({"ret": e.ret, "depth": e.depth, "k": k, "d": diff[e.T + k] - diff[e.T - 1]})
    return pd.DataFrame(out), pd.DataFrame(prof)


if __name__ == "__main__":
    rng = np.random.default_rng(A.SEED + 7)
    E, P, cites = A.load()
    R, prof = rows(match_t1(E, P, cites), cites)
    M = A.ret_means(R)
    out = {"pairs": {str(d): int((R.depth == d).sum()) for d in (1, 2)}}
    for d in (1, 2):
        m = M[M.depth == d]
        e_, c_, n_ = A.boot_mean(m, rng)
        out[f"depth{d}"] = {"effect": round(e_, 5), "ci": [round(x, 5) for x in c_], "retractions": n_, "pct": round(100 * (np.exp(e_) - 1), 2)}
        for cls in ("misconduct", "honest", "other"):
            e2, c2, n2 = A.boot_mean(m, rng, (m.cls == cls).to_numpy())
            out[f"depth{d}"][cls] = {"effect": round(e2, 5), "ci": [round(x, 5) for x in c2], "n": n2}
    pr = prof.groupby(["ret", "depth", "k"]).d.mean().reset_index().groupby(["depth", "k"]).d.agg(["mean", "count"]).reset_index()
    pr.to_csv(A.TAB / "event_profile_t1.csv", index=False)
    out["pre_T2_minus_T1"] = {str(d): round(float(pr[(pr.depth == d) & (pr.k == -2)]["mean"].iloc[0]), 5) for d in (1, 2)}
    (A.TAB / "posthoc.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
    print(pr.to_string())
