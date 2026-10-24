"""Major-event rules and the validation gate (plan sections 2-3).

  rules.py validate   reproduce the Commission's DPP4 uncapped parameters (R model, DPP4 file) and DPP3 boundary
                      values (Stata model, DPP3 file) -> results/tables/validation.json

commission(): the DPP3/DPP4 rule. Interruptions are rounded down to the half-hour; the rolling 24-hour total at
half-hour t is the sum over t-47..t; the boundary value is the rolling total of rank n (2.3 major events a year x 48
x 10 years = 1104; small-distributor adjustments as the Commission's code); a half-hour lies in a major event if any
24-hour window containing it exceeds the boundary, and its SAIDI is then capped at boundary / 48. Target = mean
annual normalised SAIDI; SD = SD of daily normalised SAIDI x sqrt(365.25); limit = target + 2 SD.
ieee(): IEEE 1366 2.5-beta on calendar-day SAIDI: threshold exp(mean + 2.5 SD) of ln(daily SAIDI) on non-zero days.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
INT = RUN / "data" / "interim"
T = RUN / "results" / "tables"
COM = RUN / "data" / "raw" / "comcom"
RANK = {"dpp3": {"Electricity Invercargill": 726, "Nelson Electricity": 329},
        "dpp4": {"Electricity Invercargill": 734, "Nelson Electricity": 328}}


def disc_year(t):
    t = pd.DatetimeIndex(t)
    return np.where(t.month >= 4, t.year + 1, t.year)


def halfhours(u, t0, t1, col="saidi"):
    """Half-hour totals of `col` on the grid t0..t1 (inclusive), interruptions by start time rounded down."""
    grid = pd.date_range(t0, t1, freq="30min")
    s = u[(u.start >= grid[0]) & (u.start < grid[-1] + pd.Timedelta("30min"))]
    x = s.groupby(s.start.dt.floor("30min"))[col].sum().reindex(grid, fill_value=0.0)
    return grid, x.to_numpy(float)


def rolling24(x):
    c = np.cumsum(x)
    r = np.full(len(x), np.nan)
    r[48:] = c[48:] - c[:-48]
    return r


def boundary_at_rank(roll, n, valid):
    v = roll[valid & ~np.isnan(roll)]
    return float(np.sort(v)[::-1][int(round(n)) - 1])


def in_major_event(roll, bound, strict=True):
    """True where any 24-h window containing the half-hour exceeds the boundary (windows ending at t..t+47)."""
    over = (roll > bound) if strict else (roll >= bound)
    over = np.nan_to_num(over.astype(float))
    c = np.concatenate([[0.0], np.cumsum(over)])
    n = len(over)
    hi = np.minimum(np.arange(n) + 48, n)
    return (c[hi] - c[np.arange(n)]) > 0


def normalise(x, roll, bound, strict=True):
    me = in_major_event(roll, bound, strict)
    return np.where(me & (x > bound / 48), bound / 48, x), me


def params(grid, xn, years):
    dy = disc_year(grid)
    k = np.isin(dy, years)
    target = xn[k].sum() / len(years)
    daily = pd.Series(xn[k], index=grid[k]).groupby(grid[k].normalize()).sum()
    sd = daily.std(ddof=1) * np.sqrt(365.25)
    return target, sd, target + 2 * sd


def commission(u, t0, t1, years, n, rank_from=None, strict=True, bound=None, col="saidi"):
    grid, x = halfhours(u, t0, t1, col)
    roll = rolling24(x)
    valid = np.ones(len(x), bool) if rank_from is None else (grid >= pd.Timestamp(rank_from))
    if bound is None:
        bound = boundary_at_rank(roll, n, valid)
    xn, me = normalise(x, roll, bound, strict)
    target, sd, limit = params(grid, xn, years)
    return {"bound": bound, "target": target, "sd": sd, "limit": limit, "grid": grid, "x": x, "xn": xn, "me": me}


def daily(u, d0, d1, col="saidi"):
    days = pd.date_range(d0, d1, freq="D")
    s = u[(u.start >= days[0]) & (u.start < days[-1] + pd.Timedelta("1D"))]
    return s.groupby(s.start.dt.normalize())[col].sum().reindex(days, fill_value=0.0)


def ieee_threshold(dser):
    v = dser[dser > 0].to_numpy()
    lv = np.log(v)
    return float(np.exp(lv.mean() + 2.5 * lv.std(ddof=1)))


def validate():
    out = {}
    d4 = pd.read_parquet(INT / "dpp4.parquet")
    d4 = d4[d4.pu == "unplanned"]
    unc = pd.read_csv(next((COM / "dpp4_zip" / "edb_quality_dpp4" / "outputs").glob("unplanned_norm_param_not_caps*.csv"))).set_index("edb")
    rows = []
    for e, g in d4.groupby("edb"):
        n = RANK["dpp4"].get(e, 2.3 * 48 * 10)
        r = {}
        for col in ("saidi", "saifi"):
            # R model: grid 2014-03-31 00:00 .. 2024-03-31 23:30, interruptions with dates in range; last 10 disclosure years
            gg = g[(g.start.dt.normalize() >= "2014-03-31") & (g.start.dt.normalize() <= "2024-03-31")]
            c = commission(gg, "2014-03-31 00:00", "2024-03-31 23:30", list(range(2015, 2025)), n, strict=True, col=col)
            r.update({f"{col}_bound": c["bound"], f"{col}_target": c["target"], f"{col}_cap": c["limit"]})
        ref = unc.loc[e]
        rel = {k: abs(v / ref[k] - 1) if ref[k] else abs(v) for k, v in r.items()}
        rows.append({"edb": e, **{k: round(v, 5) for k, v in r.items()}, **{f"ref_{k}": round(float(ref[k]), 5) for k in r},
                     "max_rel_diff": round(max(rel.values()), 6)})
    v4 = pd.DataFrame(rows)
    out["dpp4"] = {"edbs": int(len(v4)), "all_within_1pct": bool((v4.max_rel_diff <= 0.01).all()),
                   "max_rel_diff": float(v4.max_rel_diff.max()), "rows": v4.to_dict(orient="records")}
    # DPP3: Stata model on the DPP3 file; boundary values against the determination
    d3 = pd.read_parquet(INT / "dpp3.parquet")
    d3 = d3[d3.pu == "unplanned"]
    lim = pd.read_csv(T / "dpp_limits.csv")
    det = lim[lim.dpp == "DPP3"].set_index("edb_current")
    rows = []
    raw3 = pd.read_excel(COM / "dpp3_zip" / "Final model - Publication version" / "Inputs" / "DPP3 Final - EDB interruptions.xlsx",
                         usecols=["EDB"]).EDB.replace({"Eastland Network": "Firstlight Network"})
    for e, g in d3.groupby("edb"):
        n = RANK["dpp3"].get(e, 1104)
        gg = g[g.start.dt.normalize() >= "2009-03-31"]
        c = commission(gg, "2009-03-31 00:00", "2019-03-31 23:30", list(range(2010, 2020)), n,
                       rank_from="2009-04-01 00:00", strict=False)
        cf = commission(gg, "2009-03-31 00:00", "2019-03-31 23:30", list(range(2010, 2020)), n,
                        rank_from="2009-04-01 00:00", strict=False, col="saifi")
        dd = det.loc[e]
        rows.append({"edb": e, "saidi_bound": round(c["bound"], 4), "det_saidi_bv": float(dd.saidi_bv),
                     "saifi_bound": round(cf["bound"], 5), "det_saifi_bv": float(dd.saifi_bv),
                     "saidi_limit": round(c["limit"], 3), "det_saidi_limit": float(dd.saidi_limit),
                     "saifi_limit": round(cf["limit"], 4), "det_saifi_limit": float(dd.saifi_limit),
                     "bv_rel_diff": round(abs(c["bound"] / dd.saidi_bv - 1), 5),
                     "saifi_bv_rel_diff": round(abs(cf["bound"] / dd.saifi_bv - 1), 5),
                     "limit_rel_diff": round(abs(c["limit"] / dd.saidi_limit - 1), 5)})
    v3 = pd.DataFrame(rows)
    # D3: the uncapped limits against the Stata model's own output (the determination applies a +/-5% target cap, Table J1)
    st = pd.read_stata(COM / "dpp3_zip" / "Final model - Publication version" / "Outputs" / "Unplanned parameters.dta")
    st["edb"] = st.edb.replace({"Eastland Network": "Firstlight Network"})
    st = st.set_index("edb")
    v3["stata_saidi_limit"] = [round(float(st.loc[e, "saidi_cap"]), 3) if e in st.index else None for e in v3.edb]
    v3["limit_vs_stata_rel"] = [round(abs(l / sl - 1), 5) if sl else None for l, sl in zip(v3.saidi_limit, v3.stata_saidi_limit)]
    out["dpp3_vs_stata"] = {"edbs": int(v3.stata_saidi_limit.notna().sum()), "max_rel_diff": float(v3.limit_vs_stata_rel.max()),
                            "all_within_0_1pct": bool((v3.limit_vs_stata_rel.dropna() <= 0.001).all())}
    out["dpp3"] = {"edbs": int(len(v3)), "bv_all_within_1pct": bool((v3.bv_rel_diff <= 0.01).all()),
                   "saifi_bv_all_within_1pct": bool((v3.saifi_bv_rel_diff <= 0.01).all()),
                   "limit_within_1pct": int((v3.limit_rel_diff <= 0.01).sum()), "rows": v3.to_dict(orient="records")}
    out["gate_passes"] = out["dpp4"]["all_within_1pct"] and out["dpp3"]["bv_all_within_1pct"]
    (T / "validation.json").write_text(json.dumps(out, indent=1))
    print(v4[["edb", "saidi_bound", "ref_saidi_bound", "saidi_cap", "ref_saidi_cap", "max_rel_diff"]].to_string())
    print(v3[["edb", "saidi_bound", "det_saidi_bv", "saidi_limit", "det_saidi_limit", "bv_rel_diff", "limit_rel_diff"]].to_string())
    print("gate passes:", out["gate_passes"])


if __name__ == "__main__":
    {"validate": validate}[sys.argv[1]]()
