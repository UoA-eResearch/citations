"""Pipeline check (plan section 5), run after recompute.py and before analysis.py: for the 10 eligible signals with the
largest reported case counts, the recomputed drug-event count a (primary protocol and the variants) beside the paper's
reported count. Counts only; no ROR is compared here. Descriptive. Writes results/tables/pipeline_check.csv."""
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]


def main():
    e = pd.read_csv(RUN / "data" / "signals_eligible.csv", dtype={"paper": str})
    r = pd.read_csv(RUN / "data" / "recomputed.csv", dtype={"paper": str})
    d = e.merge(r[["paper", "k", "status"] + [c for c in r.columns if c.endswith("_a")]], on=["paper", "k"], how="left")
    top = d[d.n_cases.notna() & (d.status == "ok")].sort_values("n_cases", ascending=False).head(10)
    cols = ["paper", "drug", "ingredient", "event_uk", "win", "n_cases", "primary_a", "allsuspect_a", "nodedup_a", "fullwindow_a"]
    top = top[cols].copy()
    top["primary_over_reported"] = top.primary_a / top.n_cases
    top["allsuspect_over_reported"] = top.allsuspect_a / top.n_cases
    top.to_csv(RUN / "results" / "tables" / "pipeline_check.csv", index=False)
    print(top.to_string(index=False))
    print("median primary/reported", round(top.primary_over_reported.median(), 3), "; all-suspect/reported", round(top.allsuspect_over_reported.median(), 3))


if __name__ == "__main__":
    main()
