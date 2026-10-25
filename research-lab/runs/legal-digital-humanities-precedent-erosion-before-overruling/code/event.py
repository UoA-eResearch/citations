"""Matching, stacked PPML event study, pre-share and bootstrap (plan sections 2-5).

  event.py            primary + secondaries -> results/tables/{matching_balance.json, primary.json, event_path.csv}

D2 (after review): controls must have an SCDB id and the treated case's SCDB issue area, as plan.md says (the first
version admitted orders-list clusters and CAP duplicates without one); per-stack balance is reported; post hoc
variants (labelled in posthoc_d2.py): "noFD" drops district-court citers, "era*" and "recent" restrict overruling
years, "appellate" keeps federal courts of appeals only.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
INT = RUN / "data" / "interim"
RAW = RUN / "data" / "raw"
T = RUN / "results" / "tables"
B, SEED, LASTYEAR = 1000, 20261023, 2025
PRE, EV = range(-20, -10), range(-10, 11)
ERAS = {"era1960_89": (1960, 1989), "era1990_2013": (1990, 2013), "recent": (2014, 2024)}


def counts_panel(cites, clusters):
    """Yearly lower-court citations for the given cited clusters, dict cluster -> Series(year -> n)."""
    c = cites[cites.cited_cluster.isin(clusters)]
    return c.groupby(["cited_cluster", "year"]).size()


def build(variant="primary"):
    cites = pd.read_parquet(INT / "cites_scotus.parquet")
    if variant == "federal":
        cites = cites[cites.juris.str.startswith("F")]
    elif variant == "state":
        cites = cites[cites.juris.isin(["S", "SA", "ST", "SS"])]
    elif variant == "appellate":                                    # D2 post hoc: federal courts of appeals only
        cites = cites[cites.juris == "F"]
    if "noFD" in variant:                                           # D2 post hoc: drop district-court citers
        cites = cites[cites.juris != "FD"]
    cl = pd.read_parquet(INT / "clusters.parquet", columns=["id", "date_filed", "scdb_id"])
    cl["id"] = pd.to_numeric(cl.id, errors="coerce")
    cl = cl.dropna(subset=["id"]).astype({"id": "int64"})
    sc_ids = set(cites.cited_cluster.unique())
    cl = cl[cl.id.isin(sc_ids)].copy()
    cl["dyear"] = pd.to_numeric(cl.date_filed.str[:4], errors="coerce")
    scdb = pd.read_csv(next((RAW / "scdb").glob("*.csv")), encoding="latin-1", usecols=["caseId", "issueArea"])
    cl = cl.merge(scdb.rename(columns={"caseId": "scdb_id"}), on="scdb_id", how="left")
    cnt = cites.groupby(["cited_cluster", "year"]).size().rename("n").reset_index()
    wide = cnt.pivot(index="cited_cluster", columns="year", values="n").fillna(0)
    years = [y for y in range(1900, LASTYEAR + 1)]
    wide = wide.reindex(columns=years, fill_value=0)
    pairs = pd.read_csv(T / "overruled_pairs.csv")
    listed = set(int(x) for s in pairs.overruled_clusters.dropna().astype(str) for x in s.split(";") if x)
    p = pairs[pairs.overruling_year.between(1960, 2024)].sort_values("overruling_year")
    p = p.drop_duplicates("overruled_cite", keep="first")              # first listed overruling
    if variant == "constitutional":
        p = p[p.section == "Constitutional"]
    elif variant == "statutory":
        p = p[p.section == "Statutory"]
    elif variant == "post1990":
        p = p[p.overruling_year > 1990]
    if variant.startswith("pre2019"):                              # D1 (post hoc): windows before the coverage break
        p = p[p.overruling_year <= 2013]
    for k, (lo, hi) in ERAS.items():                                # D2 post hoc: overruling-year eras
        if k in variant:
            p = p[p.overruling_year.between(lo, hi)]
    treated, excluded = [], {"too_young": 0, "under_50": 0, "not_in_citation_data": 0}
    for r in p.itertuples():
        cands = [int(x) for x in str(r.overruled_clusters).split(";") if x and x != "nan" and int(x) in wide.index]
        if not cands:
            excluded["not_in_citation_data"] += 1
            continue
        T0 = int(r.overruling_year)
        pre_n = {c: wide.loc[c, [y for y in years if y < T0]].sum() for c in cands}
        c = max(pre_n, key=pre_n.get)
        if int(r.overruled_year) > T0 - 20:
            excluded["too_young"] += 1
            continue
        if pre_n[c] < 50:
            excluded["under_50"] += 1
            continue
        ov = [int(x) for x in str(r.overruling_clusters).split(";") if x and x != "nan"]
        treated.append({"cluster": c, "T0": T0, "dyear": int(r.overruled_year), "section": r.section,
                        "cite": r.overruled_cite, "overruling_clusters": ov,
                        "ia": getattr(r, "overruled_scdb_issueArea", np.nan)})
    return cites, cl, wide, listed, treated, excluded


def match(cl, wide, listed, treated):
    cl = cl.set_index("id")
    stacks, bal = [], []
    for s, t in enumerate(treated):
        T0, dy = t["T0"], t["dyear"]
        pool = cl[(cl.dyear.between(dy - 2, dy + 2)) & ~cl.index.isin(listed) & (cl.scdb_id.fillna("") != "")].index
        ia = t.get("ia", np.nan)
        if pd.isna(ia):
            ia = cl.issueArea.get(t["cluster"], np.nan)
        if pd.notna(ia):                                              # D2: same SCDB issue area, as planned
            pool = [c for c in pool if cl.issueArea.get(c) == ia]
        pool = [c for c in pool if c in wide.index]
        prey = [T0 + e for e in PRE]
        pre_tot = [y for y in wide.columns if y < T0]
        pool = [c for c in pool if wide.loc[c, pre_tot].sum() >= 50]
        if not pool:
            continue
        X = np.log1p(wide.loc[pool, prey].to_numpy(float))
        x0 = np.log1p(wide.loc[t["cluster"], prey].to_numpy(float))
        S = np.cov(np.vstack([X, x0]).T) + 1e-6 * np.eye(len(prey))
        Si = np.linalg.pinv(S)
        dd = np.einsum("ij,jk,ik->i", X - x0, Si, X - x0)
        ctrl = [pool[i] for i in np.argsort(dd)[:10]]
        stacks.append({"stack": s, "treated": t, "controls": ctrl})
        bal.append({"stack": s, "treated_mean": float(x0.mean()), "control_mean": float(X[np.argsort(dd)[:10]].mean()),
                    "pool_sd": float(X.std())})
    b = pd.DataFrame(bal)
    per = (b.treated_mean - b.control_mean) / b.pool_sd.replace(0, np.nan)
    return stacks, {"stacks": len(stacks), "controls_per_stack_mean": float(np.mean([len(s["controls"]) for s in stacks])),
                    "mean_smd_log_pre": round(float(per.mean()), 4), "median_smd": round(float(per.median()), 4),
                    "stacks_abs_smd_gt_0_5": int((per.abs() > 0.5).sum()), "stacks_abs_smd_gt_1": int((per.abs() > 1).sum()),
                    "per_stack_smd": [round(float(x), 3) for x in per]}


def long_panel(stacks, wide, cites=None, excl_overruling=False):
    rows = []
    for st in stacks:
        t = st["treated"]
        T0 = t["T0"]
        yrs = [T0 + e for e in range(-20, 11) if T0 + e <= LASTYEAR]
        tw = wide.loc[t["cluster"], yrs].copy()
        if excl_overruling and cites is not None:
            co = set(cites[cites.cited_cluster.isin(t["overruling_clusters"])].citing_cluster)
            sub = cites[(cites.cited_cluster == t["cluster"]) & cites.citing_cluster.isin(co)].groupby("year").size()
            tw = tw - sub.reindex(yrs, fill_value=0).to_numpy()
        for c, ycol, tr in [(t["cluster"], tw, 1)] + [(c, wide.loc[c, yrs], 0) for c in st["controls"]]:
            for y, n in zip(yrs, np.asarray(ycol, float)):
                rows.append((st["stack"], c, y, y - T0, tr, n))
    d = pd.DataFrame(rows, columns=["stack", "case", "year", "ev", "treated", "y"])
    d["cs"] = d["stack"].astype(str) + "_" + d.case.astype(str)
    d["ys"] = d["stack"].astype(str) + "_" + d.year.astype(str)
    return d


def fit(d):
    import pyfixest as pf
    q = d.copy()
    cols = []
    for e in EV:
        c = f"e_{e + 20}"
        q[c] = ((q.treated == 1) & (q.ev == e)).astype(float)
        if q[c].sum() > 0:
            cols.append((c, e))
    q = q[q.groupby("cs").y.transform("sum") > 0]
    m = pf.fepois("y ~ " + " + ".join(c for c, _ in cols) + " | cs + ys", data=q, vcov={"CRV1": "stack"})
    b = m.coef()
    return {e: float(b[c]) for c, e in cols if c in b.index}


def stats(beta):
    D = {e: 1 - np.exp(b) for e, b in beta.items()}
    pre = D.get(-1, np.nan) / D.get(5, np.nan) if D.get(5) else np.nan
    pooled = (np.mean([D[e] for e in (-3, -2, -1) if e in D]) / np.mean([D[e] for e in (3, 4, 5) if e in D])
              if all(e in D for e in (3, 4, 5)) else np.nan)
    return D, pre, pooled


def _boot(args):
    d, stacks_ids, seed = args
    rng = np.random.default_rng(seed)
    pick = rng.choice(stacks_ids, len(stacks_ids))
    parts = []
    for k, s in enumerate(pick):
        x = d[d["stack"] == s].copy()
        x["stack"] = k
        x["cs"] = str(k) + "_" + x.case.astype(str)
        x["ys"] = str(k) + "_" + x.year.astype(str)
        parts.append(x)
    try:
        beta = fit(pd.concat(parts))
        D, pre, pooled = stats(beta)
        return {"pre": pre, "pooled": pooled, "D5": D.get(5, np.nan), "Dm1": D.get(-1, np.nan)}
    except Exception:
        return None


def run(variant="primary", boot=True):
    cites, cl, wide, listed, treated, excluded = build(variant)
    stacks, bal = match(cl, wide, listed, treated)
    d = long_panel(stacks, wide, cites, excl_overruling=(variant == "excl_cocite"))
    if variant.startswith("pre2019"):
        d = d[d.year <= 2018]
    beta = fit(d)
    D, pre, pooled = stats(beta)
    out = {"variant": variant, "treated": len(treated), "excluded": excluded, "balance": bal,
           "D": {int(e): round(v, 4) for e, v in D.items()}, "pre_share": round(float(pre), 4), "pooled_ratio": round(float(pooled), 4)}
    if boot:
        ids = sorted(d["stack"].unique())
        # spawn, not fork: forked workers deadlock once pyfixest's thread pools exist in the parent
        import multiprocessing as mp
        bs = []
        with mp.get_context("spawn").Pool(8) as pool:
            for i, r in enumerate(pool.imap_unordered(_boot, [(d, ids, SEED + i) for i in range(B)], chunksize=4)):
                if r:
                    bs.append(r)
                if (i + 1) % 100 == 0:
                    print(variant, "bootstrap", i + 1, flush=True)
        bs = pd.DataFrame(bs)
        q = lambda v: [round(float(np.nanpercentile(v, 2.5)), 4), round(float(np.nanpercentile(v, 97.5)), 4)]
        out.update({"boot_ok": int(len(bs)), "pre_share_ci": q(bs.pre), "pooled_ratio_ci": q(bs.pooled),
                    "D5_ci": q(bs.D5), "Dm1_ci": q(bs.Dm1)})
        if out["D5_ci"][0] <= 0 <= out["D5_ci"][1]:
            out["H1"] = "not testable (no detectable post-overruling decline)"
        elif out["pre_share"] >= 0.33 and out["pre_share_ci"][0] > 0:
            out["H1"] = "Supported"
        elif out["pre_share_ci"][1] < 0.33:
            out["H1"] = "Refuted"
        else:
            out["H1"] = "Inconclusive"
    return out, d, stacks


def main():
    if sys.argv[1:] == ["pre2019"]:                               # D1 (post hoc)
        o, d, _ = run("pre2019")
        (T / "posthoc_pre2019.json").write_text(json.dumps(o, indent=1, default=str))
        print(json.dumps(o, indent=1, default=str))
        return
    res = {}
    prim, d, stacks = run("primary")
    res["primary"] = prim
    pd.DataFrame([{"event": e, "D": v} for e, v in prim["D"].items()]).to_csv(T / "event_path.csv", index=False)
    (T / "matching_balance.json").write_text(json.dumps(prim["balance"], indent=1))
    json.dump({"stacks": [{"stack": s["stack"], "treated_cluster": s["treated"]["cluster"], "cite": s["treated"]["cite"],
                           "T0": s["treated"]["T0"], "controls": s["controls"]} for s in stacks]},
              open(T / "stacks.json", "w"), indent=1)
    for v in ("excl_cocite", "federal", "state", "constitutional", "statutory", "post1990"):
        o, _, _ = run(v, boot=(v in ("excl_cocite",)))
        res[v] = o
        print(v, o.get("pre_share"), o.get("pre_share_ci"), o["D"].get(5), flush=True)
    (T / "primary.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps(prim, indent=1, default=str))


if __name__ == "__main__":
    main()
