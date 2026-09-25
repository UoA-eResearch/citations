#!/usr/bin/env python
"""D30: the preregistered E2 statistic as literally specified (plan sec 4 item 5): Kendall tau of posterior-MEAN point
estimates of q and chi_eff (the analysis has used medians since stage 04). Real catalog (4000 samples per event, as in
e2_tau.py) vs the v3c null mocks, under the PE prior (post) and with the prior removed (flattheta, same clipped
weights as e2_tau.py). Output: results/tables/e2_tau_means_v3c.json
"""
import json, os, sys
from pathlib import Path
os.environ.setdefault("JAX_PLATFORMS", "cpu")
import h5py, numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src")); sys.path.insert(0, str(HERE))
from config import load_config
from e2_tau import clipped_weights, tau, wmedian
from fit_models import load_event_arrays

cfg = load_config(mode="full", config_path=str(HERE.parent / "config.yaml"))
clip_q = float(cfg.raw["mocks"]["kernel_weight_clip_quantile"])


def stats(q, chi, lp):
    out = {}
    for lab, w in (("post", np.ones_like(q)), ("flattheta", clipped_weights(-lp, clip_q))):
        w = w / w.sum(1, keepdims=True)
        out[f"tau_mean_{lab}"] = tau((w * q).sum(1), (w * chi).sum(1))
        out[f"tau_median_{lab}"] = tau(wmedian(q, w), wmedian(chi, w))
    return out


ev, _, _ = load_event_arrays(cfg, cfg.rng("e2_tau_real") if hasattr(cfg, "rng") else np.random.default_rng(0), max_samples=4000)
real = stats(ev["mass_ratio"], ev["chi_eff"], ev["ln_prior"])
rows = []
with h5py.File(cfg.path("mocks_dir") / "v3c" / "mocks_full_rho+0.00.h5", "r") as fh:
    for k in sorted(k for k in fh if k.startswith("mock_")):
        g = fh[k]
        rows.append(stats(np.asarray(g["mass_ratio"]), np.asarray(g["chi_eff"]), np.asarray(g["ln_prior"])))
out = {"real": real, "null": {}}
for key in real:
    v = np.array([r[key] for r in rows])
    out["null"][key] = dict(median=float(np.median(v)), p2p5=float(np.quantile(v, 0.025)), p97p5=float(np.quantile(v, 0.975)),
                            fpr_one_sided=float(np.mean(v <= real[key])), n=len(v))
    print(f"{key:20s} real {real[key]:+.3f} | v3c null {np.median(v):+.3f} [{np.quantile(v, .025):+.3f}, {np.quantile(v, .975):+.3f}] | FPR {np.mean(v <= real[key]):.3f}")
json.dump(out, open(cfg.path("tables_dir") / "e2_tau_means_v3c.json", "w"), indent=2)
