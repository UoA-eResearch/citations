"""Reviewer replication of limb 1, plus a placebo sweep.

Pass 1 over data/samples/*.parquet (per part, 5 columns) builds day x class counts under the study's own care filter,
and counts the samples whose BioSample Owner is empty (one cluster in the study's cluster bootstrap).

Then:
 1. reproduces the preregistered point estimates at 2023-06-01 (no bootstrap);
 2. runs the SAME specification at every month-start cutoff from 2020-06-01 to 2025-01-01 - the design's own
    falsification distribution. If the jump at the real cutoff is not unusual in that distribution, the design
    cannot attribute the jump to the rule.
Writes review/reviewer_checks/rd_replicate.json.
"""
import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RUN / "code"))
import analysis_rd as A  # noqa: E402

OUT = Path(__file__).resolve().parent
CLASSES = A.CLASSES


def day_counts():
    tot = None
    empty_owner = 0
    n_window = 0
    for f in sorted(glob.glob(str(RUN / "data" / "samples" / "*.parquet"))):
        d = pd.read_parquet(f, columns=["submission_date", "owner", "country_class", "organism", "host"])
        d = d[~A.human_host_metagenome(d)]
        d["date"] = pd.to_datetime(d.submission_date, errors="coerce")
        d = d.dropna(subset=["date"])
        w = d[(d.date >= "2021-06-01") & (d.date < "2025-06-01")]
        n_window += len(w)
        empty_owner += int((w.owner.fillna("").str.strip() == "").sum())
        g = pd.crosstab(d.date, d.country_class)
        tot = g if tot is None else tot.add(g, fill_value=0)
        del d, w, g
    for c in CLASSES:
        if c not in tot:
            tot[c] = 0.0
    tot = tot[CLASSES].fillna(0.0)
    tot["n"] = tot.sum(axis=1)
    return tot.sort_index(), empty_owner, n_window


def jump(days, n_day, k_day, cut, bw_days, donut_days):
    t = (days - cut).days.to_numpy().astype(float)
    keep = (np.abs(t) <= bw_days) & (np.abs(t) > donut_days) & (n_day > 0)
    if keep.sum() < 10:
        return np.nan
    tt, y = t[keep], k_day[keep] / n_day[keep]
    w = n_day[keep] * (1 - np.abs(t[keep]) / bw_days)
    post = (tt >= 0).astype(float)
    X = np.column_stack([np.ones_like(tt), post, tt, post * tt])
    sw = np.sqrt(w)
    beta, *_ = np.linalg.lstsq(X * sw[:, None], y * sw, rcond=None)
    return float(beta[1])


def at(cut, tab, bw_months=24, donut_months=1):
    cut = pd.Timestamp(cut)
    lo, hi = cut - pd.DateOffset(months=bw_months), cut + pd.DateOffset(months=bw_months)
    t = tab[(tab.index >= lo) & (tab.index < hi)]
    days = pd.DatetimeIndex(t.index)
    bw = (hi - cut).days
    dn = (cut + pd.DateOffset(months=donut_months) - cut).days if donut_months else 0
    n = t.n.to_numpy(float)
    return {c: round(100 * jump(days, n, t[c].to_numpy(float), cut, bw, dn), 3) for c in CLASSES}


tab, empty_owner, n_window = day_counts()
res = {"window_samples": int(n_window), "samples_with_empty_owner": int(empty_owner),
       "empty_owner_share": round(empty_owner / n_window, 5),
       "replicated_2023_06_01": at("2023-06-01", tab),
       "replicated_placebo_2021_06_01": at("2021-06-01", tab),
       "replicated_placebo_2022_06_01": at("2022-06-01", tab),
       "placebo_sweep": {}}
for cut in pd.date_range("2020-06-01", "2025-01-01", freq="MS"):
    res["placebo_sweep"][str(cut.date())] = at(cut, tab)
for c in CLASSES:
    v = np.array([r[c] for k, r in res["placebo_sweep"].items() if k != "2023-06-01"], dtype=float)
    real = res["replicated_2023_06_01"][c]
    res[f"sweep_{c}"] = {"real_cutoff_jump_pp": real, "n_placebo_dates": int(len(v)),
                         "placebo_mean": round(float(np.nanmean(v)), 3),
                         "placebo_sd": round(float(np.nanstd(v)), 3),
                         "placebo_abs_p90": round(float(np.nanpercentile(np.abs(v), 90)), 3),
                         "placebo_min": round(float(np.nanmin(v)), 3), "placebo_max": round(float(np.nanmax(v)), 3),
                         "placebo_dates_with_abs_jump_at_least_real": int(np.nansum(np.abs(v) >= abs(real))),
                         "share_of_placebo_dates_at_least_as_large": round(float(np.nanmean(np.abs(v) >= abs(real))), 3)}
(OUT / "rd_replicate.json").write_text(json.dumps(res, indent=1))
print(json.dumps({k: v for k, v in res.items() if k != "placebo_sweep"}, indent=1))
print("\nplacebo sweep (usable, placeholder, absent) by cutoff:")
for k, r in res["placebo_sweep"].items():
    print(f"  {k}  usable {r['usable']:8.2f}  placeholder {r['placeholder']:8.2f}  absent {r['absent']:8.2f}")
