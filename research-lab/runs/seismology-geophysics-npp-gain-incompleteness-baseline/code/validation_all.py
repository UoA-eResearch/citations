"""All validation tables, regenerated with the final code and the wide multi-start (deviations.md D2-D3).

1. validation.csv: one catalog simulated from A and one from B (seed 7, mainshocks M6.3/5.8/6.0); fits of S2, A and B
   with training log-likelihood per event, plus the true-parameter log-likelihood.
2. validation_recovery.csv: delta-method SEs and the plan's criterion (|z| <= 2 or within 10%) for the generating model.
3. validation_seeds_A.csv / validation_seeds_B.csv: 8 seeds each, with and without imposed mainshocks.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

sys.path.insert(0, str(Path(__file__).resolve().parent))
import etas_lib as E  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
TRUE = dict(mu=0.5, K=0.2, alpha=1.5, c=0.02, p=1.2, beta=2.3)
GEN = {"A": dict(Tb=0.01), "B": dict(G=3.0, H=0.8)}
M0 = 1.2
MAINS = (np.array([150.0, 400.0, 900.0]), np.array([6.3, 5.8, 6.0]))
NOMAINS = (np.array([1e9]), np.array([0.0]))


def starts():
    out = []
    for c, a, tb, p, k in [(0.02, 1.5, 0.01, 1.2, 0.2), (1e-3, 2.0, 0.003, 1.1, 0.1), (0.1, 1.0, 0.03, 1.4, 0.3),
                           (0.005, 2.2, 0.006, 1.15, 0.05), (0.3, 1.3, 0.02, 1.3, 0.15), (0.01, 1.8, 0.001, 1.25, 0.25)]:
        out.append(dict(mu=0.3, K=k, alpha=a, c=c, p=p, Tb=tb, G=2.5, H=1.0, beta=2.0))
        out.append(dict(mu=0.6, K=k, alpha=a, c=c, p=p, Tb=tb, G=3.5, H=0.6, beta=2.5))
    return out


def simulate(gen, seed, mains=True, tend=1300.0):
    tr = TRUE | GEN[gen]
    mt, mm = MAINS if mains else NOMAINS
    return E.simulate(tr["mu"], tr["K"], tr["alpha"], tr["c"], tr["p"], tr["beta"], M0, tend if mains else 3000.0,
                      1 if gen == "A" else 2, tr.get("Tb", 0.0), tr.get("G", 0.0), tr.get("H", 0.0), seed, mt, mm)


def fit_one(gen, model, T, M):
    d = E.fit(model, T, M, M0, starts(), refine=3)
    return d


def main():
    rows, rec = [], []
    for gen in ("A", "B"):
        tr = TRUE | GEN[gen]
        T, M = simulate(gen, 7)
        ll_true = E.train_ll(tr, gen, T, M, M0)[0] / (len(T) - 1)
        fits = Parallel(n_jobs=3)(delayed(fit_one)(gen, m, T, M) for m in ("S2", "A", "B"))
        for model, d in zip(("S2", "A", "B"), fits):
            rows.append(dict(generator=gen, model=model, n=len(T), train_ll_per_event=d["train_ll_per_event"], true_ll_per_event=ll_true,
                             **{k: d[k] for k in E.NAMES[model]}, beta_used=d["beta"]))
            if model == gen:
                se = E.standard_errors(d, gen, T, M, M0)
                for k in E.NAMES[gen]:
                    z = (d[k] - tr[k]) / se[k] if se[k] > 0 else np.nan
                    rec.append(dict(generator=gen, param=k, true=tr[k], est=d[k], se=se[k], z=z,
                                    ok=bool(abs(z) <= 2 or abs(d[k] / tr[k] - 1) <= 0.10)))
    pd.DataFrame(rows).to_csv(TAB / "validation.csv", index=False)
    pd.DataFrame(rec).to_csv(TAB / "validation_recovery.csv", index=False)
    print(pd.DataFrame(rows).round(4).to_string(index=False))
    print(pd.DataFrame(rec).round(4).to_string(index=False))
    for gen in ("A", "B"):
        tr = TRUE | GEN[gen]

        def one(seed, mains):
            T, M = simulate(gen, seed, mains)
            d = E.fit(gen, T, M, M0, starts(), refine=2)
            return dict(seed=seed, mains=mains, n=len(T), ll_fit=d["train_ll_per_event"],
                        ll_true=E.train_ll(tr, gen, T, M, M0)[0] / (len(T) - 1), **{k: d[k] for k in E.NAMES[gen]})
        r = pd.DataFrame(Parallel(n_jobs=8)(delayed(one)(s, m) for s in range(10, 18) for m in (True, False)))
        r.to_csv(TAB / f"validation_seeds_{gen}.csv", index=False)
        print(gen, "mean over seeds"); print(r.groupby("mains")[E.NAMES[gen]].mean().round(4).to_string())
        print("fit >= true LL in", int((r.ll_fit >= r.ll_true - 1e-6).sum()), "of", len(r))


if __name__ == "__main__":
    main()
