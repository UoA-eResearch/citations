"""Matching, pair DiD, H1-H3 and secondaries (plan sections 0, 2, 3) -> results/tables/primary.json, event_profile.csv."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
INT, TAB = RUN / "data" / "interim", RUN / "results" / "tables"
TAB.mkdir(parents=True, exist_ok=True)
B, SEED, CAL, EQ = 2000, 20261025, 0.25, 0.01
DOMAIN = {1: "life sciences", 2: "social sciences", 3: "physical sciences", 4: "health sciences"}


def load():
    D1 = pd.read_parquet(INT / "d1.parquet").assign(depth=1)
    D2 = pd.read_parquet(INT / "d2.parquet").assign(depth=2)
    E = pd.concat([D1[["wid", "year", "ret", "T", "cls", "depth"]], D2[["wid", "year", "ret", "T", "cls", "depth"]]])
    meta = pd.read_parquet(INT / "exposed_meta.parquet")[["wid", "dom"]].drop_duplicates("wid")
    E = E.merge(meta, on="wid", how="left")
    P = pd.read_parquet(INT / "candidates.parquet")
    C = pd.read_parquet(INT / "cites.parquet")
    cites = {}
    for w, g in C.groupby("wid"):
        cites[w] = dict(zip(g.cyear.astype(int), g.n.astype(int)))
    return E, P, cites


def pre_metrics(c, T):
    cum = sum(n for y, n in c.items() if y <= T - 2)
    return np.log1p(cum), np.log1p(c.get(T - 2, 0))


def match(E, P, cites, exact=False):
    cand = P.groupby("exposed").cand.apply(list)
    pairs = []
    for e in E.itertuples():
        if e.wid not in cand.index:
            continue
        ce = cites.get(e.wid, {})
        a0, b0 = pre_metrics(ce, e.T)
        best, bd = None, np.inf
        for c in cand.loc[e.wid]:
            a, b = pre_metrics(cites.get(c, {}), e.T)
            if exact:
                ok = a == a0 and b == b0
            else:
                ok = abs(a - a0) <= CAL and abs(b - b0) <= CAL
            if ok:
                d = (a - a0) ** 2 + (b - b0) ** 2
                if d < bd:
                    best, bd = c, d
        if best is not None:
            pairs.append((e, best))
    return pairs


def pair_rows(pairs, cites):
    rows, prof = [], []
    for e, c in pairs:
        ce, cc = cites.get(e.wid, {}), cites.get(c, {})
        diff = {t: np.log1p(ce.get(t, 0)) - np.log1p(cc.get(t, 0)) for t in range(e.T - 4, e.T + 5)}
        pre = [t for t in range(max(e.T - 4, e.year + 1), e.T - 1)]
        post = list(range(e.T + 1, e.T + 5))
        if not pre:
            continue
        did = np.mean([diff[t] for t in post]) - np.mean([diff[t] for t in pre])
        rows.append({"wid": e.wid, "ret": e.ret, "T": e.T, "cls": e.cls, "depth": e.depth, "dom": e.dom, "did": did})
        ref = diff[e.T - 1]
        for k in range(-4, 5):
            t = e.T + k
            if t >= e.year + 1:
                prof.append({"ret": e.ret, "depth": e.depth, "cls": e.cls, "k": k, "d": diff[t] - ref})
    return pd.DataFrame(rows), pd.DataFrame(prof)


def ret_means(R):
    return R.groupby(["ret", "depth", "cls"]).did.mean().reset_index()


def boot_mean(M, rng, mask=None):
    v = M.did.to_numpy() if mask is None else M.did.to_numpy()[mask]
    est = float(v.mean())
    bs = np.array([v[rng.integers(0, len(v), len(v))].mean() for _ in range(B)])
    return est, [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))], len(v)


def verdict_penalty(ci):
    return "Supported" if ci[1] < 0 else "Refuted" if (ci[0] > -EQ and ci[1] < EQ) else "Inconclusive"


def main():
    rng = np.random.default_rng(SEED)
    E, P, cites = load()
    pairs = match(E, P, cites)
    R, prof = pair_rows(pairs, cites)
    R.to_parquet(INT / "pairs.parquet", index=False)
    M = ret_means(R)
    out = {"exposed": {str(d): int((E.depth == d).sum()) for d in (1, 2)},
           "matched_pairs": {str(d): int((R.depth == d).sum()) for d in (1, 2)},
           "retractions": {str(d): int(M[M.depth == d].ret.nunique()) for d in (1, 2)}}
    m1 = M[M.depth == 1]
    est, ci, n = boot_mean(m1, rng)
    out["H1"] = {"did": round(est, 5), "ci": [round(x, 5) for x in ci], "retractions": n, "pct": round(100 * (np.exp(est) - 1), 2),
                 "verdict": verdict_penalty(ci)}
    mm, mh = m1[m1.cls == "misconduct"].did.to_numpy(), m1[m1.cls == "honest"].did.to_numpy()
    Cs = []
    for _ in range(B):
        a = mm[rng.integers(0, len(mm), len(mm))].mean()
        b = mh[rng.integers(0, len(mh), len(mh))].mean()
        Cs.append(-a - 2 * (-b))
    C = -mm.mean() - 2 * (-mh.mean())
    lo, hi = np.percentile(Cs, [2.5, 97.5])
    out["H2"] = {"penalty_misconduct": round(float(-mm.mean()), 5), "penalty_honest": round(float(-mh.mean()), 5),
                 "n_misconduct": int(len(mm)), "n_honest": int(len(mh)), "C": round(float(C), 5), "C_ci": [round(float(lo), 5), round(float(hi), 5)],
                 "verdict": "Supported" if lo > 0 else "Refuted" if hi < 0 else "Inconclusive"}
    for cls in ("misconduct", "honest", "other"):
        e2, c2, n2 = boot_mean(m1, rng, (m1.cls == cls).to_numpy())
        out["H2"][f"did_{cls}"] = {"did": round(e2, 5), "ci": [round(x, 5) for x in c2], "n": n2}
    m2 = M[M.depth == 2]
    est2, ci2, n2 = boot_mean(m2, rng)
    out["H3"] = {"did": round(est2, 5), "ci": [round(x, 5) for x in ci2], "retractions": n2,
                 "verdict": "Supported" if (ci2[0] > -EQ and ci2[1] < EQ) else "Refuted" if (ci2[1] < 0 or ci2[0] > 0) else "Inconclusive"}
    # event profile (retraction-weighted)
    pr = prof.groupby(["ret", "depth", "k"]).d.mean().reset_index().groupby(["depth", "k"]).d.agg(["mean", "count"]).reset_index()
    pr.to_csv(TAB / "event_profile.csv", index=False)
    pre = prof[prof.k <= -2].groupby(["ret", "depth"]).d.mean().reset_index()
    out["pretrend"] = {str(d): round(float(pre[pre.depth == d].d.mean()), 5) for d in (1, 2)}
    # secondaries: by domain and era (depth 1)
    out["by_domain"] = {}
    for dom, name in DOMAIN.items():
        r = R[(R.depth == 1) & (R.dom == dom)]
        if r.ret.nunique() >= 30:
            mm_ = ret_means(r)
            e_, c_, n_ = boot_mean(mm_, rng)
            out["by_domain"][name] = {"did": round(e_, 5), "ci": [round(x, 5) for x in c_], "retractions": n_}
    for era, (a, b) in {"2000-2010": (2000, 2010), "2011-2021": (2011, 2021)}.items():
        mm_ = m1[m1.ret.isin(R[(R.T >= a) & (R.T <= b)].ret)]
        e_, c_, n_ = boot_mean(mm_, rng)
        out.setdefault("by_era", {})[era] = {"did": round(e_, 5), "ci": [round(x, 5) for x in c_], "retractions": n_}
    # sensitivity: exact matching on pre-period counts
    Rx, _ = pair_rows(match(E[E.depth == 1], P, cites, exact=True), cites)
    if len(Rx):
        ex_, cx_, nx_ = boot_mean(ret_means(Rx), rng)
        out["sensitivity_exact_match"] = {"did": round(ex_, 5), "ci": [round(x, 5) for x in cx_], "retractions": nx_, "pairs": int(len(Rx))}
    (TAB / "primary.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
