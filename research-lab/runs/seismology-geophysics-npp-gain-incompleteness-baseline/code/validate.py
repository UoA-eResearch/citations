"""Validation on simulated catalogs (plan.md section 3): simulate from model A and model B (only observed events
trigger, so each likelihood is exact), fit S2, A and B, check parameter recovery and that the true model wins.
Output: results/tables/validation.csv"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import etas_lib as E  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TRUE = dict(mu=0.5, K=0.2, alpha=1.5, c=0.02, p=1.2, beta=2.3)
M0 = 1.2


def main():
    rows = []
    for gen, extra in [("A", dict(Tb=0.01)), ("B", dict(G=3.0, H=0.8))]:
        tr = TRUE | extra
        mt, mm = np.array([150.0, 400.0, 900.0]), np.array([6.3, 5.8, 6.0])
        T, M = E.simulate(tr["mu"], tr["K"], tr["alpha"], tr["c"], tr["p"], tr["beta"], M0, 1300.0,
                          1 if gen == "A" else 2, tr.get("Tb", 0.0), tr.get("G", 0.0), tr.get("H", 0.0), 7, mt, mm)
        print(gen, "simulated events", len(T))
        start = dict(mu=0.3, K=0.15, alpha=1.0, c=0.05, p=1.3, Tb=0.02, G=2.5, H=1.0, beta=2.0)
        for model in ("S2", "A", "B"):
            t0 = time.time()
            d = E.fit(model, T, M, M0, [start])
            row = dict(generator=gen, model=model, n=len(T), seconds=round(time.time() - t0, 1),
                       **{k: d[k] for k in E.NAMES[model]}, beta_fit=d["beta"], train_ll_per_event=d["train_ll_per_event"],
                       soe_err=d["soe_max_rel_err"])
            rows.append(row)
            print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in row.items()})
        rows.append(dict(generator=gen, model="TRUE", **tr))
    pd.DataFrame(rows).to_csv(RUN / "results" / "tables" / "validation.csv", index=False)


if __name__ == "__main__":
    main()
