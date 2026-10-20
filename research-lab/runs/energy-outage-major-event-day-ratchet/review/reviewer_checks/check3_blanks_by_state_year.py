"""Reviewer check 3: per state and year, the rows with a blank customers_out (which build.py drops, i.e. treats as no
outage), the rows with customers_out == 0, the distinct counties, and the distinct counties that ever have a blank row.
Blank rows exist only in some years (none in 2015-2017 and 2023 per check 1); if they are concentrated in particular
states and years, those state-years' SAIDI are understated relative to the rest of the panel. Also samples, from the
check-1 subsets, the same county's neighbouring snapshots around blank rows to see whether blanks are isolated parse
failures or long runs. Writes check3_blanks_by_state_year.csv and check3_blank_runs.json."""
import json
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RUN = HERE.parents[1]
RAW = RUN / "data" / "raw"
CACHE = HERE / "cache"


def scan(y):
    f = RAW / f"eaglei_outages_{y}.csv"
    col = "sum" if "sum" in pd.read_csv(f, nrows=0).columns else "customers_out"
    acc = []
    for ch in pd.read_csv(f, usecols=["fips_code", "state", col], dtype={"fips_code": str, "state": str}, chunksize=5_000_000):
        c = pd.to_numeric(ch[col], errors="coerce")
        ch = ch.assign(blank=c.isna(), zero=(c == 0), cust=c.fillna(0))
        acc.append(ch.groupby("state").agg(rows=("blank", "size"), blank=("blank", "sum"), zero=("zero", "sum"), cust=("cust", "sum")))
        acc.append(ch.groupby("state").fips_code.nunique().rename("ncty_chunk").to_frame())
        acc.append(ch[ch.blank].groupby("state").fips_code.unique().rename("blank_cty").to_frame())
        acc.append(ch.groupby("state").fips_code.unique().rename("all_cty").to_frame())
    a = pd.concat([x for x in acc if "rows" in x.columns]).groupby(level=0).sum()
    bc = pd.concat([x for x in acc if "blank_cty" in x.columns]).groupby(level=0).blank_cty.apply(lambda s: len(set(np.concatenate(list(s)))) if len(s) else 0)
    ac = pd.concat([x for x in acc if "all_cty" in x.columns]).groupby(level=0).all_cty.apply(lambda s: len(set(np.concatenate(list(s)))))
    a["n_counties"] = ac; a["n_counties_with_blanks"] = bc.reindex(a.index).fillna(0).astype(int); a["year"] = y
    print(y, "done", flush=True)
    return a.reset_index()


if __name__ == "__main__":
    with Pool(3) as p:
        res = p.map(scan, range(2015, 2026))
    df = pd.concat(res); df["blank_share"] = df.blank / df.rows
    df.to_csv(HERE / "check3_blanks_by_state_year.csv", index=False)
    piv = df.pivot(index="state", columns="year", values="blank_share").round(3)
    with pd.option_context("display.width", 250, "display.max_rows", 100):
        print("blank share of rows by state and year"); print(piv.to_string())
        print("national:", df.groupby("year").agg(rows=("rows", "sum"), blank=("blank", "sum"), zero=("zero", "sum")).assign(share=lambda x: (x.blank / x.rows).round(4)).to_string())
    # blank runs from the subsets
    runs = {}
    for y in (2018, 2020, 2022):
        s = pd.read_parquet(CACHE / f"subset_{y}.parquet"); s["t"] = pd.to_datetime(s.t); s = s.sort_values(["fips", "t"])
        s["blank"] = s.cust.isna()
        s["run"] = (s.blank != s.groupby("fips").blank.shift()).cumsum()
        rl = s[s.blank].groupby("run").size()
        runs[y] = dict(n_blank_rows=int(s.blank.sum()), n_runs=int(len(rl)), run_len_median=float(rl.median()) if len(rl) else None,
                       run_len_p90=float(rl.quantile(0.9)) if len(rl) else None, run_len_max=int(rl.max()) if len(rl) else None,
                       blank_share_by_state=s.groupby("state").blank.mean().round(3).to_dict())
        # value just before and after a blank run, for the same county
        prev = s.groupby("fips").cust.shift(); nxt = s.groupby("fips").cust.shift(-1)
        starts = s.blank & ~prev.isna(); ends = s.blank & ~nxt.isna()
        runs[y]["median_cust_before_blank_run"] = float(prev[starts].median()) if starts.any() else None
        runs[y]["median_cust_after_blank_run"] = float(nxt[ends].median()) if ends.any() else None
        runs[y]["median_cust_nonblank_rows"] = float(s.cust.dropna().median())
    json.dump(runs, open(HERE / "check3_blank_runs.json", "w"), indent=1, default=float)
    print(json.dumps(runs, indent=1, default=float))
