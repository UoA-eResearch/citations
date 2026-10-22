"""dv/v by stretching (plan section 2), from the daily correlations in data/ccf/.

Per pair: bandpass 0.5-2 Hz; symmetric correlation (mean of the causal and time-reversed acausal sides); coda window
t1 = max(5 s, 2d / 1.5 km/s) to t1 + 20 s; reference = mean of the pair-segment's 2013-2020 daily correlations;
current = 10-day centred moving stack (at least 5 days); the current stack is stretched, cur(t(1+e)), against the
reference and dv/v = -e at the best correlation coefficient (grid +/-2%: 0.05% steps, then 0.005% around the best).
Station segments follow the plan's rule (same location code and sensor description, gaps up to 7 days).

Writes results/tables/dvv_daily.parquet (pair, date, dvv_pct, cc, ndays, seg) and results/tables/pairs.csv.
"""
import itertools
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import butter, sosfiltfilt

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"
FS, L = 20.0, 2000
TRAIN_END = pd.Timestamp("2020-12-31")


def segments():
    """Per station: list of (start, end) of continuous segments, from the FDSN channel epochs (location 10, Z)."""
    d = pd.read_csv(RUN / "results" / "tables" / "fdsn_channels.txt", sep="|")
    d.columns = [c.strip("# ").strip() for c in d.columns]
    d = d[(d.Location == 10) & d.Channel.isin(["EHZ", "HHZ"])].copy()
    d["start"] = pd.to_datetime(d.StartTime.str[:10])
    d["end"] = pd.to_datetime(d.EndTime.fillna("2026-12-31").astype(str).str[:10].replace("nan", "2026-12-31"))
    out = {}
    for st, g in d.sort_values("start").groupby("Station"):
        segs, cur = [], None
        for r in g.itertuples():
            if cur and r.SensorDescription == cur[2] and (r.start - cur[1]).days <= 7:
                cur = (cur[0], max(cur[1], r.end), cur[2])
            else:
                if cur:
                    segs.append(cur)
                cur = (r.start, r.end, r.SensorDescription)
        segs.append(cur)
        out[st] = [(a, b) for a, b, _ in segs]
    return out


def seg_index(segs, dates):
    s = np.full(len(dates), -1)
    for k, (a, b) in enumerate(segs):
        s[(dates >= a) & (dates <= b)] = k
    return s


def load():
    files = sorted((RUN / "data" / "ccf").glob("*/*.npz"))
    dates = pd.to_datetime([f.stem for f in files])
    z0 = np.load(files[0])
    stations = list(z0["stations"])
    C = np.zeros((len(files), len(z0["nwin"]), 2 * L + 1), np.float32)
    N = np.zeros((len(files), len(z0["nwin"])), np.int16)
    for i, f in enumerate(files):
        z = np.load(f)
        C[i], N[i] = z["ccf"], z["nwin"]
    return dates, stations, C, N


def main():
    dates, stations, C, N = load()
    segs = segments()
    import pyproj
    ch = pd.read_csv(RUN / "results" / "tables" / "fdsn_channels.txt", sep="|")
    ch.columns = [c.strip("# ").strip() for c in ch.columns]
    loc = ch.groupby("Station")[["Latitude", "Longitude"]].first()
    geod = pyproj.Geod(ellps="WGS84")
    sos = butter(4, [0.5, 2.0], btype="band", fs=FS, output="sos")
    lags = np.arange(-L, L + 1) / FS
    pos = lags[L:]
    rows, prow = [], []
    for p, (i, j) in enumerate(itertools.combinations(range(len(stations)), 2)):
        a, b = stations[i], stations[j]
        _, _, dist = geod.inv(loc.Longitude[a], loc.Latitude[a], loc.Longitude[b], loc.Latitude[b])
        d_km = dist / 1000
        t1 = max(5.0, 2 * d_km / 1.5)
        t2 = t1 + 20.0
        if t2 > 95:
            prow.append({"pair": f"{a}-{b}", "dist_km": round(d_km, 2), "t1": t1, "note": "coda window beyond lag range"})
            continue
        have = N[:, p] > 0
        if have.sum() < 200:
            prow.append({"pair": f"{a}-{b}", "dist_km": round(d_km, 2), "t1": t1, "days": int(have.sum()), "note": "too few days"})
            continue
        x = sosfiltfilt(sos, C[:, p, :].astype(float), axis=1)
        sym = 0.5 * (x[:, L:] + x[:, L::-1])
        si, sj = seg_index(segs[a], dates), seg_index(segs[b], dates)
        seg = np.where((si >= 0) & (sj >= 0), si * 100 + sj, -1)
        win = (pos >= t1) & (pos <= t2)
        tw = pos[win]
        for sg in np.unique(seg[(seg >= 0) & have]):
            m = (seg == sg) & have
            mt = m & (dates <= TRAIN_END)
            if mt.sum() < 60:
                continue
            ref = sym[mt].mean(axis=0)
            idx = np.nonzero(m)[0]
            # 10-day centred moving stack over valid days of this pair-segment
            cum = np.zeros((len(dates) + 1, sym.shape[1]))
            cum[1:] = np.cumsum(np.where(m[:, None], sym, 0.0), axis=0)
            cnt = np.concatenate([[0], np.cumsum(m)])
            dd = dates.to_numpy()
            for k in idx:
                lo = np.searchsorted(dd, dd[k] - np.timedelta64(5, "D"))
                hi = np.searchsorted(dd, dd[k] + np.timedelta64(5, "D"), side="right")
                n = cnt[hi] - cnt[lo]
                if n < 5:
                    continue
                cur = (cum[hi] - cum[lo]) / n
                best = None
                for grid in (np.arange(-0.02, 0.02 + 1e-12, 0.0005), None):
                    if grid is None:
                        grid = np.arange(best - 0.0005, best + 0.0005 + 1e-12, 0.00005)
                    r = ref[win]
                    rz = (r - r.mean()) / (r.std() + 1e-20)
                    ccs = []
                    for e in grid:
                        s = np.interp(tw * (1 + e), pos, cur)
                        sz = (s - s.mean()) / (s.std() + 1e-20)
                        ccs.append(float((sz * rz).mean()))
                    kbest = int(np.argmax(ccs))
                    best, ccbest = grid[kbest], ccs[kbest]
                rows.append({"pair": f"{a}-{b}", "date": dates[k], "dvv_pct": -100 * best, "cc": ccbest, "ndays": int(n),
                             "seg": int(sg)})
        prow.append({"pair": f"{a}-{b}", "dist_km": round(d_km, 2), "t1": round(t1, 2), "days": int(have.sum()), "note": ""})
        print(f"{a}-{b}", round(d_km, 1), "km", int(have.sum()), "days", flush=True)
    pd.DataFrame(rows).to_parquet(T / "dvv_daily.parquet", index=False)
    pd.DataFrame(prow).to_csv(T / "pairs.csv", index=False)


if __name__ == "__main__":
    main()
