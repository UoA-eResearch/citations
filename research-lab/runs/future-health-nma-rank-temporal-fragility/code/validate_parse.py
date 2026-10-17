"""Validation V1 (plan section 6): side-by-side evidence of raw sheet vs standardised table for a random sample.

Sample: 20 networks at random from those passing the size and year rules (seed 20261018), plus label-year networks
(D1) drawn at random until at least 8 are in the sample. Writes data/validation/v1/<record>.txt and the sample list
data/validation/v1_sample.csv. The adjudication is entered by hand in results/tables/v1_parse_validation.csv."""
import random
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")
RUN = Path(__file__).resolve().parents[1]
OUT = RUN / "data" / "validation" / "v1"


def main():
    s = pd.read_csv(RUN / "data" / "std_summary.csv", dtype={"record": str})
    e = s[s.parsed & (s.measure != "other") & (s.n_trts >= 3) & (s.n_studies >= 10) & (s.year_share >= 0.90)]
    rnd = random.Random(20261018)
    pick = rnd.sample(sorted(e.record), 20)
    ly = sorted(e[e.issues.fillna("").str.contains("D1")].record)
    rest = [r for r in ly if r not in pick]
    rnd.shuffle(rest)
    while sum(r in ly for r in pick) < 8 and rest:
        pick.append(rest.pop())
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"record": pick, "label_year": [r in ly for r in pick]}).to_csv(OUT.parent / "v1_sample.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_colwidth", 40)
    for rid in pick:
        raw = pd.read_excel(RUN / "data" / "raw" / "datasets" / f"{rid}.xlsx")
        std = pd.read_csv(RUN / "data" / "std" / f"{rid}.csv")
        meta = e[e.record == rid].iloc[0]
        with open(OUT / f"{rid}.txt", "w") as fh:
            fh.write(f"record {rid}  format {meta.format}  type {meta.type}  measure {meta.measure}  direction {meta.direction}\n")
            fh.write(f"parsed: studies {meta.n_studies}  treatments {meta.n_trts}  rows {meta.n_rows}  years {meta.year_min}-{meta.year_max} "
                     f"(share {meta.year_share:.2f})  issues: {meta.issues}\n")
            fh.write(f"catalogue: studies {meta.cat_studies}  treatments {meta.cat_trts}\n\n== RAW ({raw.shape[0]} rows)\n")
            fh.write(raw.to_string(max_rows=400) + "\n\n== STANDARDISED\n" + std.to_string(max_rows=400) + "\n")
    print(len(pick), "networks;", sum(r in ly for r in pick), "label-year")


if __name__ == "__main__":
    main()
