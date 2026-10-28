"""Annual maxima (plan section 2, read by deviations.md D2) for each fetched gauge, water year and duration.

Hilltop incremental series: a record's value is the rain in (previous record, this record]. Rain is spread evenly
within its interval (the councils' own convention) and summed into 5-minute bins; d-hour totals are sliding sums of
bins, assigned to the water year in which the window ends.

  maxima.py -> data/maxima.parquet: server, file, wy, d (hours), variant, max_point, max_upper, known_frac, dense,
               t_max (end of the maximum window, minutes since 1970), max_point_no_janfeb2023 (2022/23 only),
               wet_median_min (median interval of the year's wet records: its native resolution; D3)
               (variants: primary, S2, S3, S4; S1 is the primary's max_upper)
"""
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
S = RUN / "data" / "series"
BIN = 5                                                    # minutes
DUR = {1: 5, 6: 15, 24: 60}                                # duration (h) -> longest resolved wet interval (min), D2 rule 2
DENSE_SILENCE, OUTAGE_MIN, S2_DAYS = 0.02, 60, 14          # D2 rule 3 and S2
JF23 = (int(pd.Timestamp("2023-01-01").value // 60_000_000_000), int(pd.Timestamp("2023-03-01").value // 60_000_000_000))


def wy_of(minutes):
    ts = pd.to_datetime(minutes, unit="m")
    return np.where(ts.month >= 7, ts.year, ts.year - 1)


def wy_start(y):
    return int(pd.Timestamp(f"{y}-07-01").value // 60_000_000_000)


def bad_quality(q, variant):
    h = np.where(q >= 0, q // 100, -1)
    bad = np.isin(h, [1, 3]) if variant == "S3" else np.isin(h, [1, 2, 3])
    if variant == "S4":
        bad |= (q == 0) | (h == 4)
    return bad


def load(f):
    """The main series, with water years 1995/96-2004/05 from data/series_early/ spliced on where fetched (D3)."""
    parts = [np.load(g) for g in (S.parent / "series_early" / f.name, f) if g.exists()]
    t = np.concatenate([z["t"] for z in parts]).astype(np.int64)
    v = np.concatenate([z["v"] for z in parts]).astype(np.float64)
    q = np.concatenate([z["q"] for z in parts]).astype(np.int64)
    o = np.argsort(t, kind="stable")
    t, v, q = t[o], v[o], q[o]
    keep = np.r_[True, t[1:] != t[:-1]]
    return t[keep], v[keep], q[keep]


def one(f):
    t, v, q = load(f)
    server = f.stem.split("__")[0]
    if len(t) < 2:
        return []
    s, e, val, qq = t[:-1], t[1:], v[1:], q[1:]                   # interval (s, e] carries val
    L = (e - s).astype(np.float64)
    ey = wy_of(e)
    # dense gauge-years (D2 rule 3): share of time in 1-hour to 7-day silences
    short = L <= 7 * 1440
    sil = pd.Series(np.where(short & (L > 60), L, 0.0)).groupby(ey).sum()
    span = pd.Series(np.where(short, L, 0.0)).groupby(ey).sum()
    dense_y = (sil / span.where(span > 0)).fillna(1.0) <= DENSE_SILENCE
    dense = pd.Series(ey).map(dense_y).fillna(False).to_numpy()
    years = np.arange(max(1995, int(ey.min())), min(2025, int(ey.max())) + 1)   # 2025/26 is the last full water year
    if len(years) == 0:
        return []
    lo, hi = wy_start(years[0]), wy_start(years[-1] + 1)
    edges = np.arange(lo, hi + 1, BIN)                            # 5-minute bin edges
    out = []
    for variant in ("primary", "S2", "S3", "S4"):
        bad = bad_quality(qq, "primary" if variant == "S2" else variant)
        rain = np.where(bad, 0.0, val)
        Crain = np.interp(edges, np.r_[s[0], e], np.r_[0.0, np.cumsum(rain)])
        point_bins = np.diff(Crain)
        for d, res in DUR.items():
            wet = rain > 0
            unres = wet & (L > res)
            rs = pd.Series(L[wet]).groupby(ey[wet]).median()
            dry_unknown = (~wet) & ((dense & (L > OUTAGE_MIN)) | ((variant == "S2") & (L > S2_DAYS * 1440)))
            known = ~bad & ~unres & ~dry_unknown
            Ck = np.interp(edges, np.r_[s[0], e], np.r_[0.0, np.cumsum(np.where(known, L, 0.0))])
            n = d * 60 // BIN
            cs = np.r_[0.0, np.cumsum(point_bins)]
            win = cs[n:] - cs[:-n]                                    # window ending at bin edge index n..; sum of n bins
            res_rain = np.where(unres, 0.0, rain)
            Cres = np.interp(edges, np.r_[s[0], e], np.r_[0.0, np.cumsum(res_rain)])
            cr = np.r_[0.0, np.cumsum(np.diff(Cres))]
            win_res = cr[n:] - cr[:-n]
            # full amount of every unresolved interval overlapping each window (difference array over window ends)
            over = np.zeros(len(edges) + n + 1)
            if unres.any():
                a = np.clip(((s[unres] - lo) // BIN).astype(np.int64) + 1, 0, len(over) - 1)
                b = np.clip(((e[unres] - lo + BIN - 1) // BIN).astype(np.int64) + n, 0, len(over) - 1)
                np.add.at(over, a, rain[unres]); np.add.at(over, b, -rain[unres])
            over = np.cumsum(over)[n:len(edges)]
            upper = win_res + over[: len(win_res)]
            wend = edges[n:]
            wy_w = wy_of(wend)
            for y in years:
                m = wy_w == y
                if not m.any():
                    continue
                kn = (np.interp(wy_start(y + 1), edges, Ck) - np.interp(wy_start(y), edges, Ck)) / (wy_start(y + 1) - wy_start(y))
                i = np.flatnonzero(m)[np.argmax(win[m])]
                nojf = float(win[m & ((wend < JF23[0]) | (wend >= JF23[1]))].max()) if y == 2022 else np.nan
                out.append((server, f.stem, int(y), d, variant, float(win[i]), float(upper[m].max()), round(float(kn), 4),
                            bool(dense_y.get(y, False)), int(wend[i]), nojf, float(rs.get(y, np.nan))))
    return out


def main(files=None):
    fs = [S / f"{x}.npz" for x in files] if files else sorted(S.glob("*.npz"))
    with ProcessPoolExecutor(8) as ex:
        rows = [r for rs in ex.map(one, fs, chunksize=2) for r in rs]
    d = pd.DataFrame(rows, columns=["server", "file", "wy", "d", "variant", "max_point", "max_upper", "known_frac", "dense",
                                    "t_max", "max_point_no_janfeb2023", "wet_median_min"])
    if not files:
        d.to_parquet(RUN / "data" / "maxima.parquet")
    return d


if __name__ == "__main__":
    print(main(sys.argv[1:] or None).groupby(["variant", "d"]).size())
