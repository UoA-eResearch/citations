#!/usr/bin/env python
"""Per-station warm-season extremes from GHCN-Daily TMAX (plan.md sec 4).

For each downloaded station file: TMAX values with an empty quality flag, in degC. Warm season = May-Sep (station
latitude >= 0) or Nov-Mar (latitude < 0; the season is assigned to the year in which it ends). A season is valid when
>= 90% of its days have TMAX. For valid seasons:
  TXx  = maximum daily TMAX;
  TX7x = maximum 7-day running mean of TMAX over windows whose 7 days are all present (NaN if none).
Years 1951-2025 only.

Output: data/processed/extremes.parquet (station, year, n_days, n_expected, valid, txx, tx7x) and
        data/processed/stations_meta.parquet (station, lat, lon, elev, name, hcn_crn, gsn)
"""
from __future__ import annotations

import gzip
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
RAW, PROC = RUN / "data" / "raw", RUN / "data" / "processed"
Y0, Y1 = 1951, 2025


def read_meta() -> pd.DataFrame:
    rows = []
    for line in open(RAW / "ghcnd-stations.txt"):
        rows.append(dict(station=line[0:11], lat=float(line[12:20]), lon=float(line[21:30]), elev=float(line[31:37]),
                         name=line[41:71].strip(), gsn=line[72:75].strip() == "GSN", hcn_crn=line[76:79].strip()))
    return pd.DataFrame(rows)


def season_days(year: int, south: bool) -> pd.DatetimeIndex:
    if south:
        return pd.date_range(f"{year - 1}-11-01", f"{year}-03-31", freq="D")
    return pd.date_range(f"{year}-05-01", f"{year}-09-30", freq="D")


def process(args):
    sid, lat = args
    path = RAW / "by_station" / f"{sid}.csv.gz"
    try:
        with gzip.open(path, "rt") as fh:
            d = pd.read_csv(fh, header=None, usecols=[1, 2, 3, 5], names=["date", "el", "val", "q"],
                            dtype={"date": str, "el": str, "val": float, "q": str}, low_memory=False)
    except Exception as e:                                   # unreadable / truncated file
        return [dict(station=sid, year=-1, error=str(e)[:200])]
    d = d[(d.el == "TMAX") & d.q.isna()]
    if d.empty:
        return []
    s = pd.Series(d.val.values / 10.0, index=pd.to_datetime(d.date, format="%Y%m%d", errors="coerce"))
    s = s[~s.index.isna()]
    s = s[~s.index.duplicated()].sort_index()
    south = lat < 0
    out = []
    for y in range(Y0, Y1 + 1):
        idx = season_days(y, south)
        x = s.reindex(idx)
        n, ne = int(x.notna().sum()), len(idx)
        valid = n >= 0.9 * ne
        txx = float(x.max()) if valid else np.nan
        r7 = x.rolling(7, min_periods=7).mean()
        tx7x = float(r7.max()) if valid and r7.notna().any() else np.nan
        out.append(dict(station=sid, year=y, n_days=n, n_expected=ne, valid=valid, txx=txx, tx7x=tx7x))
    return out


def main():
    PROC.mkdir(parents=True, exist_ok=True)
    meta = read_meta()
    meta.to_parquet(PROC / "stations_meta.parquet", index=False)
    have = {p.name[:11] for p in (RAW / "by_station").glob("*.csv.gz")}
    todo = meta[meta.station.isin(have)][["station", "lat"]].values.tolist()
    print(f"{len(todo)} station files", flush=True)
    rows = []
    with Pool(24) as pool:
        for k, r in enumerate(pool.imap_unordered(process, todo, chunksize=8)):
            rows += r
            if k % 500 == 0:
                print(f"{k} processed", flush=True)
    df = pd.DataFrame(rows)
    err = df[df.year == -1] if "error" in df else df.iloc[:0]
    df = df[df.year > 0].drop(columns=[c for c in ("error",) if c in df])
    df.to_parquet(PROC / "extremes.parquet", index=False)
    print(f"stations {df.station.nunique()}, station-years {len(df):,}, valid {int(df.valid.sum()):,}; unreadable files {len(err)}")


if __name__ == "__main__":
    sys.exit(main())
