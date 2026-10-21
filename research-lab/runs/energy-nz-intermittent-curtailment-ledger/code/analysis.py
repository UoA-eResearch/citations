"""Curtailment shares, H1 and H2, the measurability gate, variants and the monthly ledger (plan sections 1, 3, 4).

Reads data/panel.parquet (build.py). Writes results/tables/primary.json, robustness.json and ledger_monthly.csv.

Definitions (plan section 1), per POC (a point of connection carrying wind or solar):
  unconstrained TP   price >= maxprice + MARGIN, price >= 1 $/MWh, offered >= P
  k                  median(G / P) over unconstrained TPs with P >= 10% of the POC's maximum offered MW, per quarter
  P_hat = k * P; g = P_hat - G; f = FLOOR_Q percentile of g over the same unconstrained TPs
  curtailed TP       g > f; curtailed energy = sum(g) * 0.5 h; available energy = sum(P_hat) * 0.5 h
  a POC-quarter with fewer than 200 unconstrained TPs takes its k and f from the POC-year
Bootstrap: 7-day moving blocks of days, 2,000 resamples, seed 20261021, k and f re-estimated in each resample.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
RUN = Path(__file__).resolve().parents[1]
DATA = RUN / "data"
TAB = RUN / "results" / "tables"
SEED, B, BLOCK = 20261021, 2000, 7
BASE = ("2020-01-01", "2020-12-31")
RECENT = ("2025-07-01", "2026-06-30")
RTP = "2022-11-01"


def prepare(df):
    d = df.dropna(subset=["P", "G", "price"]).copy()
    d = d[d.P >= 0]
    d["quarter"] = d.date.dt.to_period("Q").astype(str)
    d["year"] = d.date.dt.year
    d["cap"] = d.groupby(["poc", "quarter"]).offered.transform("max")
    return d


def calibrate(d, margin=1.0, floor_q=95, bias=True, use="P"):
    """k and f per POC-quarter (pooled to POC-year when thin); returns d with P_hat, g, f, curtailed."""
    d = d.copy()
    pot = d[use]
    unc = (d.price >= d.maxprice.fillna(0) + margin) & (d.price >= 1.0) & (d.offered >= pot)
    big = unc & (pot >= 0.1 * d.cap) & (pot > 0)
    ratio = (d.G / pot).where(big)
    kq = ratio.groupby([d.poc, d.quarter]).transform("median")
    ky = ratio.groupby([d.poc, d.year]).transform("median")
    nq = big.groupby([d.poc, d.quarter]).transform("sum")
    k = (kq.where(nq >= 200, ky) if bias else pd.Series(1.0, index=d.index)).fillna(1.0)
    d["k"] = k
    d["P_hat"] = k * pot
    d["g"] = d.P_hat - d.G
    gq = d.g.where(unc)
    fq = gq.groupby([d.poc, d.quarter]).transform(lambda v: np.nanpercentile(v, floor_q) if v.notna().any() else np.nan)
    fy = gq.groupby([d.poc, d.year]).transform(lambda v: np.nanpercentile(v, floor_q) if v.notna().any() else np.nan)
    nu = unc.groupby([d.poc, d.quarter]).transform("sum")
    d["f"] = fq.where(nu >= 200, fy)
    d["unconstrained"] = unc
    d["curtailed"] = d.g > d.f
    return d


def shares(d, above_floor=False):
    c = d[d.curtailed]
    curt = ((c.g - c.f) if above_floor else c.g).sum() * 0.5
    avail = d.P_hat.sum() * 0.5
    nonprice = c[c.price > 0.01]
    np_curt = ((nonprice.g - nonprice.f) if above_floor else nonprice.g).sum() * 0.5
    return dict(share=curt / avail if avail else np.nan, curtailed_mwh=curt, available_mwh=avail,
                nonprice_share=np_curt / curt if curt else np.nan)


def period(d, lo, hi):
    return d[(d.date >= lo) & (d.date <= hi)]


def estimate(d, **kw):
    """Shares for the baseline and recent periods with calibration done within each period."""
    above = kw.pop("above_floor", False)
    min_k = kw.pop("min_k", None)
    cb, cr = calibrate(period(d, *BASE), **kw), calibrate(period(d, *RECENT), **kw)
    if min_k is not None:                      # D1 item 6: drop POC-quarters whose metering covers part of the plant
        cb, cr = cb[cb.k >= min_k], cr[cr.k >= min_k]
    return shares(cb, above), shares(cr, above)


def block_resample(d, rng):
    days = np.sort(d.date.unique())
    n = len(days)
    starts = rng.integers(0, n - BLOCK + 1, size=int(np.ceil(n / BLOCK)))
    pick = np.concatenate([days[s:s + BLOCK] for s in starts])[:n]
    by_day = {k: v for k, v in d.groupby("date")}
    parts = [by_day[t].assign(date=pd.Timestamp(days[i])) for i, t in enumerate(pick)]
    out = pd.concat(parts, ignore_index=True)
    out["quarter"] = out.date.dt.to_period("Q").astype(str)
    out["year"] = out.date.dt.year
    return out


def main():
    d = prepare(pd.read_parquet(DATA / "panel.parquet"))
    base_d, rec_d = period(d, *BASE), period(d, *RECENT)
    b, r = estimate(d)
    rng = np.random.default_rng(SEED)
    draws = []
    for _ in range(B):
        bb = shares(calibrate(block_resample(base_d, rng)))
        rr = shares(calibrate(block_resample(rec_d, rng)))
        draws.append((bb["share"], rr["share"], rr["share"] - bb["share"], rr["nonprice_share"]))
    draws = np.array(draws)
    ci = lambda j: [float(np.nanpercentile(draws[:, j], 2.5)), float(np.nanpercentile(draws[:, j], 97.5))]
    res = {"baseline_2020": {**b, "share_ci": ci(0)}, "recent_2025_26": {**r, "share_ci": ci(1)},
           "increase": {"estimate": r["share"] - b["share"], "ci": ci(2)},
           "nonprice_share_recent": {"estimate": r["nonprice_share"], "ci": ci(3)}}
    bl, rh, inc = res["baseline_2020"], res["recent_2025_26"], res["increase"]
    if bl["share"] < 0.005 and rh["share"] >= 0.02 and inc["ci"][0] > 0:
        h1 = "Supported"
    elif rh["share_ci"][1] < 0.02 or bl["share_ci"][0] > 0.005:
        h1 = "Refuted"
    else:
        h1 = "Inconclusive"
    npc = res["nonprice_share_recent"]
    h2 = ("Supported" if npc["estimate"] >= 0.5 and npc["ci"][0] > 0.4 else
          "Refuted" if npc["ci"][1] < 0.5 else "Inconclusive")
    res["H1"], res["H2"] = h1, h2
    # measurability gate: median POC's floor in the recent period relative to its mean potential
    cr = calibrate(rec_d)
    gate = cr.groupby("poc").apply(lambda x: x.f.median() / x.P_hat.mean() if x.P_hat.mean() > 0 else np.nan)
    res["gate_median_floor_over_mean_potential"] = float(gate.median())
    res["gate_measurable"] = bool(gate.median() <= 0.25)
    res["gate_by_poc"] = gate.round(3).to_dict()
    # causes in the recent period
    c = cr[cr.curtailed]
    cause = np.where(c.offered < c.P_hat, "offer-limited",
                     np.where(c.price <= c.maxprice.fillna(0), "price-driven", "other"))
    res["causes_recent_mwh"] = (c.g * 0.5).groupby(cause).sum().round(1).to_dict()
    json.dump(res, open(TAB / "primary.json", "w"), indent=1, default=float)
    print(json.dumps({k: v for k, v in res.items() if k != "gate_by_poc"}, indent=1, default=float))

    rob = {}
    for name, kw in {"no_bias_correction": dict(bias=False), "above_floor_only": dict(above_floor=True),
                     "floor_p90": dict(floor_q=90), "floor_p99": dict(floor_q=99), "margin_10": dict(margin=10.0),
                     "exclude_k_below_0_5": dict(min_k=0.5)}.items():
        bb, rr = estimate(d, **kw)
        rob[name] = {"baseline_share": bb["share"], "recent_share": rr["share"], "recent_nonprice": rr["nonprice_share"]}
    if d.MaximumOutputMegawatts.notna().mean() > 0.5 if "MaximumOutputMegawatts" in d else False:
        bb, rr = estimate(d, use="MaximumOutputMegawatts")
        rob["max_output_instead_of_potential"] = {"baseline_share": bb["share"], "recent_share": rr["share"]}
    else:
        rob["max_output_instead_of_potential"] = "not estimable: MaximumOutputMegawatts is empty for these units"
    loo = {}
    for p in sorted(d.poc.unique()):
        bb, rr = estimate(d[d.poc != p])
        loo[p] = {"baseline_share": bb["share"], "recent_share": rr["share"]}
    rob["leave_one_poc_out"] = loo
    wind = d[d.fuel == "Wind"]
    bb, rr = estimate(wind)
    rob["wind_only"] = {"baseline_share": bb["share"], "recent_share": rr["share"], "recent_nonprice": rr["nonprice_share"]}
    pre, post = calibrate(d[(d.date >= "2020-01-01") & (d.date < RTP)]), calibrate(d[(d.date >= RTP) & (d.date <= RECENT[1])])
    rob["pre_rtp_2020_to_oct2022"], rob["post_rtp_nov2022_to_jun2026"] = shares(pre), shares(post)
    # weather plausibility (plan section 4): correlation of the potential forecast, and of output, with ERA5 at the
    # plant on unconstrained TPs; the TP is matched to the hour it starts in
    import weather
    wx = {}
    try:
        weather.fetch(sorted(d.poc.unique()))
    except Exception as e:                                  # reported, not fatal: a secondary check
        wx["fetch_error"] = repr(e)
    cal = calibrate(d[(d.date >= "2020-01-01") & (d.date <= RECENT[1])])
    for p in sorted(d.poc.unique()):
        try:
            h = weather.hourly(p)
        except Exception:
            continue
        x = cal[(cal.poc == p) & cal.unconstrained].copy()
        x["time"] = x.date + pd.to_timedelta((x.tp - 1) * 30, unit="min")
        x["time"] = x.time.dt.floor("h")
        x = x.merge(h, on="time", how="inner")
        col = "swr" if (x.fuel == "Solar").all() else "wind100"
        if len(x) > 100:
            wx[p] = {"weather": col, "n": int(len(x)), "corr_potential": round(float(x.P.corr(x[col])), 3),
                     "corr_output": round(float(x.G.corr(x[col])), 3)}
    rob["weather_check"] = wx
    # frozen projection for the 12 months to 30 June 2027 (plan section 4)
    rec = calibrate(rec_d)
    a_rec = rec.groupby("poc").P_hat.sum() * 0.5
    first = d.groupby("poc").date.min()
    late = d[d.date <= "2026-09-30"].copy()
    late["month"] = late.date.dt.to_period("M")
    lcal = calibrate(late)
    lcal["month"] = lcal.date.dt.to_period("M")
    monthly = lcal.groupby(["poc", "month"]).P_hat.sum() * 0.5
    proj = {}
    for p in first.index:
        if first[p] <= pd.Timestamp(RECENT[0]) and p in a_rec:
            proj[p] = float(a_rec[p])
        elif p in monthly.index.get_level_values(0):
            proj[p] = float(monthly.loc[p].mean() * 12)
    a_proj, a_now = sum(proj.values()), float(a_rec.sum())
    rob["projection_2026_27"] = {"recent_share": res["recent_2025_26"]["share"], "available_2025_26_mwh": a_now,
                                 "available_projected_mwh": a_proj,
                                 "projected_share": res["recent_2025_26"]["share"] * a_proj / a_now if a_now else None,
                                 "rule": "2025/26 share x projected available energy / 2025/26 available energy; "
                                         "plants first seen after 1 July 2025 annualised from their months to Sep 2026",
                                 "score_after": "2027-06-30"}
    json.dump(rob, open(TAB / "robustness.json", "w"), indent=1, default=float)

    # monthly ledger by POC, with calibration by POC-quarter over the whole panel
    full = calibrate(d)
    full["month"] = full.date.dt.to_period("M").astype(str)
    full["cause"] = np.where(~full.curtailed, "", np.where(full.offered < full.P_hat, "offer-limited",
                             np.where(full.price <= full.maxprice.fillna(0), "price-driven", "other")))
    full["curt_mwh"] = np.where(full.curtailed, full.g * 0.5, 0.0)
    full["avail_mwh"] = full.P_hat * 0.5
    led = full.groupby(["month", "poc", "fuel"]).agg(available_mwh=("avail_mwh", "sum"),
                                                     curtailed_mwh=("curt_mwh", "sum"),
                                                     output_mwh=("G", lambda v: v.sum() * 0.5)).reset_index()
    for cz in ("offer-limited", "price-driven", "other"):
        led[f"curtailed_{cz}_mwh"] = full[full.cause == cz].groupby(["month", "poc", "fuel"]).curt_mwh.sum() \
            .reindex(pd.MultiIndex.from_frame(led[["month", "poc", "fuel"]])).fillna(0).to_numpy()
    led.round(2).to_csv(TAB / "ledger_monthly.csv", index=False)
    print("robustness and ledger written")


if __name__ == "__main__":
    main()
