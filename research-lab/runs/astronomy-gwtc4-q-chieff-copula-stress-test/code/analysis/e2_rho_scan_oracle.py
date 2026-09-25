#!/usr/bin/env python
"""D27c: where does the null bias of the integrated rho scan on v3b come from? (diagnostic, not a new test statistic)

The integrated scan (e2_rho_scan_int.py) gives rho_hat_int median -0.14 on the rho = 0 v3b mocks. Two oracle variants use
each mock's TRUE generating hyperparameters (stored with the mock), which a real catalog does not have:
  (a) 'truth':    plug-in scan at the true nuisance (K = 1). If the mock generator and the likelihood are consistent this is
                  unbiased up to finite-catalog noise; a bias here would point at the generator / likelihood, not the nuisance.
  (b) 'centred':  the same fixed 16-draw ensemble as the integrated scan, translated so its mean equals the true nuisance
                  (clipped into the prior box). Compared with the plain integrated scan this isolates the effect of the
                  ensemble's offset from the mock's own nuisance.

Runs beside other GPU jobs: memory is capped and not preallocated, no vllm handling (GPUSession is bypassed).
Usage: JAX_PLATFORMS=cuda ../venv/bin/python analysis/e2_rho_scan_oracle.py [--sets rho+0.00,rho-0.40,rho+0.20] [--max-mocks 80]
Output: results/tables/e2_rhoscan_oracle_v3.csv
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("XLA_PYTHON_CLIENT_PREALLOCATE", "false")
os.environ.setdefault("XLA_PYTHON_CLIENT_MEM_FRACTION", "0.13")
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))

from config import load_config  # noqa: E402
from io_utils import read_injection_table  # noqa: E402
from e2_rho_scan_int import COLS, K_ENS, RHO, summarize  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock-dir", default=None)
    ap.add_argument("--sets", default="rho+0.00,rho-0.40,rho+0.20")
    ap.add_argument("--max-mocks", type=int, default=80)
    ap.add_argument("--chunk", type=int, default=77)
    ap.add_argument("--noiseless", action="store_true",
                    help="(c) replace each event's PE samples by its true parameters (K = 1, ln_prior = 0): isolates the "
                         "estimator's own finite-catalog behaviour from the measurement / selection model")
    ap.add_argument("--pdet", action="store_true",
                    help="(d) analyse each mock with the likelihood that matches how v3b was generated: detection was drawn "
                         "from the true parameters (found injections) and the PE noise independently, so each event's "
                         "integrand carries P_det(theta) (Essick & Fishbach 2024, arXiv:2310.02017)")
    args = ap.parse_args()
    if args.pdet:
        from pdet_grid import PdetGrid
        pdg = PdetGrid(cfg_path := HERE.parent.parent / "data" / "processed" / "pdet_grid_full.npz")
    cfg = load_config(mode="full", config_path=str(HERE.parent / "config.yaml"))
    mock_dir = Path(args.mock_dir) if args.mock_dir else cfg.path("mocks_dir") / "v3"
    post = np.load(cfg.fit_dir("copula_indep_plp") / "posterior.npz", allow_pickle=True)
    pn = [str(x) for x in post["names"]]
    ens = post["samples"][np.random.default_rng(20260925).choice(len(post["samples"]), K_ENS, replace=False)]

    import h5py
    import jax
    jax.config.update("jax_enable_x64", True)
    from jaxmodels import Grids, HierarchicalLikelihood
    from models_registry import build_model
    print("JAX devices:", jax.devices(), flush=True)
    G = Grids(cfg, cfg.mode_value("mass_spline_nodes"), cfg.mode_value("marginal_spline_nodes"))
    spec, names, fixed, prior = build_model("copula_gauss_plp", cfg)
    ir = names.index("gaussian_copula_rho")
    nuis = [i for i in range(len(names)) if i != ir]
    base = np.array([[e[pn.index(n)] if n in pn else 0.0 for n in names] for e in ens])      # (K, n_par)
    # spline nodes are unbounded (Gaussian random-walk prior); only the uniform-prior parameters are clipped
    lo = np.where(prior.uniform_mask, prior.lo, -np.inf)
    hi = np.where(prior.uniform_mask, prior.hi, np.inf)
    inj = read_injection_table(cfg.injection_table_path())

    def grid(ensemble):
        th = np.repeat(ensemble, len(RHO), axis=0)
        th[:, ir] = np.tile(RHO, len(ensemble))
        return th

    rows = []
    for tag in args.sets.split(","):
        t1 = time.time()
        with h5py.File(mock_dir / f"mocks_full_{tag}.h5", "r") as fh:
            keys = sorted(k for k in fh if k.startswith("mock_"))[: args.max_mocks]
            for k in keys:
                g = fh[k]
                if args.noiseless:
                    tr = np.asarray(g["true"])
                    ev = {c: tr[:, j:j + 1] for j, c in enumerate(COLS)}
                    ev["ln_prior"] = np.zeros_like(ev["mass_1"])
                else:
                    ev = {c: np.asarray(g[c]) for c in COLS}
                    ev["ln_prior"] = np.asarray(g["ln_prior"])
                    if args.pdet:
                        ev["ln_prior"] = ev["ln_prior"] - pdg.ln_pdet(ev["mass_1"], ev["mass_ratio"], ev["chi_eff"], ev["redshift"])
                par = json.loads(g.attrs["params"])
                true = np.array([par.get(n, 0.0) for n in names])
                lik = HierarchicalLikelihood(spec, names, fixed, ev, inj, G, max_variance=1e12,
                                             enforce_injection_convergence=False, cache_key="rhoscan_oracle" + ("_nl" if args.noiseless else "") + ("_pd" if args.pdet else ""))
                f = lik.make_batched(args.chunk)
                ra = summarize(np.asarray(f(grid(true[None, :]))).reshape(1, len(RHO)))
                cen = base.copy()
                cen[:, nuis] = base[:, nuis] - base[:, nuis].mean(0) + true[nuis]
                cen[:, nuis] = np.clip(cen[:, nuis], lo[nuis], hi[nuis])
                rb = summarize(np.asarray(f(grid(cen))).reshape(K_ENS, len(RHO)))
                rows.append(dict(set=tag, mock=int(k.split("_")[1]), rho_true=par.get("gaussian_copula_rho", np.nan),
                                 rho_hat_truth=ra["rho_hat"], lr0_truth=ra["lr0"],
                                 rho_hat_centred=rb["rho_hat"], lr0_centred=rb["lr0"],
                                 single_sd_centred=rb["single_rho_hat_sd"]))
        sub = pd.DataFrame([r for r in rows if r["set"] == tag])
        print(f"{tag:<9} n={len(sub)}  truth: median {sub.rho_hat_truth.median():+.3f} [{sub.rho_hat_truth.quantile(.16):+.3f}, "
              f"{sub.rho_hat_truth.quantile(.84):+.3f}]  centred: median {sub.rho_hat_centred.median():+.3f} "
              f"[{sub.rho_hat_centred.quantile(.16):+.3f}, {sub.rho_hat_centred.quantile(.84):+.3f}] ({time.time() - t1:.0f}s)", flush=True)
        pd.DataFrame(rows).to_csv(cfg.path("tables_dir") / f"e2_rhoscan_oracle_v3{'_noiseless' if args.noiseless else ''}{'_pdet' if args.pdet else ''}.csv", index=False)


if __name__ == "__main__":
    main()
