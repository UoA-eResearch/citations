"""G4 (plan section 5): 30 randomly sampled qualifying 6-hour annual maxima, recomputed independently from the raw
records and compared with maxima.py.

Independent method: the cumulative rain curve is piecewise linear between records, so the largest d-hour total is
reached with a window edge on a record time. Evaluate C(end) - C(end - d) for every end in {t_i, t_i + d} inside the
water year, directly from the records (no 5-minute grid). maxima.py's grid maximum must not exceed it and should be
within a few per cent of it.

Raw check (added in D5): 10 random gauge-years are refetched from the servers and their record counts and totals
compared with the stored series, which catches reader bugs that recomputing from stored data cannot.

  g4_check.py -> results/tables/g4_check.csv, results/tables/g4_raw_check.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
import maxima as MX  # noqa: E402  (load() and bad_quality() only: the record reader and the quality rule)

D, T, d = RUN / "data", RUN / "results" / "tables", 6


def exact_max(f, y):
    t, v, q = MX.load(MX.S / f"{f}.npz")
    rain = np.where(MX.bad_quality(q, "primary"), 0.0, v)
    C = np.r_[0.0, np.cumsum(rain[1:])]                    # cumulative at record times; record 0 opens the series
    a, b = MX.wy_start(y), MX.wy_start(y + 1)
    ends = np.unique(np.r_[t, t + d * 60])
    ends = ends[(ends > a) & (ends <= b)]
    win = np.interp(ends, t, C) - np.interp(ends - d * 60, t, C)
    return float(win.max()) if len(win) else np.nan


def raw_check(m, k=10):
    import re as _re
    import urllib.parse
    import fetch as FH
    import fetch_auckland as FA
    inv = FH.candidates().assign(stem=lambda d: d.server + "__" + d.site.map(lambda x: _re.sub(r"[^A-Za-z0-9._-]+", "_", x)))
    s = m.drop_duplicates(["file", "wy"]).sample(k, random_state=7)
    op, rows = None, []
    for r in s.itertuples():
        a, b = f"{r.wy}-07-01", f"{r.wy + 1}-07-01"
        if r.file.startswith("Auckland__"):
            op = op or FA.session()
            ai = pd.read_parquet(D / "inventory_auckland.parquet")
            ds = ai[ai.LocationIdentifier == r.file.split("__")[1].split("_")[0]].DatasetIdentifier.iloc[0]
            txt = FA.export(op, ds, a, b)
            recs = [x.split(",") for x in txt.splitlines() if _re.match(r"\d{4}-\d\d-\d\d \d\d:\d\d", x)]
            vals = [float(x[1]) for x in recs if len(x) > 1 and x[1] not in ("", "NaN")]
            times = [x[0] for x in recs]
        else:
            row = inv[inv.stem == r.file].iloc[0]
            x = FH.get(f"{FH.SERVERS[row.server]}?Service=Hilltop&Request=GetData&Site={urllib.parse.quote(row.site)}"
                       f"&Measurement={urllib.parse.quote(row.measurement)}&From={a}&To={b}")
            recs = FH.REC.findall(x)
            vals = [float(v) for _, v, _ in recs if v not in ("",)]
            times = [t for t, _, _ in recs]
        t_raw = pd.to_datetime(pd.Series(times)).to_numpy("datetime64[s]").astype(np.int64) / 60.0
        t, v, _ = MX.load(MX.S / f"{r.file}.npz")
        lo, hi = MX.wy_start(r.wy), MX.wy_start(r.wy + 1)
        sel = (t >= lo) & (t <= hi)
        rows.append((r.file, r.wy, len(t_raw), int(sel.sum()), round(float(np.nansum(vals)), 2), round(float(np.nansum(v[sel])), 2)))
    out = pd.DataFrame(rows, columns=["file", "wy", "raw_records", "stored_records", "raw_total_mm", "stored_total_mm"])
    out.to_csv(T / "g4_raw_check.csv", index=False)
    print(out.to_string(index=False))
    print("records match:", bool((out.raw_records == out.stored_records).all()),
          "| totals match:", bool(np.allclose(out.raw_total_mm, out.stored_total_mm, atol=0.05)))


def main():
    M = pd.read_parquet(D / "maxima.parquet")
    m = M[(M.d == d) & (M.variant == "primary") & (M.known_frac >= 0.9) & (M.wet_median_min <= 15)]
    s = m.sample(30, random_state=20261028)
    s = s.assign(exact=[exact_max(r.file, r.wy) for r in s.itertuples()])
    s["grid_over_exact"] = s.max_point / s.exact
    s[["file", "wy", "max_point", "exact", "grid_over_exact"]].to_csv(T / "g4_check.csv", index=False)
    print(s[["file", "wy", "max_point", "exact", "grid_over_exact"]].round(3).to_string(index=False))
    print("grid never above exact:", bool((s.max_point <= s.exact + 1e-6).all()),
          "| min ratio", round(float(s.grid_over_exact.min()), 4), "| median", round(float(s.grid_over_exact.median()), 4))
    raw_check(m)


if __name__ == "__main__":
    main()
