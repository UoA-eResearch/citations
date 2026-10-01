#!/usr/bin/env python
"""Checks requested by the independent review (deviations.md D4).
1. Linearity control (control_scale.py): event-peak TW change at scale -1, 0.5 and 1 for E1 and E5, lead 2.
2. Member-level tracking: correlation of the forecast change with the static change; per-member forecast/static ratio.
3. World A saturation at the initial time: share of above-ground points at RH >= 0.999 (1000, 925, 850 hPa; 2 m), F vs A.
4. R by lead, R leaving out each event, and a bootstrap that resamples models as clusters.
5. Mechanism: land and sea mean F - CF 2 m temperature and dewpoint by event and world.
Output: results/tables/control_linearity.csv, review_checks.csv, mechanism_2t_2d.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze import boot_ratio, tw_metrics  # noqa: E402
from perturb import counterfactual, deltas_to_n320  # noqa: E402
from run_forecasts import region_mask  # noqa: E402
from wetbulb import es, qsat  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
PROC, TAB = RUN / "data" / "processed", RUN / "results" / "tables"
FC = PROC / "forecasts"


def main():
    ev = pd.read_csv(TAB / "events.csv", parse_dates=["date"]).set_index("event_id")
    models = sorted(pd.read_csv(TAB / "cmip6_models.csv").model.unique())
    ll = np.load(PROC / "n320_latlon.npz")
    lat, lon = ll["lat"], ll["lon"]
    a = pd.read_csv(TAB / "attribution.csv")
    rows = []

    # 1. linearity control
    lin = []
    for eid in ("E1", "E5"):
        e = ev.loc[eid]
        m_ = region_mask(lat, lon, e.region)
        land = np.load(PROC / "era5_event" / f"{eid}.npz")["lsm_12"][m_] > 0.5
        pF = tw_metrics(np.load(FC / f"{eid}_L2_F_none.npz"), land)[0]
        for m in models:
            for w in ("A", "B"):
                for s, name in ((1.0, f"{eid}_L2_{w}_{m}.npz"), (0.5, f"{eid}_L2_{w}_{m}_s0.5.npz"), (-1.0, f"{eid}_L2_{w}_{m}_s-1.npz")):
                    p = FC / name
                    if p.exists():
                        lin.append(dict(event=eid, model=m, world=w, scale=s, dTW_peak=pF - tw_metrics(np.load(p), land)[0]))
    if lin:
        lin = pd.DataFrame(lin)
        lin.to_csv(TAB / "control_linearity.csv", index=False)
        print(lin.groupby(["world", "scale"]).dTW_peak.agg(["mean", "std", "min", "max", "count"]).round(2).to_string())

    # 2. member-level tracking
    rows.append(dict(check="corr(forecast dB_peak, static dB_peak) over members", value=float(np.corrcoef(a.dB_peak, a.static_dB_peak)[0, 1])))
    rows.append(dict(check="corr(forecast dA_peak, static dA_peak) over members", value=float(np.corrcoef(a.dA_peak, a.static_dA_peak)[0, 1])))
    l2 = a[a.lead == 2]
    r = l2.dB_peak / l2.static_dB_peak
    rows.append(dict(check="per-member forecast/static dB at lead 2: median [IQR]",
                     value=f"{r.median():.2f} [{r.quantile(.25):.2f}, {r.quantile(.75):.2f}]; negative {int((r < 0).sum())} of {len(r)}"))
    neg = a[(a.static_dB_peak < 0)]
    rows.append(dict(check="members whose static dB is negative (counterfactual hotter/moister): forecast dB range",
                     value=f"{len(neg)} members; forecast dB {neg.dB_peak.min():.2f} to {neg.dB_peak.max():.2f}; models {sorted(neg.model.unique())}"))

    # 3. world A saturation at t0
    for eid in ("E1", "E3"):
        e = ev.loc[eid]
        z = np.load(PROC / "ic" / f"{eid}_L2.npz")
        st = {k: z[k] for k in z.files if k != "t0"}
        cf = counterfactual(st, deltas_to_n320(models[0], int(e.date.month)), "A")
        for lev in (1000, 925, 850):
            above = st["sp"][1] > lev * 100
            rh_f = st[f"q_{lev}"][1] / qsat(st[f"t_{lev}"][1], lev * 100)
            rh_a = cf[f"q_{lev}"][1] / qsat(cf[f"t_{lev}"][1], lev * 100)
            rows.append(dict(check=f"{eid} t0 {lev} hPa: share of above-ground points saturated (RH>=0.999), F / A",
                             value=f"{(rh_f[above] >= 0.999).mean():.3f} / {(rh_a[above] >= 0.999).mean():.3f}"))
        m_ = region_mask(lat, lon, e.region)
        rh2f = es(st["2d"][1] - 273.15) / es(st["2t"][1] - 273.15)
        rh2a = es(cf["2d"][1] - 273.15) / es(cf["2t"][1] - 273.15)
        rows.append(dict(check=f"{eid} t0 2 m, region: share of points at RH>=0.999, F / A",
                         value=f"{(rh2f[m_] >= 0.999).mean():.3f} / {(rh2a[m_] >= 0.999).mean():.3f}"))

    # 4. R by lead, leave-one-event-out, model-cluster bootstrap
    for L in (2, 4, 6):
        for metric in ("peak", "area"):
            est, lo, hi = boot_ratio(a[a.lead == L], f"dB_{metric}", f"dA_{metric}")
            rows.append(dict(check=f"R ({metric}) at lead {L}", value=f"{est:.2f} [{lo:.2f}, {hi:.2f}]"))
    for eid in ev.index:
        s = a[a.event != eid]
        rows.append(dict(check=f"R (peak) leaving out {eid}", value=f"{s.dB_peak.mean() / s.dA_peak.mean():.2f}"))
    rng = np.random.default_rng(4)
    bs = []
    for _ in range(5000):
        pick = rng.choice(models, len(models))
        s = pd.concat([a[a.model == m] for m in pick])
        bs.append(s.dB_peak.mean() / s.dA_peak.mean())
    rows.append(dict(check="R (peak), bootstrap resampling models as clusters", value=f"[{np.percentile(bs, 2.5):.2f}, {np.percentile(bs, 97.5):.2f}]"))
    out = pd.DataFrame(rows)
    out.to_csv(TAB / "review_checks.csv", index=False)
    print(out.to_string(index=False))

    # 5. mechanism (land and sea, by event and world)
    mech = []
    for eid, e in ev.iterrows():
        m_ = region_mask(lat, lon, e.region)
        land = np.load(PROC / "era5_event" / f"{eid}.npz")["lsm_12"][m_] > 0.5
        for L in (2, 4, 6):
            F = np.load(FC / f"{eid}_L{L}_F_none.npz")
            for w in ("A", "B"):
                for surf, sel in (("land", land), ("sea", ~land)):
                    d2t = np.mean([np.mean([(F[f"2t_{h:02d}"] - np.load(FC / f"{eid}_L{L}_{w}_{m}.npz")[f"2t_{h:02d}"])[sel].mean() for h in (6, 12, 18)]) for m in models])
                    d2d = np.mean([np.mean([(F[f"2d_{h:02d}"] - np.load(FC / f"{eid}_L{L}_{w}_{m}.npz")[f"2d_{h:02d}"])[sel].mean() for h in (6, 12, 18)]) for m in models])
                    mech.append(dict(event=eid, lead=L, world=w, surface=surf, d2t=d2t, d2d=d2d))
    mech = pd.DataFrame(mech)
    mech.to_csv(TAB / "mechanism_2t_2d.csv", index=False)
    print(mech[mech.surface == "land"].groupby(["event", "world"])[["d2t", "d2d"]].mean().round(2).to_string())


if __name__ == "__main__":
    sys.exit(main())
