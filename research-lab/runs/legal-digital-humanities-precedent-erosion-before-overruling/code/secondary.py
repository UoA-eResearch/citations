"""Secondaries 1 and 6 (plan section 5) -> results/tables/{event_path.csv, secondary.json}. Reported, not confirmatory.

1. Event path with pointwise 95% intervals (the same stack bootstrap as event.py, B = 1,000, storing every D(e)),
   for the primary sample and for the co-citation exclusion; and the share series (treated and control citations as
   a share of all lower-court citations to Supreme Court clusters that year, by event year).
6. Out of sample: Chevron (467 U.S. 837; overruled 2024, in the primary sample) and Humphrey's Executor (295 U.S. 602;
   overruled 2026 by Trump v. Slaughter, not on the parsed list), each against its own matched controls, pre-period
   event years only (data end 2025).
"""
import json
import multiprocessing as mp
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import event as E  # noqa: E402

T = E.T
B, SEED = 1000, 20261023


def _boot_path(args):
    d, ids, seed = args
    rng = np.random.default_rng(seed)
    parts = []
    for k, s in enumerate(rng.choice(ids, len(ids))):
        x = d[d["stack"] == s].copy()
        x["stack"] = k
        x["cs"] = str(k) + "_" + x.case.astype(str)
        x["ys"] = str(k) + "_" + x.year.astype(str)
        parts.append(x)
    try:
        beta = E.fit(pd.concat(parts))
        return {e: 1 - np.exp(b) for e, b in beta.items()}
    except Exception:
        return None


def path_with_ci(variant):
    cites, cl, wide, listed, treated, _ = E.build(variant)
    stacks, _ = E.match(cl, wide, listed, treated)
    d = E.long_panel(stacks, wide, cites, excl_overruling=(variant == "excl_cocite"))
    if variant == "pre2019":                                         # D1 (post hoc)
        d = d[d.year <= 2018]
    D, _, _ = E.stats(E.fit(d))
    ids = sorted(d["stack"].unique())
    with mp.get_context("spawn").Pool(8) as pool:
        bs = [r for r in pool.imap_unordered(_boot_path, [(d, ids, SEED + i) for i in range(B)], chunksize=4) if r]
    bs = pd.DataFrame(bs)
    rows = [{"variant": variant, "event": int(e), "D": round(float(v), 4),
             "lo": round(float(np.nanpercentile(bs[e], 2.5)), 4), "hi": round(float(np.nanpercentile(bs[e], 97.5)), 4)}
            for e, v in sorted(D.items())]
    return rows, d, wide


def share_series(d):
    tot = pd.read_csv(T / "scotus_cites_by_year.csv", index_col=0)["all"]
    d = d.assign(share=d.y / d.year.map(tot))
    g = d.groupby(["ev", "treated"]).share.mean().unstack()
    return {int(e): {"treated": float(r[1]), "controls": float(r[0])} for e, r in g.iterrows()}


def one_case(cluster, T0, dyear, cite, cites, cl, wide, listed):
    t = {"cluster": cluster, "T0": T0, "dyear": dyear, "section": "", "cite": cite, "overruling_clusters": []}
    stacks, bal = E.match(cl, wide, listed, [t])
    if not stacks:
        return {"cite": cite, "error": "no controls"}
    d = E.long_panel(stacks, wide)
    d = d[d.year <= E.LASTYEAR]
    import pyfixest as pf
    q = d.copy()
    cols = []
    for e in range(-10, min(11, E.LASTYEAR - T0 + 1)):
        c = f"e_{e + 20}"
        q[c] = ((q.treated == 1) & (q.ev == e)).astype(float)
        if q[c].sum() > 0 or True:
            cols.append((c, e))
    q = q[q.groupby("cs").y.transform("sum") > 0]
    m = pf.fepois("y ~ " + " + ".join(c for c, _ in cols) + " | cs + ys", data=q, vcov="hetero")
    b, se = m.coef(), m.se()
    path = {int(e): {"D": round(float(1 - np.exp(b[c])), 4), "D_lo": round(float(1 - np.exp(b[c] + 1.96 * se[c])), 4),
                     "D_hi": round(float(1 - np.exp(b[c] - 1.96 * se[c])), 4)} for c, e in cols if c in b.index}
    pre_n = int(wide.loc[cluster, [y for y in wide.columns if y < T0]].sum())
    return {"cite": cite, "T0": T0, "pre_overruling_citations": pre_n, "balance": bal, "path": path}


def main():
    out = {}
    rows, d, wide = path_with_ci("primary")
    out["share_series_primary"] = share_series(d)
    rows2, _, _ = path_with_ci("excl_cocite")
    pd.DataFrame(rows + rows2).to_csv(T / "event_path.csv", index=False)
    cites, cl, wide, listed, _, _ = E.build("primary")
    import overruled as O
    m = O.us_cite_map()
    hx = sorted(m.get("295 U.S. 602", []))
    hx = [c for c in hx if c in wide.index]
    hx = max(hx, key=lambda c: wide.loc[c].sum()) if hx else None
    out["chevron"] = one_case(111221, 2024, 1984, "467 U.S. 837", cites, cl, wide, listed)
    out["humphreys_executor"] = one_case(hx, 2026, 1935, "295 U.S. 602", cites, cl, wide, listed) if hx else {"error": "not linked"}
    (T / "secondary.json").write_text(json.dumps(out, indent=1, default=str))
    print(pd.DataFrame(rows + rows2).to_string())
    print(json.dumps({k: out[k] for k in ("chevron", "humphreys_executor")}, indent=1, default=str)[:4000])


if __name__ == "__main__":
    if sys.argv[1:] == ["pre2019"]:                                  # D1 (post hoc): add the pre-2019 path
        rows, _, _ = path_with_ci("pre2019")
        ep = pd.read_csv(T / "event_path.csv")
        pd.concat([ep[ep.variant != "pre2019"], pd.DataFrame(rows)]).to_csv(T / "event_path.csv", index=False)
        print(pd.DataFrame(rows).to_string())
    else:
        main()
