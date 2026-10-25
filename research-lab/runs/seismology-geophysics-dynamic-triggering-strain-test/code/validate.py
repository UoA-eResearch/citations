"""Proxy validation (plan section 6, G3): recall of ComCat M >= 1.0 events on 100 quiet days.

For each event within 30 km of an analysable US station (at least 2 neighbours within 50 km with picks that month;
station-day loaded), the nearest such station counts a hit if it has a local-event pair with t0 within +-10 s of the
event's origin time. Recall overall and by magnitude band.
-> results/tables/proxy_validation.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
sys.path.insert(0, str(RUN / "code"))
from windows import gc_km  # noqa: E402


def main():
    ev = pd.read_csv(D / "cat" / "region_m1_validation.csv", parse_dates=["time"])
    st = pd.read_parquet(D / "raw" / "stations.parquet", columns=["id", "latitude", "longitude", "state"])
    us = st[~st.state.fillna("").str.contains(r"\(")].groupby("id")[["latitude", "longitude"]].median()
    vp = pd.concat([pd.read_parquet(f) for f in sorted((D / "proxy").glob("valpairs_*.parquet"))], ignore_index=True)
    nbr = pd.concat([pd.read_parquet(f).assign(month=f.stem[4:]) for f in sorted((D / "proxy").glob("nbr_*.parquet"))])
    av = pd.concat([pd.read_parquet(f, columns=["tid", "date", "status"]) for f in sorted((D / "raw" / "availability").glob("*.parquet"))])
    days = set(ev.time.dt.strftime("%Y-%m-%d"))
    av = av[av.date.astype(str).isin(days) & (av.status == "loaded")]
    loaded = set(zip(av.tid, av.date.astype(str)))
    rows = []
    for r in ev.itertuples():
        month, day = r.time.strftime("%Y-%m"), r.time.strftime("%Y-%m-%d")
        ok = nbr[(nbr.month == month) & (nbr.neighbours_50km >= 2)].tid
        cand = us.loc[us.index.intersection(ok)]
        cand = cand[[(t, day) in loaded for t in cand.index]]
        if not len(cand):
            continue
        dk = gc_km(r.latitude, r.longitude, cand.latitude.to_numpy(), cand.longitude.to_numpy())
        if dk.min() > 30:
            continue
        tid = cand.index[int(np.argmin(dk))]
        o = r.time.value // 10**6
        t0 = vp.t0[vp.tid == tid].to_numpy()
        rows.append({"mag": r.mag, "dist_km": float(dk.min()), "hit": bool((np.abs(t0 - o) <= 10_000).any())})
    d = pd.DataFrame(rows)
    band = pd.cut(d.mag, [1, 1.5, 2, 3, 10], right=False, labels=["1.0-1.5", "1.5-2.0", "2.0-3.0", ">=3.0"])
    out = {"events_on_days": int(len(ev)), "events_within_30km": int(len(d)), "recall": round(float(d.hit.mean()), 4),
           "by_magnitude": {str(k): {"events": int(len(g)), "recall": round(float(g.hit.mean()), 4)} for k, g in d.groupby(band, observed=True)}}
    (T / "proxy_validation.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
