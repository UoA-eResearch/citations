#!/usr/bin/env python
"""Attribution analysis (plan.md sec 4-6).
Per forecast: event-peak TW (regional max of 2 m TW at 06, 12, 18 UTC on the event day) and area-mean TW (land-point mean
of the event-day max TW). Attributable changes dA = TW_F - TW_A and dB = TW_F - TW_B per (event, lead, model).
H1: R = mean dB / mean dA, two-level bootstrap (events, then members within event), 5,000 draws.
H2: dynamic / static ratio of dB at lead 2 days (static = the same deltas applied offline to the ERA5 event-day fields).
V1: factual event-peak TW error against ERA5. V2: global-mean 2 m temperature F - B at the final step vs imposed.
Output: results/tables/per_forecast.csv, results/tables/attribution.csv, results/tables/hypotheses.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from perturb import deltas_to_n320  # noqa: E402
from run_forecasts import LEADS, region_mask  # noqa: E402
from wetbulb import es, wetbulb  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
PROC, TAB = RUN / "data" / "processed", RUN / "results" / "tables"


def tw_metrics(f, land):
    tws = np.stack([wetbulb(f[f"2t_{h:02d}"], f[f"2d_{h:02d}"], f[f"sp_{h:02d}"]) for h in (6, 12, 18)]) - 273.15
    daymax = tws.max(axis=0)
    return float(daymax.max()), float(daymax[land].mean())


def static_cf(e5, dtas, world):
    """The surface part of the counterfactual (as in perturb.counterfactual) applied to ERA5 event-day fields."""
    out = {}
    for h in (6, 12, 18):
        t, td, sp = e5[f"2t_{h:02d}"].astype(float), e5[f"2d_{h:02d}"].astype(float), e5[f"sp_{h:02d}"].astype(float)
        excess = np.maximum(0.0, td - t)
        t2 = t - dtas
        if world == "B":
            a = np.log(es(td - 273.15) / es(t - 273.15) * es(t2 - 273.15) / 6.112)
            td2 = 243.5 * a / (17.67 - a) + 273.15
        else:
            td2 = td
        out[f"2t_{h:02d}"], out[f"2d_{h:02d}"], out[f"sp_{h:02d}"] = t2, np.minimum(td2, t2 + excess), sp
    return out


def boot_ratio(d, num, den, nboot=5000, seed=0):
    rng = np.random.default_rng(seed)
    groups = [g for _, g in d.groupby("event")]
    est = d[num].mean() / d[den].mean()
    bs = []
    for _ in range(nboot):
        pick = [groups[i] for i in rng.integers(0, len(groups), len(groups))]
        s = pd.concat([g.iloc[rng.integers(0, len(g), len(g))] for g in pick])
        bs.append(s[num].mean() / s[den].mean())
    return float(est), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


def main():
    ev = pd.read_csv(TAB / "events.csv", parse_dates=["date"])
    models = sorted(pd.read_csv(TAB / "cmip6_models.csv").model.unique())
    ll = np.load(PROC / "n320_latlon.npz")
    lat, lon = ll["lat"], ll["lon"]
    coslat = np.cos(np.radians(lat))
    rows, att = [], []
    for _, e in ev.iterrows():
        mask = region_mask(lat, lon, e.region)
        e5_full = np.load(PROC / "era5_event" / f"{e.event_id}.npz")
        e5 = {k: e5_full[k][mask] for k in e5_full.files}
        land = e5["lsm_12"] > 0.5
        truth_peak, truth_area = tw_metrics(e5, land)
        for m in models:
            d = deltas_to_n320(m, int(e.date.month))
            dtas = d["tas"][mask].astype(float)
            s_f = tw_metrics(e5, land)
            s_a, s_b = tw_metrics(static_cf(e5, dtas, "A"), land), tw_metrics(static_cf(e5, dtas, "B"), land)
            gm_imposed = float(np.sum(d["tas"] * coslat) / coslat.sum())
            for L in LEADS:
                fF = np.load(PROC / "forecasts" / f"{e.event_id}_L{L}_F_none.npz")
                fA = np.load(PROC / "forecasts" / f"{e.event_id}_L{L}_A_{m}.npz")
                fB = np.load(PROC / "forecasts" / f"{e.event_id}_L{L}_B_{m}.npz")
                pF, pA, pB = tw_metrics(fF, land), tw_metrics(fA, land), tw_metrics(fB, land)
                att.append(dict(event=e.event_id, region=e.region, lead=L, model=m,
                                dA_peak=pF[0] - pA[0], dB_peak=pF[0] - pB[0], dA_area=pF[1] - pA[1], dB_area=pF[1] - pB[1],
                                static_dA_peak=s_f[0] - s_a[0], static_dB_peak=s_f[0] - s_b[0],
                                static_dA_area=s_f[1] - s_a[1], static_dB_area=s_f[1] - s_b[1],
                                gm_2t_F_minus_B=float(fF["global_2t_final"] - fB["global_2t_final"]), gm_imposed=gm_imposed))
            for L in LEADS:
                if m == models[0]:
                    fF = np.load(PROC / "forecasts" / f"{e.event_id}_L{L}_F_none.npz")
                    pF = tw_metrics(fF, land)
                    rows.append(dict(event=e.event_id, region=e.region, date=e.date.date(), lead=L, era5_peak=truth_peak,
                                     forecast_peak=pF[0], err_peak=pF[0] - truth_peak, era5_area=truth_area, forecast_area=pF[1],
                                     err_area=pF[1] - truth_area))
    pf, a = pd.DataFrame(rows), pd.DataFrame(att)
    pf.to_csv(TAB / "per_forecast.csv", index=False)
    a.to_csv(TAB / "attribution.csv", index=False)
    hyp = []
    for metric in ("peak", "area"):
        est, lo, hi = boot_ratio(a, f"dB_{metric}", f"dA_{metric}")
        v = "supported" if (est >= 1.5 and lo > 1) else ("contradicted" if hi < 1.5 else "inconclusive")
        hyp.append(dict(hypothesis="H1: R = mean dB / mean dA" + (" (primary)" if metric == "peak" else " (area-mean TW)"),
                        est=est, lo=lo, hi=hi, verdict=v if metric == "peak" else ""))
        l2 = a[a.lead == 2]
        est, lo, hi = boot_ratio(l2, f"dB_{metric}", f"static_dB_{metric}")
        v = ("consistent" if (lo >= 0.75 and hi <= 1.25) else "damped" if hi < 0.75 else "amplified" if lo > 1.25 else "inconclusive")
        hyp.append(dict(hypothesis=f"H2: dynamic / static dB at lead 2 ({metric})", est=est, lo=lo, hi=hi,
                        verdict=v if metric == "peak" else ""))
        est, lo, hi = boot_ratio(a, f"static_dB_{metric}", f"static_dA_{metric}")
        hyp.append(dict(hypothesis=f"static R (no forecast; {metric})", est=est, lo=lo, hi=hi, verdict=""))
    for L in LEADS:
        s = a[a.lead == L]
        hyp.append(dict(hypothesis=f"H3: mean dA / dB at lead {L} (peak, degC)", est=s.dA_peak.mean(), lo=s.dB_peak.mean(),
                        hi=np.nan, verdict=""))
    hyp.append(dict(hypothesis="V1: factual peak-TW error at lead 2 (mean abs, degC)", est=pf[pf.lead == 2].err_peak.abs().mean(),
                    lo=pf[pf.lead == 2].err_peak.mean(), hi=float((pf[pf.lead == 2].err_peak.abs() > 2).mean()), verdict=""))
    hyp.append(dict(hypothesis="V2: global-mean 2t F - B at final step / imposed (mean)",
                    est=float((a.gm_2t_F_minus_B / a.gm_imposed).mean()), lo=np.nan, hi=np.nan, verdict=""))
    h = pd.DataFrame(hyp)
    h.to_csv(TAB / "hypotheses.csv", index=False)
    pd.set_option("display.width", 200)
    print(h.round(3).to_string(index=False))
    print(pf.round(2).to_string(index=False))
    print(a.groupby(["event", "lead"])[["dA_peak", "dB_peak", "static_dA_peak", "static_dB_peak"]].mean().round(2).to_string())


if __name__ == "__main__":
    sys.exit(main())
