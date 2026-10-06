"""Score the frozen forecasts (plan section 5) once Health NZ publishes new quarterly files. Written and committed
before any target release. Usage: score.py  (re-run fetch.py and parse.py first so data/coverage.parquet contains the
new quarters). Checks the frozen file's sha256 against the value recorded in deviations.md D1, then:
- H2 (primary): district Totals (20 districts) at h = 1 and 2 (2026Q3 and 2026Q4), pooled over whichever of the two
  releases are available: MAE (pp) and the share of cells inside the preregistered 80% interval [lo80, hi80].
  Supported if MAE <= 2.5 and coverage in [0.70, 0.90] once both releases are in; Refuted if MAE > 2.5 or coverage
  outside [0.70, 0.90] once both are in; "pending" before that (partial results are reported).
- Secondary: the recent-window interval, Maori and Pacific cells, h = 3 and 4, the national total, and the
  persistence baseline (latest published C24 at the origin) on the same cells.
Writes results/tables/h2_score.json and results/tables/h2_cells.csv."""
import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"


def main():
    f = RUN / "results" / "forecasts_frozen.csv"
    want = re.search(r"Its sha256 is\s+([0-9a-f]{64})", (RUN / "deviations.md").read_text()).group(1)  # D1's hash
    got = hashlib.sha256(f.read_bytes()).hexdigest()
    assert got == want, f"frozen file hash mismatch: {got} != {want}"
    fr = pd.read_csv(f)
    d = pd.read_parquet(RUN / "data" / "coverage.parquet")
    # D2: parse-only edits for new layouts are allowed but must leave the historical rows (to 2026Q2) unchanged
    hist = d[pd.to_datetime(d.quarter_end) <= "2026-06-30"].sort_values(["quarter_end", "milestone", "district", "group"])
    hh = hashlib.sha256(hist[["quarter_end", "milestone", "district", "group", "eligible", "immunised"]].astype(str).to_csv(index=False).encode()).hexdigest()
    want_h = re.search(r"historical rows hash\s+([0-9a-f]{64})", (RUN / "deviations.md").read_text()).group(1)
    assert hh == want_h, f"historical coverage rows changed: {hh} != {want_h}"
    d = d[(d.milestone == 24) & (d.eligible > 0) & d.immunised.notna()].copy()
    d["target"] = [f"{t.year}Q{(t.month - 1) // 3 + 1}" for t in pd.to_datetime(d.quarter_end)]
    d["actual"] = d.immunised / d.eligible
    m = fr.merge(d[["target", "district", "group", "actual", "eligible"]], on=["target", "district", "group"], how="inner")
    m["ae"] = (m.forecast - m.actual).abs() * 100
    m["ae_persistence"] = (m.last_published_C24 - m.actual).abs() * 100
    m["in80"] = (m.actual >= m.lo80) & (m.actual <= m.hi80)
    m["in80_recent"] = (m.actual >= m.lo80_recent) & (m.actual <= m.hi80_recent)
    m.to_csv(TAB / "h2_cells.csv", index=False)
    prim = m[(m.group == "Total") & (m.district != "National total") & m.h.isin([1, 2])]
    out = dict(frozen_sha256=got, releases_scored=sorted(prim.target.unique()), n_cells=len(prim))
    if len(prim):
        out.update(MAE=float(prim.ae.mean()), coverage80=float(prim.in80.mean()), coverage80_recent=float(prim.in80_recent.mean()),
                   MAE_persistence=float(prim.ae_persistence.mean()))
    both = set(prim.target) >= {"2026Q3", "2026Q4"}
    if both:
        assert len(prim) == 40, f"expected 40 district-Total cells, got {len(prim)}"  # D2
    big = ["Auckland", "Counties Manukau", "Waitematā", "Canterbury", "Waikato", "Capital and Coast", "Southern"]
    if len(prim):
        out["coverage80_seven_largest_districts"] = float(prim[prim.district.isin(big)].in80.mean())
        out["coverage80_other_districts"] = float(prim[~prim.district.isin(big)].in80.mean())
    if not both:
        out["verdict_H2"] = "pending"
    elif out["MAE"] <= 2.5 and 0.70 <= out["coverage80"] <= 0.90:
        out["verdict_H2"] = "Supported"
    else:
        out["verdict_H2"] = "Refuted"
    sec = {}
    for lab, sel in [("Maori h1-2", (m.group == "Maori") & m.h.isin([1, 2])), ("Pacific h1-2", (m.group == "Pacific") & m.h.isin([1, 2])),
                     ("district Totals h3-4", (m.group == "Total") & (m.district != "National total") & m.h.isin([3, 4])),
                     ("national Total", (m.group == "Total") & (m.district == "National total"))]:
        x = m[sel & (m.district != "National total") if "national" not in lab else sel]
        if len(x):
            sec[lab] = dict(n=len(x), MAE=float(x.ae.mean()), coverage80=float(x.in80.mean()), MAE_persistence=float(x.ae_persistence.mean()))
    out["secondary"] = sec
    json.dump(out, open(TAB / "h2_score.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
