"""D3b (confirmation finding C1): the null re-ranked by -log P(<=1) (d3_fixes.log_null, binom.logcdf), which does not
saturate; log P(>=2) (logsf) had saturated at exactly 0.0 for the same candidates the probability saturated at 1.0.

Only null-dependent quantities are recomputed here. The model fits are deterministic (fixed hyperparameters and
seeds; the reviewer reproduced them bit for bit), so the model metrics are carried over from the first D3 run, and one
model fit at the preregistered seed is redone for the H1 bootstrap.

  d3c_null.py -> results/tables/d3.json (null fields, ratios and H1_d3 replaced; "null_version": "logcdf")
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyse as A  # noqa: E402
import d3_fixes as F  # noqa: E402

d = json.loads((A.T / "d3.json").read_text())
d["null_version"] = "logcdf (D3b); model metrics carried over from the first D3 run (deterministic fits)"
for task, (trn, ten) in {"primary": ("train", "test"), "first_appearance": ("train_any", "test_any"),
                         "three_isolates": ("train_3", "test_3"), "all_genes": ("train_allgenes", "test_allgenes")}.items():
    te = pd.read_parquet(A.D / f"task_{ten}.parquet"); y = te.y.to_numpy(); ln = F.log_null(te, 2022, 2025)
    r = d[task]
    r["null_log"] = F.metrics(ln, y)
    r["null_distinct_scores_top1000"] = int(len(np.unique(np.sort(ln)[::-1][:1000])))
    r["null_log_p@100_row_order"] = float(y[np.argsort(-ln, kind="stable")[:100]].mean())
    pn = r["null_log"]["p@100"]
    r["ratio_p@100_by_seed"] = [x / pn if pn > 0 else None for x in r["full_p@100_by_seed"]]
    r["auprc_ratio_by_seed"] = [x["full"]["auprc"] / r["null_log"]["auprc"] for x in r["runs"]]
    print(task, "null p@100", round(pn, 4), "auprc", round(r["null_log"]["auprc"], 4), "distinct top1000", r["null_distinct_scores_top1000"],
          "| ratios", [round(x, 2) if x is not None else None for x in r["ratio_p@100_by_seed"]], flush=True)
    if task == "primary":
        tr = pd.read_parquet(A.D / "task_train.parquet")
        p_pre = F.fit(tr, te, A.FULL, A.SEED)
        pm, pn0 = F.topk(p_pre, y, 100), F.topk(ln, y, 100)
        rb = np.random.default_rng(A.SEED); ratios = []
        for idx in A.boot_indices(te.gene.to_numpy(), rb, A.B):
            a, b = F.topk(p_pre[idx], y[idx], 100), F.topk(ln[idx], y[idx], 100)
            ratios.append(np.inf if (b == 0 and a > 0) else (np.nan if b == 0 else a / b))
        ratios = np.array(ratios, float); lo, hi = np.nanpercentile(ratios, [2.5, 97.5])
        ratio = pm / pn0 if pn0 > 0 else None
        d["H1_d3"] = {"model_p@100": pm, "null_log_p@100": pn0, "ratio": ratio, "ci": [float(lo), float(hi)],
                      "draws_0_over_0_dropped": int(np.isnan(ratios).sum()), "draws_model_over_zero": int(np.isinf(ratios).sum()),
                      "verdict": "Supported" if (ratio or 0) >= 2 and lo > 1 else "Refuted" if hi < 2 else "Inconclusive",
                      "ratio_by_seed": r["ratio_p@100_by_seed"]}
        sc = -np.expm1(-ln)
        q = pd.qcut(pd.Series(sc).rank(method="first"), 10, labels=False)
        d["null_calibration"]["exact"] = pd.DataFrame({"q": q, "p": sc, "y": y}).groupby("q").agg(mean_p=("p", "mean"), observed=("y", "mean")).round(5).to_dict("index")
        print("H1", d["H1_d3"], flush=True)
(A.T / "d3.json").write_text(json.dumps(d, indent=1, default=float) + "\n")
