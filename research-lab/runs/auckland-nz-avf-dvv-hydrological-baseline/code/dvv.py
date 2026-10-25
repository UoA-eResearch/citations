"""dv/v by stretching (plan section 2), from the daily correlations in data/ccf/.

Per pair: bandpass 0.5-2 Hz; symmetric correlation (mean of the causal and time-reversed acausal sides); coda window
t1 = max(5 s, 2d / 1.5 km/s) to t1 + 20 s; reference = mean of the pair-segment's 2013-2020 daily correlations;
current = centred moving stack of +/-5 days (11 days, at least 5 valid); the current stack is stretched, cur(t(1+e)),
against the reference and dv/v = -e at the best correlation coefficient (grid +/-2%: 0.05% steps, then 0.005%
around the best; the plan named a 0.01% grid).
Station segments follow the plan's rule (same location code and sensor description, gaps up to 7 days).
D1 (after review): segments also break on a change of sensor dip (polarity) and on station data gaps of more than 90
days (GAP; a 7-day threshold, the first D1 choice, split records at routine outages and is kept as a sensitivity); days whose current stack has no energy in the coda window (dead channel) or correlates negatively with the
reference at zero stretch are rejected and counted (G2); the stretched trace is evaluated with a cubic spline instead
of linear interpolation on the 20 Hz lag grid. RULE=every_epoch makes every FDSN epoch its own segment (secondary 4).

Writes results/tables/dvv_daily.parquet (pair, date, dvv_pct, cc, ndays, seg) and results/tables/pairs.csv.
"""
import itertools
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import butter, sosfiltfilt

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"
FS, L = 20.0, 2000
TRAIN_END = pd.Timestamp("2020-12-31")


def segments(rule="plan", avail=None, gap_days=90):
    """Per station: list of (start, end) of continuous segments, from the FDSN channel epochs (location 10, Z).
    plan: consecutive epochs merge if sensor description and dip (polarity, D1) are unchanged and the gap is <= 7 days;
    every_epoch: each epoch is a segment. D1: segments are also split at station data gaps > 7 days (avail: station ->
    sorted array of dates with data)."""
    d = pd.read_csv(RUN / "results" / "tables" / "fdsn_channels.txt", sep="|")
    d.columns = [c.strip("# ").strip() for c in d.columns]
    d = d[(d.Location == 10) & d.Channel.isin(["EHZ", "HHZ"])].copy()
    d["start"] = pd.to_datetime(d.StartTime.str[:10])
    d["end"] = pd.to_datetime(d.EndTime.fillna("2026-12-31").astype(str).str[:10].replace("nan", "2026-12-31"))
    out = {}
    for st, g in d.sort_values("start").groupby("Station"):
        segs, cur = [], None
        for r in g.itertuples():
            same = cur and rule == "plan" and r.SensorDescription == cur[2] and r.Dip == cur[3] and (r.start - cur[1]).days <= 7
            if same:
                cur = (cur[0], max(cur[1], r.end), cur[2], cur[3])
            else:
                if cur:
                    segs.append(cur)
                cur = (r.start, r.end, r.SensorDescription, r.Dip)
        segs.append(cur)
        segs = [(a, b) for a, b, _, _ in segs]
        if avail is not None and st in avail:
            split = []
            days = avail[st]
            for a, b in segs:
                dd = days[(days >= a) & (days <= b)]
                if len(dd) == 0:
                    continue
                gaps = np.nonzero(np.diff(dd) > np.timedelta64(gap_days, "D"))[0]
                lo = a
                for gi in gaps:
                    split.append((lo, pd.Timestamp(dd[gi])))
                    lo = pd.Timestamp(dd[gi + 1])
                split.append((lo, b))
            segs = split
        out[st] = segs
    return out


def station_availability(dates, stations, N):
    """Station -> dates on which any pair including it has at least one window."""
    av = {}
    for s_i, st in enumerate(stations):
        cols = [p for p, (i, j) in enumerate(itertools.combinations(range(len(stations)), 2)) if s_i in (i, j)]
        av[st] = dates.to_numpy()[(N[:, cols] > 0).any(axis=1)]
    return av


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


