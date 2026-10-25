"""H1 analysis (plan section 0 and 5). Written before any RF result was read.

DiD per species = mean over C2..C6 of AUROC - AUROC(C1), on range-masked source test cells; mean over species with a
species bootstrap (2,000 resamples, seed 20261025). Supported if mean >= 0.02 and lower bound > 0; Refuted if upper
bound < 0.02; Inconclusive otherwise. Species need a defined AUROC in all seven conditions.
Secondary: the same contrast on other test cells and all test cells; the raw C0 - C1 and C0 - random drops; DiD by
source database (databases with at least 50 species).
-> results/tables/primary.json, results/tables/species_did.csv
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
W, T = RUN / "data" / "work", RUN / "results" / "tables"
SEED, B = 20261025, 2000
RAND = ["C2", "C3", "C4", "C5", "C6"]


def load():
    rows = [json.loads(f.read_text()) for f in (W / "rf").glob("C*.json")]
    return pd.DataFrame(rows)


def boot(x, rng):
    x = np.asarray(x, float)
    bs = [x[rng.integers(len(x), size=len(x))].mean() for _ in range(B)]
    return float(x.mean()), [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]


def contrast(d, col, rng):
    w = d.pivot(index="sp", columns="cond", values=col).dropna()
    if not len(w):
        return None
    did = w[RAND].mean(axis=1) - w["C1"]
    drop1 = w["C0"] - w["C1"]
    dropr = w["C0"] - w[RAND].mean(axis=1)
    m, ci = boot(did, rng)
    return {"species": int(len(w)), "did": round(m, 5), "ci": [round(c, 5) for c in ci],
            "drop_C0_minus_C1": round(float(drop1.mean()), 5), "drop_C0_minus_random": round(float(dropr.mean()), 5),
            "auroc_C0": round(float(w["C0"].mean()), 4), "auroc_C1": round(float(w["C1"].mean()), 4),
            "auroc_random": round(float(w[RAND].mean(axis=1).mean()), 4),
            "species_changed_by_C1": int((w["C1"] != w["C0"]).sum())}, did


def coverage(d):
    """G2 (METHODS.md): fits per condition and species with an undefined AUROC (no positives or no negatives among
    range-masked cells), which the contrast drops."""
    import sys
    sys.path.insert(0, str(RUN.parents[1] / "tools"))
    from coverage import Coverage
    pop = pd.read_csv(T / "population.csv").sp.tolist()
    for col in ("auroc_src", "auroc_other", "auroc_all"):
        cov = Coverage(f"rf_{col}", T / "coverage.json")
        got = {(r.sp, r.cond): r[col] for _, r in d.iterrows()}
        for sp in pop:
            for c in ["C0", "C1"] + RAND:
                cov.attempt((sp, c))
                if (sp, c) not in got:
                    cov.drop((sp, c), "fit missing")
                elif pd.isna(got[(sp, c)]):
                    cov.drop((sp, c), "AUROC undefined (one class only)")
                else:
                    cov.ok((sp, c))
        cov.save()


def main():
    rng = np.random.default_rng(SEED)
    d = load()
    coverage(d)
    out = {"fits": int(len(d)), "reused_fits": int(d.get("reused", pd.Series(False)).fillna(False).sum())}
    res, did = contrast(d, "auroc_src", rng)
    res["verdict"] = ("Supported" if res["did"] >= 0.02 and res["ci"][0] > 0 else
                      "Refuted" if res["ci"][1] < 0.02 else "Inconclusive")
    out["H1_source_cells"] = res
    out["other_cells"] = contrast(d, "auroc_other", rng)[0]
    out["all_cells"] = contrast(d, "auroc_all", rng)[0]
    by = {}
    dbs = sorted({k for x in d.auroc_db for k in (x or {})})
    for db in dbs:
        d[f"db_{db}"] = d.auroc_db.map(lambda x: (x or {}).get(db))
        c = contrast(d, f"db_{db}", rng)
        if c and c[0]["species"] >= 50:
            by[db] = c[0]
    out["by_source_db"] = by
    (T / "primary.json").write_text(json.dumps(out, indent=1))
    did.rename("did").reset_index().to_csv(T / "species_did.csv", index=False)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
