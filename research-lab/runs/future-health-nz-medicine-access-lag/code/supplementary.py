"""Supplementary counts for the report (descriptive): milestone counts; how many consented substances show a provisional
consent route (status or a 'Provisional' application, where T2 may be the later full-consent date, D6.4); funded
substances with a PHARMAC application before Medsafe consent; the share of the cohort that is EMA-first with a generic
class name (the D7 residual). Writes results/tables/supplementary.json."""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analysis import load  # noqa: E402
from link import has_any  # noqa: E402

RUN = Path(__file__).resolve().parents[1]


def main():
    d, cutoff = load()
    P = pd.read_csv(RUN / "data" / "medsafe_products.csv", dtype=str)
    A = pd.read_csv(RUN / "data" / "medsafe_applications.csv", dtype=str)
    prov = 0
    for r in d[d.t2.notna()].itertuples():
        pats = str(r.match_names).split("|")
        p = P[P.substance.isin(pats) & P.ingredients.map(lambda x: has_any(pats, x))]
        a = A[A.substance.isin(pats) & A.ingredients.map(lambda x: has_any(pats, x))]
        if p.status.str.contains("Provisional", na=False).any() or a.type.str.contains("Provisional", na=False).any() \
                or a.change.str.contains("Provisional", na=False).any():
            prov += 1
    out = dict(cohort=int(len(d)), consented=int(d.t2.notna().sum()), funded=int(d.t3.notna().sum()),
               funded_community=int(d.t3b.notna().sum()), funded_hospital=int(d.t3h.notna().sum()),
               tga=int(d.t_tga.notna().sum()), applications=int(d.t_app.notna().sum()),
               consented_with_provisional_route=prov,
               funded_without_consent=int((d.t3.notna() & d.t2.isna()).sum()),
               t0_2024=int((d.t0.dt.year == 2024).sum()), t0_2024_consented=int(((d.t0.dt.year == 2024) & d.t2.notna()).sum()),
               t0_2024_funded=int(((d.t0.dt.year == 2024) & d.t3.notna()).sum()))
    json.dump(out, open(RUN / "results" / "tables" / "supplementary.json", "w"), indent=1)
    print(out)


if __name__ == "__main__":
    sys.exit(main())
