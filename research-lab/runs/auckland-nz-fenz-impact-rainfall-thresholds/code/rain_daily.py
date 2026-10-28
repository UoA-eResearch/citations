"""Daily rain per gauge (plan section 2), from the HIRDS lead's series and rules (its maxima.py: reader, NEMS quality
rule, dense-logging outages, resolution of wet intervals).

Primary quality: 1xx and 3xx excluded, 2xx kept (the HIRDS lead's "S3" rule). Sensitivity Q: 2xx excluded as well.
For NZST day k: d_h = largest sliding h-hour total among windows ending in the day (5-minute bins); ante72 = total in
the 72 hours before the day; known_h = share of [day start - h, day end] that is known under the h-hour resolution.

  rain_daily.py -> data/rain_daily.parquet (file, day, d1, d6, d24, ante72, known1, known6, known24, d6_q, known6_q)
"""
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
HL = RUN.parent / "auckland-nz-hirds-out-of-sample-exceedance-audit"
sys.path.insert(0, str(HL / "code"))
import maxima as MX  # noqa: E402

D = RUN / "data"
T0, T1 = pd.Timestamp("2017-06-27"), pd.Timestamp("2025-07-01")
M0, M1 = int(T0.value // 60_000_000_000), int(T1.value // 60_000_000_000)
RES = {1: 5, 6: 15, 24: 60}


def series_arrays(t, v, q, variant):
    s, e, val, qq = t[:-1], t[1:], v[1:], q[1:]
    L = e - s
    ey = MX.wy_of(e)
    short = L <= 7 * 1440
    sil = pd.Series(np.where(short & (L > 60), L, 0.0)).groupby(ey).sum()
    span = pd.Series(np.where(short, L, 0.0)).groupby(ey).sum()
    dense_y = (sil / span.where(span > 0)).fillna(1.0) <= MX.DENSE_SILENCE
    dense = pd.Series(ey).map(dense_y).fillna(False).to_numpy()
    bad = MX.bad_quality(qq, variant) | ~np.isfinite(val) | MX.physical_bad(L, val)   # spikes and stuck sensors (D1)
    rain = np.where(bad, 0.0, val)
    return s, e, L, rain, bad, dense


def one(f):
    t, v, q = MX.load(f)
    if len(t) < 2 or t[-1] < M0 or t[0] > M1:
        return None
    edges = np.arange(M0, M1 + 1, MX.BIN, dtype=np.float64)
    days = pd.date_range(T0, T1 - pd.Timedelta(days=1), freq="D")
    dstart = np.array([(d.value // 60_000_000_000) for d in days], dtype=np.float64)
    out = {"file": f.stem, "day": days}
    for variant, sfx in (("S3", ""), ("primary", "_q")):
        s, e, L, rain, bad, dense = series_arrays(t, v, q, variant)
        x = np.r_[s[0], e]
        cs = np.interp(edges, x, np.r_[0.0, np.cumsum(rain)])         # cumulative rain at bin edges
        for h in ((1, 6, 24) if sfx == "" else (6,)):
            unres = (rain > 0) & (L > RES[h])
            dry_unknown = (rain == 0) & dense & (L > MX.OUTAGE_MIN)
            known = ~bad & ~unres & ~dry_unknown
            ck = np.interp(edges, x, np.r_[0.0, np.cumsum(np.where(known, L, 0.0))])
            n = h * 60 // MX.BIN
            win = cs[n:] - cs[:-n]                                     # window ending at edges[n:]
            wend = edges[n:]
            k = np.searchsorted(dstart, wend, side="left") - 1          # end in (day start, next day start]: midnight closes a day
            ok = (k >= 0) & (k < len(days))
            dmax = np.full(len(days), np.nan)
            np.fmax.at(dmax, k[ok], win[ok])
            a, b = dstart - h * 60, dstart + 1440
            kn = (np.interp(b, edges, ck) - np.interp(a, edges, ck)) / (b - a)
            out[f"d{h}{sfx}"] = dmax; out[f"known{h}{sfx}"] = np.round(kn, 4)
        if sfx == "":
            out["ante72"] = np.interp(dstart, edges, cs) - np.interp(dstart - 72 * 60, edges, cs)
    return pd.DataFrame(out)


def main():
    files = sorted((HL / "data" / "series").glob("*.npz"))
    with ProcessPoolExecutor(8) as ex:
        parts = [p for p in ex.map(one, files, chunksize=2) if p is not None]
    d = pd.concat(parts, ignore_index=True)
    d = d[(d.day >= "2017-07-01") & (d.day <= "2025-06-30")]
    d.to_parquet(D / "rain_daily.parquet")
    print(d.file.nunique(), "gauges;", len(d), "gauge-days;", round(float((d.known6 >= 0.9).mean()), 3), "share usable at 6 h (before resolution)")


if __name__ == "__main__":
    main()
