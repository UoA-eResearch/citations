#!/usr/bin/env python
"""Label-shuffle control (plan.md sec 6, H3): with the real test predictions, cliff labels are permuted among each target's
test molecules (keeping the number of cliff molecules), 200 times; the gap should then be about zero. Also writes the
per-target and per-model summary used in the report.
Output: results/tables/control_shuffle.csv, results/tables/summary_by_target.csv, results/tables/summary_by_model.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import models as MD  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"


def main():
    pred = pd.read_parquet(TAB / "predictions.parquet")
    mol = pd.read_parquet(TAB / "molecules.parquet")
    pm = pred.merge(mol[["dataset", "idx", "cliff_mol"]], on=["dataset", "idx"])
    rng = np.random.default_rng(0)
    rows = []
    for (name, model, seed), g in pm.groupby(["dataset", "model", "seed"]):
        if seed != 0:
            continue
        y, p, c = g.y.values, g.pred.values, g.cliff_mol.values == 1
        shuf = [MD.gap(y, p, rng.permutation(c))[0] for _ in range(200)]
        rows.append(dict(dataset=name, model=model, gap_real=MD.gap(y, p, c)[0], gap_shuffled_mean=float(np.mean(shuf))))
    ctl = pd.DataFrame(rows)
    ctl.to_csv(TAB / "control_shuffle.csv", index=False)
    print("label-shuffle control: mean real gap %.3f, mean shuffled gap %.4f" % (ctl.gap_real.mean(), ctl.gap_shuffled_mean.mean()))
    cp = pd.read_parquet(TAB / "cliff_pairs_conf.parquet")
    cl = cp[cp.cliff]
    gt = pd.read_csv(TAB / "gaps_by_target.csv").set_index("dataset")
    nt = pd.read_csv(TAB / "null_gaps.csv").groupby(["dataset", "draw"]).gap.mean().groupby("dataset").mean()
    nn = pd.read_csv(TAB / "null_gaps_normal.csv").groupby(["dataset", "draw"]).gap.mean().groupby("dataset").mean()
    st = pd.DataFrame(dict(cliff_pairs=cl.groupby("dataset").size(), frac_conf_le_0p8_t=cl.groupby("dataset").conf.apply(lambda c: (c <= 0.8).mean()),
                           gap=gt.gap, rmse_cliff=gt.rmse_cliff, rmse_noncliff=gt.rmse_noncliff, n_cliff_test=gt.n_cliff_test,
                           null_gap_t=nt, null_gap_normal=nn))
    st.to_csv(TAB / "summary_by_target.csv")
    print(st.describe().loc[["mean", "min", "max"]].round(3).to_string())
    bm = pd.read_csv(TAB / "gaps_by_model.csv").groupby("model")[["gap", "rmse_cliff", "rmse_noncliff"]].mean()
    bm["null_gap_t"] = pd.read_csv(TAB / "null_gaps.csv").groupby("model").gap.mean()
    bm["null_gap_normal"] = pd.read_csv(TAB / "null_gaps_normal.csv").groupby("model").gap.mean()
    bm.to_csv(TAB / "summary_by_model.csv")
    print(bm.round(3).to_string())


if __name__ == "__main__":
    main()
