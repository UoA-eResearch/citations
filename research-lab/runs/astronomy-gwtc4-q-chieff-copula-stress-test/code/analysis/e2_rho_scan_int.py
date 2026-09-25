#!/usr/bin/env python
"""D27: nuisance-integrated rho scan (replaces the plug-in scan of D20, whose value depended on the plug-in nuisance).

Statistic, identical for the real catalog and every mock: the Gaussian-copula likelihood averaged over a FIXED
ensemble of K = 16 equal-weight posterior draws theta_k of the independence fit (copula_indep_plp),
    L_int(rho) = (1/K) sum_k L(rho, theta_k),
on a 77-point rho grid; rho_hat_int = argmax, LR0_int = 2 [max ln L_int - ln L_int(0)], and P(rho < 0) under a flat prior.
The mocks (v2, D27) are generated from other random posterior draws, so the offset between a mock's true nuisance and
the ensemble mirrors the real catalog's. Per catalog the spread of the single-draw rho_hat across the ensemble is also
recorded (the reviewer's nuisance-sensitivity diagnostic).

Usage: ../venv/bin/python analysis/e2_rho_scan_int.py [--mock-dir data/mocks/v2] [--backend gpu]
Outputs: results/tables/e2_rhoscan_int_full.csv / .json
"""
from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import logsumexp

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from config import load_config  # noqa: E402
from gpu import GPUSession  # noqa: E402
from io_utils import read_injection_table  # noqa: E402

COLS = ("mass_1", "mass_ratio", "chi_eff", "redshift")
RHO = np.linspace(-0.95, 0.95, 77)
K_ENS = 16


