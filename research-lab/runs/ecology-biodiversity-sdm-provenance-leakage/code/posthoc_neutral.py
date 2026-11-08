"""Neutral counterfactual (D4, after the independent review's finding 3; post hoc). -> results/tables/posthoc_neutral.json

In C1 a removed provenance-only presence can become a background (pseudo-absence) cell for that species, so the
TAVA DiD mixes "lost information" with "trained to predict absence at the test location". The neutral variants
C1n..C6n remove the same presences but also keep those cells out of that species' background (rf.py fit_neutral).

  posthoc_neutral.py species   species with a defined per-database AUROC for TAVA West Africa or the Ukraine
                               Grassland Database in C0 -> results/tables/neutral_species.csv
  posthoc_neutral.py analyse   per-database DiD, standard and neutral, on the same species
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
W, T = RUN / "data" / "work", RUN / "results" / "tables"
DBS = ["TAVA West_Africa", "Ukraine Grassland Database"]
SEED, B = 20261025, 2000


def rows(pattern):
    return pd.DataFrame([json.loads(f.read_text()) for f in (W / "rf").glob(pattern)])


def species():
    d = rows("C0_*.json")
    pop = set(pd.read_csv(T / "population.csv").sp)
    d = d[d.sp.isin(pop)]
    keep = d[d.auroc_db.map(lambda x: any((x or {}).get(db) is not None for db in DBS))]
    keep[["sp"]].drop_duplicates().sort_values("sp").to_csv(T / "neutral_species.csv", index=False)
    print(len(keep), "species")


def did(d, db, conds1, rand):
    d = d.assign(v=d.auroc_db.map(lambda x: (x or {}).get(db)))
    w = d.pivot(index="sp", columns="cond", values="v").dropna()
    if not len(w):
        return None, None
    x = (w[rand].mean(axis=1) - w[conds1]).to_numpy(float)
    rng = np.random.default_rng(SEED)
    bs = [x[rng.integers(len(x), size=len(x))].mean() for _ in range(B)]
    return {"species": int(len(w)), "did": round(float(x.mean()), 4),
            "ci": [round(float(np.percentile(bs, 2.5)), 4), round(float(np.percentile(bs, 97.5)), 4)]}, set(w.index)


def analyse():
    sp = set(pd.read_csv(T / "neutral_species.csv").sp)
    d = pd.concat([rows("C*.json")])
    d = d[d.sp.isin(sp)]
    out = {}
    for db in DBS:
        std, s1 = did(d[d.cond.isin(["C1", "C2", "C3", "C4", "C5", "C6"])], db, "C1", ["C2", "C3", "C4", "C5", "C6"])
        neu, s2 = did(d[d.cond.isin(["C1n", "C2n", "C3n", "C4n", "C5n", "C6n"])], db, "C1n", ["C2n", "C3n", "C4n", "C5n", "C6n"])
        out[db] = {"standard": std, "neutral": neu}
    (T / "posthoc_neutral.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    {"species": species, "analyse": analyse}[sys.argv[1]]()
