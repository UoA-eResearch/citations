#!/usr/bin/env python
"""D22 (exploratory): is any q-chi_eff dependence localised in primary mass?

Likelihood scan of `copula_gauss_mbin_plp` -- a Gaussian copula with a separate rho in each preregistered E5
primary-mass bin (m1 < 20, 20-40, >= 40 Msun; bins assigned by each sample's own m1, so the model is normalised for
every m1) -- on a 17^3 grid (rho in -0.8 ... +0.8, step 0.1), with all other hyperparameters fixed at the null
population (copula_indep_plp posterior median). Identical settings for the real catalog and all 360 mocks
(2000 samples per event, all 1.07 M found injections), exactly as the global scan of D20.

Per catalog: rho_hat per bin (3-D argmax), LR_zero = 2 [max ln L - ln L(0,0,0)], LR_het = 2 [max ln L - max over
the diagonal rho0 = rho1 = rho2] (evidence that the bins differ), and per-bin fixed-marginal posterior means and
P(rho_b < 0) under flat priors on the grid.

Outputs: results/tables/e2_rhoscan_mbin_full.csv, results/tables/e2_rhoscan_mbin_full.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from config import load_config  # noqa: E402
from gpu import GPUSession  # noqa: E402
from io_utils import load_json, read_injection_table  # noqa: E402

COLS = ("mass_1", "mass_ratio", "chi_eff", "redshift")
GRID = np.round(np.linspace(-0.8, 0.8, 17), 3)
NB = 3


def summarize(lnl):
    L = np.asarray(lnl, float).reshape((len(GRID),) * NB)
    L = np.where(np.isfinite(L), L, -np.inf)
    idx = np.unravel_index(np.argmax(L), L.shape)
    i0 = int(np.argmin(np.abs(GRID)))
    diag = np.array([L[i, i, i] for i in range(len(GRID))])
    w = np.exp(L - L.max())
    w /= w.sum()
    out = dict(lnl_max=float(L.max()), lr_zero=float(2 * (L.max() - L[i0, i0, i0])),
               lr_het=float(2 * (L.max() - diag.max())), rho_common_hat=float(GRID[int(np.argmax(diag))]))
    for b in range(NB):
        axes = tuple(a for a in range(NB) if a != b)
        marg = w.sum(axis=axes)
        out[f"rho_hat_b{b}"] = float(GRID[idx[b]])
        out[f"post_mean_b{b}"] = float(np.sum(marg * GRID))
        out[f"p_neg_b{b}"] = float(marg[GRID < 0].sum())
        prof = L.max(axis=axes)                                   # profile likelihood in rho_b
        out[f"lr_zero_b{b}"] = float(2 * (prof.max() - prof[i0]))
        out[f"at_edge_b{b}"] = bool(idx[b] in (0, len(GRID) - 1))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="full")
    ap.add_argument("--backend", default="gpu")
    ap.add_argument("--chunk", type=int, default=256)
    ap.add_argument("--limit", type=int, default=0, help="only the first N mocks per rho_true (testing)")
    args = ap.parse_args()
    cfg = load_config(mode=args.mode, config_path=str(HERE.parent / "config.yaml"))
    tables = cfg.path("tables_dir")
    ref = load_json(cfg.fit_dir("copula_indep_plp") / "summary.json")
    base = {n: q["median"] for n, q in ref["quantiles"].items()}
    base.update(ref.get("fixed", {}))

    with GPUSession(cfg, args.backend) as gs:
        import h5py
        import jax
        jax.config.update("jax_enable_x64", True)
        from fit_models import load_event_arrays
        from jaxmodels import Grids, HierarchicalLikelihood
        from models_registry import build_model
        print(f"JAX platform: {gs.platform}", flush=True)
        G = Grids(cfg, cfg.mode_value("mass_spline_nodes"), cfg.mode_value("marginal_spline_nodes"))
        spec, names, fixed, prior = build_model("copula_gauss_mbin_plp", cfg)
        rho_idx = [names.index(f"rho_b{b}") for b in range(NB)]
        mesh = np.array(np.meshgrid(*([GRID] * NB), indexing="ij")).reshape(NB, -1).T      # (17^3, 3)
        thetas = np.tile(np.array([base.get(n, 0.0) for n in names], float), (len(mesh), 1))
        thetas[:, rho_idx] = mesh
        inj = read_injection_table(cfg.injection_table_path())
        ev_real, _, _ = load_event_arrays(cfg, cfg.rng("fit_subsample"), max_samples=2000)

        def scan(ev):
            lik = HierarchicalLikelihood(spec, names, fixed, ev, inj, G, max_variance=1e12,
                                         enforce_injection_convergence=False, cache_key="rhoscan_mbin")
            return summarize(lik.make_batched(args.chunk)(thetas))

        rows = []
        t0 = time.time()
        r = scan(ev_real)
        rows.append(dict(kind="real", rho_true=np.nan, mock=-1, **r))
        print("REAL: " + " ".join(f"rho_hat_b{b}={r[f'rho_hat_b{b}']:+.2f} (mean {r[f'post_mean_b{b}']:+.2f}, "
                                  f"P<0 {r[f'p_neg_b{b}']:.2f})" for b in range(NB))
              + f" | LR_zero={r['lr_zero']:.2f} LR_het={r['lr_het']:.2f} ({time.time() - t0:.1f}s incl. compile)", flush=True)
        for rho in [0.0] + list(cfg.rho_true_grid):
            t1 = time.time()
            with h5py.File(cfg.mocks_path(rho), "r") as fh:
                keys = sorted(k for k in fh if k.startswith("mock_"))
                if args.limit:
                    keys = keys[: args.limit]
                for k in keys:
                    g = fh[k]
                    ev = {c: np.asarray(g[c]) for c in COLS}
                    ev["ln_prior"] = np.asarray(g["ln_prior"])
                    rows.append(dict(kind="mock", rho_true=rho, mock=int(k.split("_")[1]), **scan(ev)))
            sub = pd.DataFrame([x for x in rows if x["kind"] == "mock" and x["rho_true"] == rho])
            print(f"rho_true={rho:+.2f}: n={len(sub)} " + " ".join(
                f"b{b} rho_hat median {sub[f'rho_hat_b{b}'].median():+.2f}" for b in range(NB))
                  + f" | LR_het median {sub.lr_het.median():.2f} ({time.time() - t1:.0f}s)", flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(tables / f"e2_rhoscan_mbin_{args.mode}.csv", index=False)
    real = df[df.kind == "real"].iloc[0]
    null = df[(df.kind == "mock") & (df.rho_true == 0.0)]
    out = {"grid": [float(GRID[0]), float(GRID[-1]), len(GRID)], "bins_msun": [[2, 20], [20, 40], [40, 1e9]],
           "observed": {k: (float(real[k]) if not isinstance(real[k], (bool, np.bool_)) else bool(real[k]))
                        for k in real.index if k not in ("kind", "rho_true", "mock")},
           "fpr": {"lr_zero_ge_observed": float(np.mean(null.lr_zero >= real.lr_zero)),
                   "lr_het_ge_observed": float(np.mean(null.lr_het >= real.lr_het)), "n_null": int(len(null))},
           "per_bin": []}
    for b in range(NB):
        v = null[f"rho_hat_b{b}"].values
        o = real[f"rho_hat_b{b}"]
        out["per_bin"].append(dict(bin=b, observed_rho_hat=float(o), null_median=float(np.median(v)),
                                   null_p16=float(np.quantile(v, 0.16)), null_p84=float(np.quantile(v, 0.84)),
                                   fpr_rho_hat=float(np.mean(v <= o) if o <= 0 else np.mean(v >= o)),
                                   fpr_lr_zero_b=float(np.mean(null[f"lr_zero_b{b}"] >= real[f"lr_zero_b{b}"])),
                                   observed_p_neg=float(real[f"p_neg_b{b}"])))
    out["response"] = []
    for rho in [0.0] + list(cfg.rho_true_grid):
        m = df[(df.kind == "mock") & np.isclose(df.rho_true, rho)]
        out["response"].append(dict(rho_true=rho, n=int(len(m)), **{f"rho_hat_b{b}_median": float(m[f"rho_hat_b{b}"].median())
                                                                    for b in range(NB)}))
    with open(tables / f"e2_rhoscan_mbin_{args.mode}.json", "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps({k: out[k] for k in ("fpr", "per_bin")}, indent=1), flush=True)


if __name__ == "__main__":
    main()
