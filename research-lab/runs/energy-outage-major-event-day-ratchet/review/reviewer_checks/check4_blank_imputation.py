"""Reviewer check 4: materiality of the blank customers_out rows that build.py drops (treats as no outage).
For the eight cached states: (a) annual customer-minutes with blanks dropped vs with blanks imputed by per-county linear
interpolation in time between the neighbouring non-blank snapshots (upper bound on what the blanks could hide if they
are missing counts of ongoing outages); (b) whether blanks behave like the explicit zero rows of 2022-2024: the
distribution of the non-blank value just before/after a blank run (2018, 2020, 2025) vs just before/after a zero run
(2022-2024). Writes check4_blank_imputation.json."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
CACHE = HERE / "cache"
out = dict(annual_ratio_imputed_over_dropped={}, blank_share_customer_minutes_if_interpolated={}, neighbours={})
ABBR = {"District of Columbia": "DC", "Florida": "FL", "Vermont": "VT", "Iowa": "IA", "Illinois": "IL", "Louisiana": "LA", "Nevada": "NV", "Michigan": "MI"}
for y in range(2015, 2026):
    s = pd.read_parquet(CACHE / f"subset_{y}.parquet"); s["t"] = pd.to_datetime(s.t); s = s.sort_values(["fips", "t"])
    nb = s.cust.isna().sum()
    if nb == 0 and y not in (2022, 2023, 2024):
        continue
    if nb > 0:
        # interpolate per county on the time axis
        imp = s.set_index("t").groupby("fips").cust.transform(lambda x: x.interpolate(method="time", limit_area="inside")).values
        imp = np.where(np.isnan(imp), 0.0, imp)
        s["imp"] = imp
        a = s.groupby("state").agg(dropped=("cust", lambda x: float(np.nansum(x))), imputed=("imp", "sum"))
        out["annual_ratio_imputed_over_dropped"][y] = (a.imputed / a.dropped).round(4).rename(index=ABBR).to_dict()
        out["blank_share_customer_minutes_if_interpolated"][y] = ((a.imputed - a.dropped) / a.imputed).round(4).rename(index=ABBR).to_dict()
    # neighbours of blank runs vs zero runs
    for kind, mask in (("blank", s.cust.isna()), ("zero", s.cust == 0)):
        if mask.sum() == 0:
            continue
        prev = s.groupby("fips").cust.shift(); nxt = s.groupby("fips").cust.shift(-1)
        valid_prev = mask & prev.notna() & (prev != 0); valid_next = mask & nxt.notna() & (nxt != 0)
        nbr = pd.concat([prev[valid_prev], nxt[valid_next]])
        out["neighbours"][f"{y}_{kind}"] = dict(n_rows=int(mask.sum()), n_with_nonzero_neighbour=int(len(nbr)),
                                                 neighbour_median=float(nbr.median()) if len(nbr) else None,
                                                 neighbour_p90=float(nbr.quantile(0.9)) if len(nbr) else None,
                                                 neighbour_mean=float(nbr.mean()) if len(nbr) else None,
                                                 nonblank_nonzero_median=float(s.cust[(s.cust > 0)].median()),
                                                 nonblank_nonzero_mean=float(s.cust[(s.cust > 0)].mean()))
    print(y, "done", flush=True)
json.dump(out, open(HERE / "check4_blank_imputation.json", "w"), indent=1, default=float)
print(json.dumps(out, indent=1, default=float))
