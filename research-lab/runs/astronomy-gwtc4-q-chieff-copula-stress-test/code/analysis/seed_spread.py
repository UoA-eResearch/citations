#!/usr/bin/env python
"""D28: sampler-noise spread of the Linear-model slope credibilities and ln Z across nautilus seeds.

For each configuration refitted with SEED_TAG=k (fits/<mode>/<model>__seed<k>), compares ln Z, P(mu_1 < 0) and
P(ln sigma_1 < 0) with the original fit. Output: results/tables/seed_spread_full.{csv,json}
"""
import json, sys
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
        smp = p["samples"]
        mu = next(n for n in ("mu_chi_eff_1",) if n in names)
        sg = next(n for n in ("sigma_chi_eff_1",) if n in names)
        rows.append(dict(model=m, seed=tag.strip("_") or "seed1", log_z=s["log_z"],
                         p_mu1_negative=float(np.mean(smp[:, names.index(mu)] < 0)),
                         p_lnsigma1_negative=float(np.mean(smp[:, names.index(sg)] < 0)), n_eq=len(smp)))
df = pd.DataFrame(rows)
df.to_csv(TAB / "seed_spread_full.csv", index=False)
summ = {m: {k: dict(values=g[k].round(4).tolist(), range=float(g[k].max() - g[k].min())) for k in ("log_z", "p_mu1_negative", "p_lnsigma1_negative")}
        for m, g in df.groupby("model")}
json.dump(summ, open(TAB / "seed_spread_full.json", "w"), indent=2)
print(df.round(4).to_string(index=False))
