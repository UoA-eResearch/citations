"""H1-H3 and the secondary analyses (plan sections 2 and 4, D1-D2) -> results/tables/primary.json, annual_rules.csv.

Trend window 2014-2025 (the plan; D3 withdrew D1). H3 assessment years 2021-2025. Daily SAIDI is by calendar day of interruption start; the IEEE threshold for disclosure
year t uses the non-zero days of years t-5..t-1 (rolling) or 2009-2013 (frozen); major-event days are excluded.
National index = ICP-weighted mean of distributor SAIDI. Trend = slope of ln(index) on year, as % a year.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rules as R  # noqa: E402

RUN = R.RUN
T = R.T
B, SEED = 2000, 20261023
YEARS = list(range(2014, 2026))
MISSING = {("Top Energy", 2025)}        # D3: not separable from Transpower-caused interruptions


def daily_by_year(u, col="saidi"):
    d = R.daily(u, "2008-04-01", "2025-03-31", col)
    return d, pd.Series(R.disc_year(d.index), index=d.index)


def annual_rules(U, col="saidi"):
    rows = []
    for e, u in U.groupby("edb"):
        d, dy = daily_by_year(u, col)
        frozen = R.ieee_threshold(d[dy.between(2009, 2013)])
        for t in YEARS:
            if (e, t) in MISSING:
                continue
            thr = R.ieee_threshold(d[dy.between(t - 5, t - 1)])
            x = d[dy == t]
            rows.append({"edb": e, "disc_yr": t, "raw": x.sum(), "excl_rolling": x[x <= thr].sum(),
                         "excl_frozen": x[x <= frozen].sum(), "med_rolling": int((x > thr).sum()),
                         "med_frozen": int((x > frozen).sum()), "thr_rolling": thr, "thr_frozen": frozen})
    return pd.DataFrame(rows)


def trend(idx):
    y = np.log(idx.to_numpy())
    x = np.asarray(idx.index, float)
    b = np.polyfit(x, y, 1)[0]
    return 100 * (np.exp(b) - 1)


def pivots(a, w):
    """Distributor x year matrices of each series and of ICP weights (missing ICP counts: the distributor's median)."""
    m = a.merge(w, on=["edb", "disc_yr"], how="left")
    m["icps"] = m.icps.fillna(m.groupby("edb").icps.transform("median"))
    P = {c: m.pivot(index="edb", columns="disc_yr", values=c) for c in ("raw", "excl_rolling", "excl_frozen", "icps")}
    return P


def national(P, col, rows=None):
    V, Wt = P[col].to_numpy(float), P["icps"].to_numpy(float)
    if rows is not None:
        V, Wt = V[rows], Wt[rows]
    Wt = np.where(np.isnan(V), 0.0, Wt)          # D3: a missing distributor-year drops out of that year's weights
    return pd.Series(np.nansum(V * Wt, 0) / Wt.sum(0), index=P[col].columns)


def trends(P, rows=None, years=None):
    out = {}
    for c in ("raw", "excl_rolling", "excl_frozen"):
        sr = national(P, c, rows)
        out[c] = trend(sr) if years is None else _trend_pairs(sr, years)
    return out


def h12(a, w, label, drop_years=(), drop_edbs=()):
    a = a[~a.disc_yr.isin(drop_years) & ~a.edb.isin(drop_edbs)]
    w = w[~w.edb.isin(drop_edbs)]
    P = pivots(a, w)
    n = len(P["raw"])
    est = trends(P)
    rng = np.random.default_rng(SEED)
    bs = [trends(P, rows=rng.integers(0, n, n)) for _ in range(B)]
    yrs = list(P["raw"].columns)
    rng2 = np.random.default_rng(SEED + 1)
    by = []
    for _ in range(B):
        sy = list(rng2.choice(yrs, len(yrs)))
        if len(set(sy)) >= 3:
            by.append(trends(P, years=sy))

    def summ(rows):
        r = pd.DataFrame(rows)
        ratio = r.excl_rolling / r.raw
        diff = r.excl_frozen - r.excl_rolling
        q = lambda v: [round(float(np.nanpercentile(v, 2.5)), 4), round(float(np.nanpercentile(v, 97.5)), 4)]
        return {"raw_ci": q(r.raw), "excl_rolling_ci": q(r.excl_rolling), "excl_frozen_ci": q(r.excl_frozen),
                "ratio_ci": q(ratio), "diff_ci": q(diff)}

    res = {"label": label, "edbs": n, "years": [int(min(yrs)), int(max(yrs))],
           "trend_pct_per_yr": {k: round(v, 4) for k, v in est.items()},
           "ratio": round(est["excl_rolling"] / est["raw"], 4) if est["raw"] else None,
           "diff_pp": round(est["excl_frozen"] - est["excl_rolling"], 4),
           "cluster": summ(bs), "years_bootstrap": summ(by)}
    c = res["cluster"]
    if c["raw_ci"][0] <= 0 <= c["raw_ci"][1]:
        res["H1"] = "Inconclusive (raw trend interval includes 0)"
    elif c["ratio_ci"][1] < 0.5:
        res["H1"] = "Supported"
    elif c["ratio_ci"][0] > 0.5:
        res["H1"] = "Refuted"
    else:
        res["H1"] = "Inconclusive"
    res["H2"] = "Supported" if c["diff_ci"][0] > 0 else "Refuted" if c["diff_ci"][1] < 0 else "Inconclusive"
    return res


def _trend_pairs(s, yrs):
    y = np.log(s.loc[yrs].to_numpy())
    return 100 * (np.exp(np.polyfit(np.asarray(yrs, float), y, 1)[0]) - 1)


def h3(U, col="saidi", use_det_limits=False):
    lim = pd.read_csv(T / "dpp_limits.csv")
    det = lim[lim.dpp == "DPP3"].set_index("edb_current")
    bvc, limc = (f"{col}_bv", f"{col}_limit")
    rows = []
    for e, u in U.groupby("edb"):
        if e == "Aurora Energy" or e not in det.index:
            continue
        yrs = [2024, 2025] if e == "Powerco" else [2021, 2022, 2023, 2024, 2025]
        if e == "Top Energy":
            yrs = [y for y in yrs if y != 2025]          # D3: Top Energy 2025 not separable (Transpower-caused included)
        bv = float(det.loc[e, bvc])
        # (a) the Commission's rule with the determination's boundary value
        ref = R.commission(u, "2009-03-31 00:00", "2019-03-31 23:30", list(range(2010, 2020)), 1104, bound=bv, strict=False, col=col)
        la = float(det.loc[e, limc]) if use_det_limits else ref["limit"]
        ass = R.commission(u, "2020-03-31 00:00", "2025-03-31 23:30", [2021], 1104, bound=bv, strict=True, col=col)
        dy = R.disc_year(ass["grid"])
        aa = {y: float(ass["xn"][dy == y].sum()) for y in yrs}
        # (b) IEEE 2.5-beta daily, boundary from the non-zero days of 2010-2019, days capped at the boundary
        d, ddy = daily_by_year(u, col)
        refd = d[ddy.between(2010, 2019)]
        thr = R.ieee_threshold(refd)
        rn = refd.clip(upper=thr)
        tb = rn.sum() / 10
        sdb = rn.std(ddof=1) * np.sqrt(365.25)
        lb = tb + 2 * sdb
        ab = {y: float(d[ddy == y].clip(upper=thr).sum()) for y in yrs}
        # D3 variant: major-event days excluded rather than capped (the H1/H2 convention)
        rx = refd[refd <= thr]
        lbx = rx.sum() / 10 + 2 * refd.where(refd <= thr, 0).std(ddof=1) * np.sqrt(365.25)
        abx = {y: float(d[(ddy == y) & (d <= thr)].sum()) for y in yrs}
        ea = [y for y in yrs if aa[y] > la]
        eb = [y for y in yrs if ab[y] > lb]
        ebx = [y for y in yrs if abx[y] > lbx]
        rows.append({"edb": e, "years": yrs, "a_boundary": bv, "a_limit": round(la, 4), "a_assessed": {y: round(v, 3) for y, v in aa.items()},
                     "a_exceed": ea, "b_boundary": round(thr, 4), "b_limit": round(lb, 4),
                     "b_assessed": {y: round(v, 3) for y, v in ab.items()}, "b_exceed": eb, "differs": ea != eb,
                     "b_excl_exceed": ebx, "differs_excl": ea != ebx,
                     "ref_days_over_ieee": int((refd > thr).sum()), "ref_share_removed_ieee": round(float(1 - rn.sum() / refd.sum()), 4) if refd.sum() else 0.0,
                     "ieee_to_commission_boundary": round(thr / bv, 3) if bv else None,
                     "margin_a": {y: round(aa[y] / la, 3) for y in yrs},
                     "raw": {y: round(float(d[ddy == y].sum()), 3) for y in yrs}})
    r = pd.DataFrame(rows)
    n = int(r.differs.sum())
    v = "Supported" if n >= 2 else "Refuted" if n == 0 else "Inconclusive"
    nx = int(r.differs_excl.sum())
    return {"verdict": v, "distributors": int(len(r)), "differing": n, "differing_names": r[r.differs].edb.tolist(),
            "variant_exclude_differing": nx, "variant_exclude_names": r[r.differs_excl].edb.tolist(),
            "inert_ieee_edbs": r[r.ref_days_over_ieee == 0].edb.tolist(),
            "ieee_to_commission_boundary_range": [float(r.ieee_to_commission_boundary.min()), float(r.ieee_to_commission_boundary.max())],
            "exceedances_a": int(r.a_exceed.map(len).sum()), "exceedances_b": int(r.b_exceed.map(len).sum()),
            "rows": r.to_dict(orient="records")}


def decomposition(U):
    lim = pd.read_csv(T / "dpp_limits.csv")
    det3 = lim[lim.dpp == "DPP3"].set_index("edb_current")
    rows = []
    for e, u in U.groupby("edb"):
        if e not in det3.index:
            continue
        n4 = R.RANK["dpp4"].get(e, 1104)
        n3 = R.RANK["dpp3"].get(e, 1104)
        gg = u[(u.start.dt.normalize() >= "2014-03-31") & (u.start.dt.normalize() <= "2024-03-31")]
        w4 = R.commission(gg, "2014-03-31 00:00", "2024-03-31 23:30", list(range(2015, 2025)), n4)
        w4f = R.commission(gg, "2014-03-31 00:00", "2024-03-31 23:30", list(range(2015, 2025)), n4, bound=float(det3.loc[e, "saidi_bv"]))
        g3 = u[u.start.dt.normalize() >= "2009-03-31"]
        w3 = R.commission(g3, "2009-03-31 00:00", "2019-03-31 23:30", list(range(2010, 2020)), n3, rank_from="2009-04-01 00:00", strict=False)
        w3f = R.commission(g3, "2009-03-31 00:00", "2019-03-31 23:30", list(range(2010, 2020)), n3, rank_from="2009-04-01 00:00",
                           strict=False, bound=w4["bound"])      # D3: the other ordering (boundary first, on 2010-2019 outcomes)
        raw3 = w3["x"][np.isin(R.disc_year(w3["grid"]), range(2010, 2020))].sum() / 10
        raw4 = w4["x"][np.isin(R.disc_year(w4["grid"]), range(2015, 2025))].sum() / 10
        rows.append({"edb": e, "bv3": round(w3["bound"], 3), "bv4": round(w4["bound"], 3), "raw_mean3": round(raw3, 3),
                     "raw_mean4": round(raw4, 3), "target3": round(w3["target"], 3), "target4": round(w4["target"], 3),
                     "target4_at_bv3": round(w4f["target"], 3), "target3_at_bv4": round(w3f["target"], 3),
                     "limit3": round(w3["limit"], 3), "limit4": round(w4["limit"], 3),
                     "limit4_at_bv3": round(w4f["limit"], 3),
                     "removed_share3": round(1 - w3["target"] / raw3, 4) if raw3 else None,
                     "removed_share4": round(1 - w4["target"] / raw4, 4) if raw4 else None})
    r = pd.DataFrame(rows)
    r["d_target"] = r.target4 - r.target3
    r["d_boundary_part"] = r.target4 - r.target4_at_bv3
    r["d_outcome_part"] = r.target4_at_bv3 - r.target3
    r["d_boundary_first"] = r.target3_at_bv4 - r.target3              # D3: boundary changed first
    r["d_outcome_second"] = r.target4 - r.target3_at_bv4
    r["d_boundary_shapley"] = (r.d_boundary_part + r.d_boundary_first) / 2
    return r


def main():
    U = pd.read_parquet(R.INT / "unplanned.parquet")
    W = pd.read_csv(T / "panel_annual.csv")[["edb", "disc_yr", "icps"]]
    out = {}
    a = annual_rules(U)
    a.to_csv(T / "annual_rules.csv", index=False)
    out["H1_H2"] = h12(a, W, "primary")
    out["sensitivity"] = {"no_2023": h12(a, W, "no 2023", drop_years=(2023,)),
                          "no_aurora": h12(a, W, "no Aurora", drop_edbs=("Aurora Energy",)),
                          "window_2014_2024": h12(a, W, "window 2014-2024 (plan section 4)", drop_years=(2025,))}
    af = annual_rules(U, "saifi")
    af.to_csv(T / "annual_rules_saifi.csv", index=False)
    out["saifi_H1_H2"] = h12(af, W, "SAIFI")
    out["H3"] = h3(U)
    out["H3_determination_limits"] = h3(U, use_det_limits=True)
    out["H3_saifi"] = h3(U, "saifi")
    dec = decomposition(U)
    dec.to_csv(T / "decomposition.csv", index=False)
    out["decomposition"] = {"median_pct_change_target": round(float((dec.target4 / dec.target3 - 1).median() * 100), 2),
                            "median_pct_change_limit": round(float((dec.limit4 / dec.limit3 - 1).median() * 100), 2),
                            "median_pct_change_raw_mean": round(float((dec.raw_mean4 / dec.raw_mean3 - 1).median() * 100), 2),
                            "sum_d_target": round(float(dec.d_target.sum()), 2),
                            "sum_boundary_part": round(float(dec.d_boundary_part.sum()), 2),
                            "sum_outcome_part": round(float(dec.d_outcome_part.sum()), 2),
                            "sum_boundary_first": round(float(dec.d_boundary_first.sum()), 2),
                            "sum_outcome_second": round(float(dec.d_outcome_second.sum()), 2),
                            "sum_boundary_shapley": round(float(dec.d_boundary_shapley.sum()), 2),
                            "median_removed_share3": round(float(dec.removed_share3.median()), 4),
                            "median_removed_share4": round(float(dec.removed_share4.median()), 4)}
    P = pivots(a, W)
    nat = {c: national(P, c).round(3).to_dict() for c in ("raw", "excl_rolling", "excl_frozen")}
    out["national_index"] = nat
    out["med_days_per_year"] = {k: a.groupby("disc_yr")[k].mean().round(3).to_dict() for k in ("med_rolling", "med_frozen")}
    (T / "primary.json").write_text(json.dumps(out, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o)))
    p = out["H1_H2"]
    print("H1/H2:", p["trend_pct_per_yr"], "ratio", p["ratio"], "diff", p["diff_pp"], p["H1"], "|", p["H2"])
    print(" cluster", p["cluster"]); print(" years", p["years_bootstrap"])
    for k, v in out["sensitivity"].items():
        print(k, v["trend_pct_per_yr"], v["ratio"], v["H1"], v["H2"])
    s = out["saifi_H1_H2"]; print("SAIFI", s["trend_pct_per_yr"], s["ratio"], s["H1"], s["H2"])
    for k in ("H3", "H3_determination_limits", "H3_saifi"):
        h = out[k]; print(k, h["verdict"], "differing", h["differing"], "of", h["distributors"], "exc a/b", h["exceedances_a"], h["exceedances_b"])
    print(json.dumps(out["decomposition"], indent=1))
    print(dec[["edb", "bv3", "bv4", "raw_mean3", "raw_mean4", "target3", "target4", "target4_at_bv3", "limit3", "limit4"]].to_string())
    print(json.dumps(nat["raw"])); print(json.dumps(out["med_days_per_year"]))


if __name__ == "__main__":
    main()
