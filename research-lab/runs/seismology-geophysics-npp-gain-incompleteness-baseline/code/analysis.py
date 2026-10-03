"""Preregistered analysis (plan.md sections 3-5): primary model choice (A vs B by training log-likelihood per event),
recovery fraction R with a 24-h block bootstrap, decision rule, and the decomposition of the gap.
Outputs: results/tables/primary.csv, decomposition.csv, tiles.json
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
CONFIGS = [("Visso", 1.2), ("Norcia", 1.2), ("Campotosto", 1.3)]
RNG = np.random.default_rng(20261004)
B = 2000


def boot_R(pw, model):
    blocks = pw.block.unique()
    g = pw.groupby("block")
    sums = g[["S0", "NPP", model]].sum()
    cnt = g.size()
    out = []
    for _ in range(B):
        bs = RNG.choice(blocks, len(blocks), replace=True)
        s = sums.loc[bs].sum()
        n = cnt.loc[bs].sum()
        m = s / n
        den = m.NPP - m.S0
        out.append((m[model] - m.S0) / den if den != 0 else np.nan)
    return np.nanpercentile(out, [2.5, 97.5])


def main():
    rows, dec = [], []
    for seq, cut in CONFIGS:
        f = json.load(open(RUN / "results" / "fits" / f"{seq}_{cut}.json"))
        pw = pd.read_parquet(RUN / "results" / "pointwise" / f"{seq}_{cut}.parquet")
        s1 = np.load(TAB / f"s1_pointwise_{seq}.npy")
        pw["S1"] = s1
        prim = "A" if f["A"]["train_ll_per_event"] >= f["B"]["train_ll_per_event"] else "B"
        m = pw[["S0", "S1", "S2", "A", "B", "NPP"]].mean()
        G = m.NPP - m.S0
        for model in ("A", "B"):
            R = (m[model] - m.S0) / G
            lo, hi = boot_R(pw, model)
            rows.append(dict(config=seq, cutoff=cut, model=model, primary=model == prim, n_targets=len(pw), G=G,
                             LL_S0=m.S0, LL_model=m[model], LL_NPP=m.NPP, R=R, R_lo=lo, R_hi=hi,
                             train_ll_A=f["A"]["train_ll_per_event"], train_ll_B=f["B"]["train_ll_per_event"]))
        dec.append(dict(config=seq, G=G, history_S1_minus_S0=m.S1 - m.S0, refit_S2_minus_S1=m.S2 - m.S1,
                        incompleteness_primary_minus_S2=m[prim] - m.S2, remainder_NPP_minus_primary=m.NPP - m[prim],
                        primary=prim))
    res = pd.DataFrame(rows)
    res.to_csv(TAB / "primary.csv", index=False)
    pd.DataFrame(dec).to_csv(TAB / "decomposition.csv", index=False)
    p = res[res.primary]
    n_rec = int((p.R >= 0.75).sum())
    n_fail = int((p.R_hi < 0.75).sum())
    verdict = "Supported" if n_rec >= 2 else ("Contradicted" if n_fail >= 2 else "Inconclusive")
    print(res.round(3).to_string(index=False))
    print(pd.DataFrame(dec).round(3).to_string(index=False))
    print(f"configurations with R >= 0.75: {n_rec}; with R upper bound < 0.75: {n_fail} -> VERDICT: {verdict}")
    pd.Series(dict(verdict=verdict, n_recovered=n_rec, n_failed=n_fail)).to_csv(TAB / "verdict.csv")


if __name__ == "__main__":
    main()
