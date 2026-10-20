"""Reviewer check 1: scan every EAGLE-I year file once and record, per year:
  rows; rows with blank customers_out; rows with customers_out == 0; sum of customers_out (magnitude check incl. 2023 'sum');
  min/max run_start_time; distinct timestamps vs the 15-minute grid (off-grid timestamps, missing slots, gap histogram);
  exact duplicates of (fips_code, run_start_time) and within-slot duplicates of (fips_code, 15-minute slot), with the
  customers_out they would double count; rows whose fips prefix disagrees with the 'state' column.
Also caches, for a few states, the compact rows (fips, time, customers_out) for the independent re-derivation (check 2).
Usage: venv/bin/python -I check1_raw_scan.py  (4 processes, one year each; ~1 GB per process)."""
import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RUN = HERE.parents[1]
RAW = RUN / "data" / "raw"
CACHE = HERE / "cache"; CACHE.mkdir(exist_ok=True)
SUBSET = {"District of Columbia", "Louisiana", "Iowa", "Florida", "Vermont", "Nevada", "Illinois", "Michigan"}
FIPS = {1: "Alabama", 2: "Alaska", 4: "Arizona", 5: "Arkansas", 6: "California", 8: "Colorado", 9: "Connecticut", 10: "Delaware",
        11: "District of Columbia", 12: "Florida", 13: "Georgia", 15: "Hawaii", 16: "Idaho", 17: "Illinois", 18: "Indiana",
        19: "Iowa", 20: "Kansas", 21: "Kentucky", 22: "Louisiana", 23: "Maine", 24: "Maryland", 25: "Massachusetts",
        26: "Michigan", 27: "Minnesota", 28: "Mississippi", 29: "Missouri", 30: "Montana", 31: "Nebraska", 32: "Nevada",
        33: "New Hampshire", 34: "New Jersey", 35: "New Mexico", 36: "New York", 37: "North Carolina", 38: "North Dakota",
        39: "Ohio", 40: "Oklahoma", 41: "Oregon", 42: "Pennsylvania", 44: "Rhode Island", 45: "South Carolina",
        46: "South Dakota", 47: "Tennessee", 48: "Texas", 49: "Utah", 50: "Vermont", 51: "Virginia", 53: "Washington",
        54: "West Virginia", 55: "Wisconsin", 56: "Wyoming"}
SLOT_NS = 15 * 60 * 10**9


