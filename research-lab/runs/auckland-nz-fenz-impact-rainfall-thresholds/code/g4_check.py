"""G4 (plan section 5).

  1. Geocoding audit: for every panel suburb, does the council of its most-used gauge match the FENZ regional council?
     Neighbouring councils (a gauge just across a boundary) are listed separately from distant mismatches.
  2. Window audit: 30 random suburb-days' d6 recomputed exactly from raw records (window edges on record times, as in
     the HIRDS lead's G4) and compared with the panel.

  g4_check.py -> results/tables/g4_geocode.json, results/tables/g4_window.csv
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
HL = RUN.parent / "auckland-nz-hirds-out-of-sample-exceedance-audit"
sys.path.insert(0, str(HL / "code"))
import maxima as MX  # noqa: E402

D, T = RUN / "data", RUN / "results" / "tables"
COUNCIL = {"Northland": "Northland Region", "HawkesBay": "Hawke's Bay Region", "Wellington": "Wellington Region",
           "Marlborough": "Marlborough Region", "Tasman": "Tasman Region", "Taranaki": "Taranaki Region",
           "WestCoast": "West Coast Region", "Auckland": "Auckland Region"}
NEIGHBOURS = {"Tasman Region": {"Nelson Region", "West Coast Region", "Marlborough Region", "Canterbury Region"},
              "Auckland Region": {"Waikato Region", "Northland Region"}, "Northland Region": {"Auckland Region"},
              "Wellington Region": {"Manawatu-Wanganui Region"}, "Hawke's Bay Region": {"Gisborne Region", "Manawatu-Wanganui Region", "Bay of Plenty Region", "Waikato Region"},
              "Taranaki Region": {"Manawatu-Wanganui Region", "Waikato Region"}, "Marlborough Region": {"Canterbury Region", "Nelson Region", "Tasman Region"},
              "West Coast Region": {"Canterbury Region", "Tasman Region", "Otago Region"}}


def geocode_audit(P):
    g = P.groupby(["suburb", "tla", "region"]).gauge.agg(lambda s: s.value_counts().index[0]).reset_index()
    g["gauge_council"] = g.gauge.str.split("__").str[0].map(COUNCIL)
    g["same"] = g.gauge_council == g.region
    g["neighbour"] = ~g.same & g.apply(lambda r: r.region in NEIGHBOURS.get(r.gauge_council, set()), axis=1)
    far = g[~g.same & ~g.neighbour]
    out = {"suburbs": len(g), "same_council": int(g.same.sum()), "neighbouring_council": int(g.neighbour.sum()),
           "distant_mismatch": len(far), "distant_examples": far.head(25)[["suburb", "tla", "region", "gauge"]].to_dict("records")}
    (T / "g4_geocode.json").write_text(json.dumps(out, indent=1) + "\n")
    print({k: v for k, v in out.items() if k != "distant_examples"})


def exact_d6(f, day):
    t, v, q = MX.load(HL / "data" / "series" / f"{f}.npz")
    bad = MX.bad_quality(q, "S3") | ~np.isfinite(v) | np.r_[False, MX.physical_bad(np.diff(t), v[1:])]
    rain = np.where(bad, 0.0, v)
    C = np.r_[0.0, np.cumsum(rain[1:])]
    a = day.value / 6e10; b = a + 1440
    lo = a + MX.BIN                                 # the grid's first window ends 5 minutes into the day
    ends = np.unique(np.r_[t, t + 360, lo, b])
    ends = ends[(ends >= lo) & (ends <= b)]         # exact maximum over the same domain as the grid
    return float((np.interp(ends, t, C) - np.interp(ends - 360, t, C)).max())


def main():
    P = pd.read_parquet(D / "panel.parquet", columns=["suburb", "tla", "region", "day", "gauge", "d6"])
    geocode_audit(P)
    s = P[P.d6 > 0].drop_duplicates(["gauge", "day"]).sample(30, random_state=20261028)
    s = s.assign(exact=[exact_d6(r.gauge, r.day) for r in s.itertuples()])
    s["grid_over_exact"] = s.d6 / s.exact
    s[["gauge", "day", "d6", "exact", "grid_over_exact"]].to_csv(T / "g4_window.csv", index=False)
    print(s[["gauge", "day", "d6", "exact", "grid_over_exact"]].round(3).to_string(index=False))
    print("grid never above exact:", bool((s.d6 <= s.exact + 1e-6).all()), "| min ratio", round(float(s.grid_over_exact.min()), 4))


if __name__ == "__main__":
    main()