def main(rule="plan", gap_days=90):
    sys.path.insert(0, str(RUN.parents[1] / "tools"))
    from coverage import Coverage
    from scipy.interpolate import CubicSpline
    suffix = ("" if rule == "plan" else f"_{rule}") + ("" if gap_days == 90 else f"_gap{gap_days}")
    cov = Coverage(f"dvv_days{suffix}", T / "coverage.json")
    dates, stations, C, N = load()
    segs = segments(rule, station_availability(dates, stations, N), gap_days)
    pd.DataFrame([{"station": st, "k": k, "start": a.date(), "end": b.date()} for st, sg in segs.items()
                  for k, (a, b) in enumerate(sg)]).to_csv(T / f"segments{suffix}.csv", index=False)
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
        snrs = []
        dead = have & (sym[:, win].std(axis=1) == 0)                       # D1: dead channel days leave the data
        for k in np.nonzero(dead)[0]:
            cov.attempt((f"{a}-{b}", int(k))); cov.drop((f"{a}-{b}", int(k)), "zero coda energy (dead channel)")
        have = have & ~dead
        for k in np.nonzero(have & (seg < 0))[0]:
            cov.attempt((f"{a}-{b}", int(k))); cov.drop((f"{a}-{b}", int(k)), "outside station segments")
        for sg in np.unique(seg[(seg >= 0) & have]):
            m = (seg == sg) & have
            mt = m & (dates <= TRAIN_END)
            if mt.sum() < 60:
                for k in np.nonzero(m)[0]:
                    cov.attempt((f"{a}-{b}", int(k))); cov.drop((f"{a}-{b}", int(k)), "segment with < 60 training days")
                continue
            ref = sym[mt].mean(axis=0)
            noise = ref[pos >= 95]
            snr = float(np.sqrt(np.mean(ref[win] ** 2)) / (np.sqrt(np.mean(noise ** 2)) + 1e-30))
            idx = np.nonzero(m)[0]
            # 10-day centred moving stack over valid days of this pair-segment
            cum = np.zeros((len(dates) + 1, sym.shape[1]))
            cum[1:] = np.cumsum(np.where(m[:, None], sym, 0.0), axis=0)
            cnt = np.concatenate([[0], np.cumsum(m)])
            dd = dates.to_numpy()
            r = ref[win]
            rz = (r - r.mean()) / (r.std() + 1e-20)
            for k in idx:
                unit = (f"{a}-{b}", int(k))
                cov.attempt(unit)
                lo = np.searchsorted(dd, dd[k] - np.timedelta64(5, "D"))
                hi = np.searchsorted(dd, dd[k] + np.timedelta64(5, "D"), side="right")
                n = cnt[hi] - cnt[lo]
                if n < 5:
                    cov.drop(unit, "fewer than 5 valid days in the stack")
                    continue
                cur = (cum[hi] - cum[lo]) / n
                if np.std(cur[win]) == 0 or np.std(sym[k, win]) == 0:      # D1: dead channel (zero coda energy)
                    cov.drop(unit, "zero coda energy (dead channel)")
                    continue
                c0 = cur[win]
                cc0 = float(((c0 - c0.mean()) / c0.std() * rz).mean())     # zero-stretch coherence of the stack
                if cc0 < 0:                                                 # D1: polarity mismatch with the reference
                    cov.drop(unit, "negative correlation with the reference at zero stretch")
                    continue
                spl = CubicSpline(pos, cur)                                 # D1: cubic instead of linear
                best = None
                for grid in (np.arange(-0.02, 0.02 + 1e-12, 0.0005), None):
                    if grid is None:
                        grid = np.arange(best - 0.0005, best + 0.0005 + 1e-12, 0.00005)
                    S = spl(np.outer(1 + grid, tw))
                    Sz = (S - S.mean(axis=1, keepdims=True)) / (S.std(axis=1, keepdims=True) + 1e-20)
                    ccs = list((Sz * rz).mean(axis=1))
                    kbest = int(np.argmax(ccs))
                    best, ccbest = grid[kbest], ccs[kbest]
                rows.append({"pair": f"{a}-{b}", "date": dates[k], "dvv_pct": -100 * best, "cc": ccbest, "cc0": cc0,
                             "ndays": int(n), "seg": int(sg)})
                cov.ok(unit)
            snrs.append(snr)
        prow.append({"pair": f"{a}-{b}", "dist_km": round(d_km, 2), "t1": round(t1, 2), "days": int(have.sum()), "note": "",
                     "coda_snr": round(float(np.median(snrs)), 3) if snrs else None})
        print(f"{a}-{b}", round(d_km, 1), "km", int(have.sum()), "days", flush=True)
    pd.DataFrame(rows).to_parquet(T / f"dvv_daily{suffix}.parquet", index=False)
    pd.DataFrame(prow).to_csv(T / f"pairs{suffix}.csv", index=False)
    cov.save()


if __name__ == "__main__":
    import os
    main(os.environ.get("RULE", "plan"), int(os.environ.get("GAP", "90")))
