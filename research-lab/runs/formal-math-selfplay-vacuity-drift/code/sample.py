"""Draw the preregistered STP samples (plan.md section 2). No Lean checks here.
Outputs (data/samples/, git-ignored with data/):
  stp_conjecture.parquet: up to 2,000 rows per conjecture iteration in random order (column `rank` 0..1999);
                          analysis takes rank < 2000 (primary windows) or rank < 1000/2000 elsewhere (pilot rule)
  stp_statement.parquet:  200 statement rows per iteration 0-47
  pilot.parquet:          300 conjecture rows from outside the main sample (timing pilot only)
and results/tables/stp_counts.csv (rows by iteration and tag)."""
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
SEED = 20261005
OUT = RUN / "data" / "samples"


def load():
    fs = sorted((RUN / "data" / "raw" / "STP_Lean_0320" / "data").glob("*.parquet"))
    df = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    df["tag"] = df.tag.astype(str).str.strip("[]'")
    df["row_id"] = np.arange(len(df))
    return df


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    df = load()
    ct = pd.crosstab(df.iteration, df.tag)
    ct.to_csv(RUN / "results" / "tables" / "stp_counts.csv")
    rng = np.random.default_rng(SEED)
    conj = df[df.tag == "conjecture"]
    parts, rest = [], []
    for it, g in conj.groupby("iteration"):
        idx = rng.permutation(len(g))
        take = g.iloc[idx[:2000]].copy()
        take["rank"] = np.arange(len(take))
        take["N_iter"] = len(g)
        parts.append(take)
        rest.append(g.iloc[idx[2000:]])
    s = pd.concat(parts, ignore_index=True)
    s.to_parquet(OUT / "stp_conjecture.parquet")
    st = df[df.tag == "statement"]
    sp = []
    for it, g in st.groupby("iteration"):
        t = g.iloc[rng.permutation(len(g))[:200]].copy()
        t["N_iter"] = len(g)
        sp.append(t)
    pd.concat(sp, ignore_index=True).to_parquet(OUT / "stp_statement.parquet")
    r = pd.concat(rest)
    pilot = r.iloc[rng.choice(len(r), 300, replace=False)]
    pilot.to_parquet(OUT / "pilot.parquet")
    print("conjecture sample", len(s), "| iterations", s.iteration.nunique(), "| statement sample", sum(len(x) for x in sp), "| pilot", len(pilot))


if __name__ == "__main__":
    main()
