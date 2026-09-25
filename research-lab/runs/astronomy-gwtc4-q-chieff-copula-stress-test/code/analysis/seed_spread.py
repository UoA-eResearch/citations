#!/usr/bin/env python
"""D28: sampler-noise spread of the Linear-model slope credibilities and ln Z across nautilus seeds.

For each configuration refitted with SEED_TAG=k (fits/<mode>/<model>__seed<k>), compares ln Z, P(mu_1 < 0) and
P(ln sigma_1 < 0) with the original fit, estimated from nautilus' WEIGHTED posterior points (the equal-weight
resample can collapse when one point dominates). Each fit is also screened for Monte Carlo likelihood spikes (largest
single-point weight share); for a flagged fit the credibilities are also given with the spike region
(mu_chi_eff_1 > 1 and sigma_chi_eff_1 > 2, where a narrow low-q chi_eff peak meets one posterior sample) removed.
Output: results/tables/seed_spread_full.{csv,json}
"""
import json
from pathlib import Path
import numpy as np, pandas as pd
RUN = Path(__file__).resolve().parents[2]
FITS, TAB = RUN / "results" / "fits" / "full", RUN / "results" / "tables"
MODELS = ["baseline_plp_both", "lvk_bpl2p_both", "abl_plp_lvkspin_both", "abl_bpl2p_plpspin_both"]
rows = []
for m in MODELS:
    for tag in ["", "__seed2", "__seed3"]:
        d = FITS / f"{m}{tag}"
        if not (d / "summary.json").exists():
            continue
        s = json.load(open(d / "summary.json"))
        p = np.load(d / "posterior.npz", allow_pickle=True)
        names = [str(x) for x in p["names"]]
        X, lw = p["weighted_points"], p["weighted_log_w"]
        w = np.exp(lw - lw.max()); w /= w.sum()
        imu, isg = names.index("mu_chi_eff_1"), names.index("sigma_chi_eff_1")
        spike = w.max() > 0.005
        keep = ~((X[:, imu] > 1.0) & (X[:, isg] > 2.0)) if spike else np.ones(len(w), bool)
        wk = w * keep; wk /= wk.sum()
        rows.append(dict(model=m, seed=tag.strip("_") or "seed1", log_z=s["log_z"], max_log_l=s["max_log_l"],
                         max_weight_share=float(w.max()), spike=bool(spike),
                         p_mu1_negative=float((w * (X[:, imu] < 0)).sum()),
                         p_lnsigma1_negative=float((w * (X[:, isg] < 0)).sum()),
                         p_mu1_negative_spike_removed=float((wk * (X[:, imu] < 0)).sum()),
                         p_lnsigma1_negative_spike_removed=float((wk * (X[:, isg] < 0)).sum()),
                         weight_in_spike_region=float(w[~keep].sum())))
df = pd.DataFrame(rows)
df.to_csv(TAB / "seed_spread_full.csv", index=False)
summ = {}
for m, g in df.groupby("model"):
    summ[m] = {k: dict(values=g[k].round(4).tolist(), range=float(g[k].max() - g[k].min()))
               for k in ("log_z", "p_mu1_negative_spike_removed", "p_lnsigma1_negative_spike_removed", "p_mu1_negative", "p_lnsigma1_negative")}
    summ[m]["spike_seeds"] = g[g.spike].seed.tolist()
json.dump(summ, open(TAB / "seed_spread_full.json", "w"), indent=2)
cols = ["model", "seed", "log_z", "max_log_l", "max_weight_share", "p_mu1_negative", "p_lnsigma1_negative",
        "p_mu1_negative_spike_removed", "p_lnsigma1_negative_spike_removed"]
print(df[cols].round(4).to_string(index=False))
print({m: {k: round(v["range"], 4) for k, v in s.items() if isinstance(v, dict)} for m, s in summ.items()})