def scan(y):
    f = RAW / f"eaglei_outages_{y}.csv"
    cols = pd.read_csv(f, nrows=0).columns.tolist()
    col = "sum" if "sum" in cols else "customers_out"
    out = dict(year=y, columns=cols, cust_col=col, rows=0, rows_nan_cust=0, rows_zero_cust=0, rows_bad_time=0,
               rows_bad_fips=0, rows_state_mismatch=0, sum_cust=0.0)
    T, F, C = [], [], []
    sub = []
    for ch in pd.read_csv(f, usecols=["fips_code", "state", col, "run_start_time"], dtype={"fips_code": str, "state": str},
                          chunksize=5_000_000):
        out["rows"] += len(ch)
        c = pd.to_numeric(ch[col], errors="coerce")
        out["rows_nan_cust"] += int(c.isna().sum())
        out["rows_zero_cust"] += int((c == 0).sum())
        out["sum_cust"] += float(c.fillna(0).sum())
        t = pd.to_datetime(ch.run_start_time, format="%Y-%m-%d %H:%M:%S", errors="coerce")
        out["rows_bad_time"] += int(t.isna().sum())
        fi = pd.to_numeric(ch.fips_code, errors="coerce")
        out["rows_bad_fips"] += int(fi.isna().sum())
        st_from_fips = (fi // 1000).map(FIPS)
        out["rows_state_mismatch"] += int(((st_from_fips != ch.state) & st_from_fips.notna()).sum())
        keep = t.notna() & fi.notna()
        T.append(t[keep].values.astype("datetime64[ns]").astype(np.int64)); F.append(fi[keep].values.astype(np.int32))
        C.append(c[keep].values.astype(np.float64))
        m = keep & ch.state.isin(SUBSET)
        if m.any():
            sub.append(pd.DataFrame(dict(state=ch.state[m].values, fips=fi[m].values.astype(np.int32),
                                         t=t[m].values, cust=c[m].values)))
    T = np.concatenate(T); F = np.concatenate(F); C = np.concatenate(C)
    out["n_distinct_fips"] = int(len(np.unique(F)))
    out["t_min"] = str(pd.Timestamp(T.min())); out["t_max"] = str(pd.Timestamp(T.max()))
    ts = np.unique(T)
    out["n_distinct_timestamps"] = int(len(ts))
    ndays = (pd.Timestamp(f"{y}-12-31") - pd.Timestamp(f"{y}-01-01")).days + 1
    out["expected_slots_full_year"] = ndays * 96
    out["n_timestamps_off_15min_grid"] = int((ts % SLOT_NS != 0).sum())
    out["n_distinct_slots"] = int(len(np.unique(T // SLOT_NS)))
    gaps = np.diff(ts) / 60e9  # minutes between consecutive distinct timestamps
    hist = {}
    for lo, hi, k in ((0, 15, "<15"), (15, 15, "=15"), (15.0001, 30, "15-30"), (30, 60, "30-60"), (60, 180, "60-180"),
                      (180, 1440, "180-1440"), (1440, 1e12, ">1440")):
        if k == "=15":
            hist[k] = int((gaps == 15).sum())
        elif k == "<15":
            hist[k] = int((gaps < 15).sum())
        else:
            hist[k] = int(((gaps > lo) & (gaps <= hi)).sum())
    out["gap_minutes_between_distinct_timestamps"] = hist
    out["minutes_missing_vs_15min_grid"] = float(np.clip(gaps - 15, 0, None).sum())
    out["largest_gap_minutes"] = float(gaps.max())
    big = np.argsort(gaps)[-5:][::-1]
    out["largest_gaps"] = [dict(start=str(pd.Timestamp(ts[i])), minutes=float(gaps[i])) for i in big]
    # duplicates
    key_exact = F.astype(np.int64) * 10**13 + (T // 10**9)
    _, inv, cnt = np.unique(key_exact, return_inverse=True, return_counts=True)
    dup_exact = cnt[inv] > 1
    out["dup_exact_rows"] = int(dup_exact.sum()); out["dup_exact_cust_sum"] = float(np.nansum(C[dup_exact]))
    key_slot = F.astype(np.int64) * 10**9 + (T // SLOT_NS)
    _, inv, cnt = np.unique(key_slot, return_inverse=True, return_counts=True)
    dup_slot = cnt[inv] > 1
    out["dup_slot_rows"] = int(dup_slot.sum()); out["dup_slot_cust_sum"] = float(np.nansum(C[dup_slot]))
    out["dup_slot_keys"] = int((cnt > 1).sum())
    # per-slot row counts: how many counties per snapshot (level of reporting)
    slots, scount = np.unique(T // SLOT_NS, return_counts=True)
    out["rows_per_slot_median"] = float(np.median(scount)); out["rows_per_slot_p05"] = float(np.percentile(scount, 5))
    # slots per local-ish calendar day (UTC) to see partial days
    days_utc, dcount = np.unique((T // SLOT_NS) // 96, return_counts=True)
    out["utc_days_present"] = int(len(days_utc)); out["utc_days_in_year"] = ndays
    out["hours_coverage_first_utc_day"] = float(len(np.unique((T[(T // SLOT_NS) // 96 == days_utc[0]]) // SLOT_NS)) / 4)
    out["hours_coverage_last_utc_day"] = float(len(np.unique((T[(T // SLOT_NS) // 96 == days_utc[-1]]) // SLOT_NS)) / 4)
    if sub:
        pd.concat(sub).to_parquet(CACHE / f"subset_{y}.parquet", index=False)
    (CACHE / f"scan_{y}.json").write_text(json.dumps(out, indent=1))
    print(y, "done", out["rows"], "rows", flush=True)
    return out


if __name__ == "__main__":
    years = [int(a) for a in sys.argv[1:]] or list(range(2015, 2026))
    with Pool(4) as p:
        res = p.map(scan, years)
    (HERE / "check1_raw_scan.json").write_text(json.dumps(res, indent=1))
    df = pd.DataFrame(res).set_index("year")
    cols = ["rows", "rows_nan_cust", "rows_zero_cust", "sum_cust", "t_min", "t_max", "n_distinct_timestamps",
            "expected_slots_full_year", "n_timestamps_off_15min_grid", "n_distinct_slots", "minutes_missing_vs_15min_grid",
            "largest_gap_minutes", "dup_exact_rows", "dup_slot_rows", "dup_slot_cust_sum", "rows_state_mismatch",
            "n_distinct_fips", "hours_coverage_first_utc_day", "hours_coverage_last_utc_day"]
    with pd.option_context("display.width", 250, "display.max_columns", 50):
        print(df[cols].to_string())
        print(pd.DataFrame({y: r["gap_minutes_between_distinct_timestamps"] for y, r in zip(df.index, res)}).to_string())
