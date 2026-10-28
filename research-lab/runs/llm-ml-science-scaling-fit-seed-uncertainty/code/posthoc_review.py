"""POST HOC (after independent review, on the corrected-N refit): numbers the review asked the report to state.

  1. Share of single-seed forecast variance explained by each size's seed (eta squared), and the 410M seed's
     per-seed median forecasts.
  2. Share of single-seed forecasts above the actual 2.8B loss; percentiles of the fitted E.
  3. Paired document-bootstrap SD of loss differences that share the evaluation tokens.
  4. Late rise (final minus minimum over checkpoints) per seed at 14M and 31M.

  posthoc_review.py -> results/tables/posthoc_review.json
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
T, SQ = RUN / "results" / "tables", RUN / "data" / "seqloss"
SIZES = ["14m", "31m", "70m", "160m", "410m"]


def main():
    out = {}
    L = pd.read_csv(T / "ladders_single.csv", keep_default_na=False, na_values=["NA"])
    seeds = L.seeds.str.split("-", expand=True).astype(int); seeds.columns = SIZES
    y = L.pred_2p8b.to_numpy(); tot = ((y - y.mean()) ** 2).sum()
    out["eta2_by_size_seed"] = {s: round(float(sum(len(g) * (g.mean() - y.mean()) ** 2 for _, g in pd.Series(y).groupby(seeds[s])) / tot), 3)
                                for s in SIZES}
    out["median_forecast_by_410m_seed"] = {int(k): round(float(v), 4) for k, v in pd.Series(y).groupby(seeds["410m"]).median().items()}
    actual = json.loads((T / "primary.json").read_text())["target"]["2.8b"]["loss"]
    out["share_single_seed_overshoot"] = round(float((y > actual).mean()), 3)
    out["E_single_p5_p50_p95"] = [round(float(np.percentile(L.E, q)), 3) for q in (5, 50, 95)]
    # paired document bootstrap on the shared evaluation tokens
    docs = np.load(RUN / "data" / "eval_docs.npy")
    ud, inv = np.unique(docs, return_inverse=True)
    rng = np.random.default_rng(20261028)
    pairs = {"2.8b_minus_410m_seed0": ("pythia-2.8b_step143000_float16.npy", "pythia-410m_step143000_float32.npy"),
             "2.8b_minus_1.4b": ("pythia-2.8b_step143000_float16.npy", "pythia-1.4b_step143000_float32.npy"),
             "410m_seed4_minus_seed0": ("pythia-410m-seed4_step143000_float32.npy", "pythia-410m_step143000_float32.npy")}
    out["paired_doc_bootstrap_sd"] = {}
    for name, (a, b) in pairs.items():
        dif = np.load(SQ / a).astype(float) - np.load(SQ / b).astype(float)
        s = np.bincount(inv, dif); n = np.bincount(inv)
        bs = []
        for _ in range(1000):
            k = rng.integers(0, len(ud), len(ud))
            bs.append(s[k].sum() / n[k].sum())
        out["paired_doc_bootstrap_sd"][name] = {"mean_difference": round(float(dif.mean()), 4), "sd": round(float(np.std(bs)), 4)}
    # late rises at 14M and 31M
    l = pd.read_csv(T / "losses.csv", keep_default_na=False, na_values=["NA"])
    l = l[l.dtype == "float32"]
    out["late_rise_final_minus_min"] = {}
    for s in ("14m", "31m"):
        g = l[l["size"] == s].sort_values("step").groupby("seed").loss
        out["late_rise_final_minus_min"][s] = {int(k): round(float(v.iloc[-1] - v.min()), 3) for k, v in g}
    (T / "posthoc_review.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