def summarize(L):                       # L: (K, n_rho) log-likelihoods
    L = np.where(np.isfinite(L), L, -np.inf)
    Li = logsumexp(L, axis=0) - np.log(L.shape[0])
    i = int(np.argmax(Li)); i0 = int(np.argmin(np.abs(RHO)))
    rh = RHO[i]
    if 0 < i < len(RHO) - 1:
        y0, y1, y2 = Li[i - 1], Li[i], Li[i + 1]
        den = y0 - 2 * y1 + y2
        if den < 0:
            rh = RHO[i] + 0.5 * (y0 - y2) / den * (RHO[1] - RHO[0])
    w = np.exp(Li - Li.max()); w /= w.sum()
    single = RHO[np.argmax(L, axis=1)]
    # E1 analogue within the scan: Bayes factor of a flat prior on rho over the grid (~U(-0.95, 0.95)) against rho = 0
    ln_bf = float(logsumexp(Li) - np.log(len(RHO)) - Li[i0])
    return dict(rho_hat=float(rh), lr0=float(2 * (Li.max() - Li[i0])), p_rho_neg=float(w[RHO < 0].sum()), ln_bf_flat=ln_bf,
                post_mean=float(np.sum(w * RHO)), single_rho_hat_sd=float(single.std()),
                single_rho_hat_min=float(single.min()), single_rho_hat_max=float(single.max()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock-dir", default=None)
    ap.add_argument("--backend", default="gpu")
    ap.add_argument("--chunk", type=int, default=308)
    ap.add_argument("--sample-table", default=None,
                    help="alternative real-catalog sample table (waveform variants, D25): real catalog only, no mocks")
    ap.add_argument("--tag", default="", help="output suffix for --sample-table runs")
    ap.add_argument("--shared-gpu", action="store_true",
                    help="run beside another GPU job: no vllm handling, memory capped and not preallocated (use --chunk 77)")
    args = ap.parse_args()
    if args.shared_gpu:
        os.environ.update(JAX_PLATFORMS="cuda", XLA_PYTHON_CLIENT_PREALLOCATE="false", XLA_PYTHON_CLIENT_MEM_FRACTION="0.13")
    cfg = load_config(mode="full", config_path=str(HERE.parent / "config.yaml"))
    if args.sample_table:
        alt = Path(args.sample_table)
        cfg.sample_table_path = lambda: alt          # load_event_arrays reads the real catalog from here
    mock_dir = Path(args.mock_dir) if args.mock_dir else cfg.path("mocks_dir") / "v2"
    tables = cfg.path("tables_dir")
    post = np.load(cfg.fit_dir("copula_indep_plp") / "posterior.npz", allow_pickle=True)
    pn = [str(x) for x in post["names"]]
    ens = post["samples"][np.random.default_rng(20260925).choice(len(post["samples"]), K_ENS, replace=False)]

    with (contextlib.nullcontext(type("S", (), {"platform": "cuda (shared)"})) if args.shared_gpu
          else GPUSession(cfg, args.backend)) as gs:
        import h5py
        import jax
        jax.config.update("jax_enable_x64", True)
        from fit_models import load_event_arrays
        from jaxmodels import Grids, HierarchicalLikelihood
        from models_registry import build_model
        print("JAX platform:", gs.platform, flush=True)
        G = Grids(cfg, cfg.mode_value("mass_spline_nodes"), cfg.mode_value("marginal_spline_nodes"))
        spec, names, fixed, _ = build_model("copula_gauss_plp", cfg)
        ir = names.index("gaussian_copula_rho")
        thetas = np.zeros((K_ENS * len(RHO), len(names)))
        for k in range(K_ENS):
            base = np.array([ens[k][pn.index(n)] if n in pn else 0.0 for n in names])
            thetas[k * len(RHO):(k + 1) * len(RHO)] = base
            thetas[k * len(RHO):(k + 1) * len(RHO), ir] = RHO
        inj = read_injection_table(cfg.injection_table_path())

        def scan(ev):
            lik = HierarchicalLikelihood(spec, names, fixed, ev, inj, G, max_variance=1e12,
                                         enforce_injection_convergence=False, cache_key="rhoscan_int")
            return summarize(lik.make_batched(args.chunk)(thetas).reshape(K_ENS, len(RHO)))

        rows = []
        t0 = time.time()
        # D26b item 3: the real catalog is scanned with several independent 2000-sample subsamples (the mocks carry 2000
        # samples per event); the median over subsamples is the observed statistic, the spread its Monte Carlo error
        subs = []
        for s_i in range(5):
            ev_real, _, _ = load_event_arrays(cfg, np.random.default_rng(1000 + s_i), max_samples=2000)
            r = scan(ev_real)
            subs.append(r)
            rows.append(dict(kind="real_sub", set="real", mock=s_i, **r))
            print(f"REAL subsample {s_i}: rho_hat_int={r['rho_hat']:+.3f} LR0={r['lr0']:.2f} P(rho<0)={r['p_rho_neg']:.2f} "
                  f"single-draw rho_hat sd {r['single_rho_hat_sd']:.3f} [{r['single_rho_hat_min']:+.2f}, {r['single_rho_hat_max']:+.2f}] "
                  f"({time.time() - t0:.0f}s)", flush=True)
        r = {k: float(np.median([x[k] for x in subs])) for k in subs[0]}
        r["rho_hat_mc_sd"] = float(np.std([x["rho_hat"] for x in subs]))
        rows.append(dict(kind="real", set="real", mock=-1, **r))
        if args.sample_table:
            out = {"sample_table": str(args.sample_table), "ensemble_size": K_ENS, **{k: float(v) for k, v in r.items()},
                   "subsamples": [x["rho_hat"] for x in subs]}
            json.dump(out, open(tables / f"e2_rhoscan_int_full_{args.tag}.json", "w"), indent=2)
            print(json.dumps(out), flush=True)
            return
        for path in sorted(mock_dir.glob("mocks_full_*.h5")):
            tag = path.stem.replace("mocks_full_", "")
            t1 = time.time()
            with h5py.File(path, "r") as fh:
                for k in sorted(k for k in fh if k.startswith("mock_")):
                    g = fh[k]
                    ev = {c: np.asarray(g[c]) for c in COLS}
                    ev["ln_prior"] = np.asarray(g["ln_prior"])
                    rows.append(dict(kind="mock", set=tag, mock=int(k.split("_")[1]), **scan(ev)))
            sub = pd.DataFrame([x for x in rows if x["set"] == tag])
            print(f"{tag:<9} n={len(sub)} rho_hat_int median {sub.rho_hat.median():+.3f} [{sub.rho_hat.quantile(0.16):+.3f}, "
                  f"{sub.rho_hat.quantile(0.84):+.3f}] LR0 median {sub.lr0.median():.2f} ({time.time() - t1:.0f}s)", flush=True)

    df = pd.DataFrame(rows)
    out_tag = mock_dir.name
    df.to_csv(tables / f"e2_rhoscan_int_full_{out_tag}.csv", index=False)
    real = df[df.kind == "real"].iloc[0]
    null = df[df.set == "rho+0.00"]
    out = {"ensemble_size": K_ENS, "mock_dir": str(mock_dir), "observed": {k: float(real[k]) for k in
           ("rho_hat", "lr0", "p_rho_neg", "ln_bf_flat", "post_mean", "single_rho_hat_sd", "rho_hat_mc_sd")},
           "fpr": {"rho_hat_as_extreme": float(np.mean(null.rho_hat >= real.rho_hat) if real.rho_hat >= 0 else np.mean(null.rho_hat <= real.rho_hat)),
                   "rho_hat_two_sided": float(np.mean(np.abs(null.rho_hat - null.rho_hat.median()) >= abs(real.rho_hat - null.rho_hat.median()))),
                   "lr0_ge_observed": float(np.mean(null.lr0 >= real.lr0)),
                   "ln_bf_flat_ge_observed": float(np.mean(null.ln_bf_flat >= real.ln_bf_flat)),
                   "p_rho_neg_le_observed": float(np.mean(null.p_rho_neg <= real.p_rho_neg)), "n_null": int(len(null))},
           "sets": {}}
    for tag, sub in df[df.kind == "mock"].groupby("set"):
        out["sets"][tag] = dict(n=int(len(sub)), rho_hat_median=float(sub.rho_hat.median()), rho_hat_p16=float(sub.rho_hat.quantile(0.16)),
                                rho_hat_p84=float(sub.rho_hat.quantile(0.84)), lr0_median=float(sub.lr0.median()),
                                ln_bf_flat_median=float(sub.ln_bf_flat.median()), p_rho_neg_median=float(sub.p_rho_neg.median()),
                                power_lr0_gt_null95=float(np.mean(sub.lr0 > null.lr0.quantile(0.95))),
                                power_rho_neg_beyond_null5=float(np.mean(sub.rho_hat < null.rho_hat.quantile(0.05))))
    json.dump(out, open(tables / f"e2_rhoscan_int_full_{out_tag}.json", "w"), indent=2)
    print(json.dumps(out, indent=1), flush=True)


if __name__ == "__main__":
    main()
