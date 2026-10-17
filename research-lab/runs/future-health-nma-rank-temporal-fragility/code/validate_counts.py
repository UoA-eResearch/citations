"""Validation V2 (plan section 6): parsed study and treatment counts against the catalogue's counts. Reported only.
Writes results/tables/v2_counts.csv and prints the agreement."""
import json
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]


def main():
    s = pd.read_csv(RUN / "data" / "std_summary.csv", dtype={"record": str})
    fits = {json.loads(l)["record"]: json.loads(l)["fits"][0] for l in open(RUN / "data" / "fits_full.jsonl")}
    s = s[s.record.isin(fits)].copy()
    s["cat_studies"] = pd.to_numeric(s.cat_studies, errors="coerce")
    s["cat_trts"] = pd.to_numeric(s.cat_trts, errors="coerce").where(lambda x: x > 0)
    s["fit_trts"] = s.record.map(lambda r: fits[r].get("n_trts"))
    s["studies_match"] = s.n_studies == s.cat_studies
    s["trts_match"] = s.n_trts == s.cat_trts
    s[["record", "format", "n_studies", "cat_studies", "studies_match", "n_trts", "cat_trts", "trts_match", "fit_trts"]].to_csv(
        RUN / "results" / "tables" / "v2_counts.csv", index=False)
    print(len(s), "networks; studies match", int(s.studies_match.sum()), "; treatments match", int(s.trts_match.sum()),
          "of", int(s.cat_trts.notna().sum()), "with a catalogue count")
    d = (s.n_studies - s.cat_studies)
    print("study-count differences:", d[d != 0].describe().round(1).to_dict())


if __name__ == "__main__":
    main()
