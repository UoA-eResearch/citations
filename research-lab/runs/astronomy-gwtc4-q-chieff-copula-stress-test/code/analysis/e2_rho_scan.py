#!/usr/bin/env python
"""E2, hierarchical-likelihood version (deviation D20): parametric-bootstrap scan in the Gaussian-copula rho.

For the real catalog and every mock catalog (rho_true in {0} U grid), evaluate the selection-corrected
hierarchical likelihood of `copula_gauss_plp` on a grid of rho, with ALL other hyperparameters (mass model,
spline q|m1 and chi_eff marginals, redshift) fixed at the population the null mocks were drawn from -- the
posterior median of the real-data independence fit `copula_indep_plp`. Identical settings for real data and
mocks: 2000 posterior samples per event, all 1.07 M found injections, no Monte Carlo cuts (the fixed
marginals keep the estimator in a well-sampled region; var_tot and n_eff are recorded).

Per catalog: rho_hat (grid argmax refined by a local parabola), LR0 = 2 [ln L(rho_hat) - ln L(0)], and the
fixed-marginal posterior of rho under its U(-0.95, 0.95) prior (mean, median, P(rho < 0)).

Why not the stage-05 MAP statistics: unpenalised MAP optimisation of the Monte Carlo likelihood exploits
injection sparsity on mock catalogs (ln L rose from ~25 at a sensible point to ~600-1200 with rho pinned at
the prior edge), the known failure the LVK variance cuts exist to prevent (deviations D20).

Outputs: results/tables/e2_rhoscan_full.csv, results/tables/e2_rhoscan_full.json
Usage:   ../venv/bin/python analysis/e2_rho_scan.py [--backend gpu]
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
RHO_GRID = np.linspace(-0.95, 0.95, 77)          # step 0.025, the prior support


def summarize_scan(lnl, var_tot, n_eff):
    lnl = np.asarray(lnl, float)
    i = int(np.nanargmax(lnl))
    rho_hat = RHO_GRID[i]
    if 0 < i < len(RHO_GRID) - 1:                  # parabola through the three points around the maximum
        y0, y1, y2 = lnl[i - 1], lnl[i], lnl[i + 1]
        den = y0 - 2 * y1 + y2
        if den < 0:
            rho_hat = RHO_GRID[i] + 0.5 * (y0 - y2) / den * (RHO_GRID[1] - RHO_GRID[0])
    i0 = int(np.argmin(np.abs(RHO_GRID)))
    w = np.exp(lnl - np.nanmax(lnl))
    w = np.where(np.isfinite(w), w, 0.0)
    w /= w.sum()
    cdf = np.cumsum(w)
    return dict(rho_hat=float(rho_hat), lnl_max=float(lnl[i]), lnl_rho0=float(lnl[i0]),
                lr0=float(2 * (np.nanmax(lnl) - lnl[i0])), post_mean=float(np.sum(w * RHO_GRID)),
                post_median=float(np.interp(0.5, cdf, RHO_GRID)), p_rho_neg=float(w[RHO_GRID < 0].sum()),
                at_edge=bool(i in (0, len(RHO_GRID) - 1)), var_tot_at_hat=float(var_tot[i]),
                var_tot_at_0=float(var_tot[i0]), n_eff_at_hat=float(n_eff[i]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="full")
    ap.add_argument("--backend", default="gpu")
    ap.add_argument("--chunk", type=int, default=77)
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
        spec, names, fixed, prior = build_model("copula_gauss_plp", cfg)
        missing = [n for n in names if n != "gaussian_copula_rho" and n not in base]
        assert not missing, f"generating population lacks {missing}"
        i_rho = names.index("gaussian_copula_rho")
        thetas = np.tile(np.array([base.get(n, 0.0) for n in names], float), (len(RHO_GRID), 1))
        thetas[:, i_rho] = RHO_GRID
        inj = read_injection_table(cfg.injection_table_path())
        ev_real, _, _ = load_event_arrays(cfg, cfg.rng("fit_subsample"), max_samples=2000)

        def scan(ev):
            lik = HierarchicalLikelihood(spec, names, fixed, ev, inj, G, max_variance=1e12,
                                         enforce_injection_convergence=False, cache_key="rhoscan")
            f = lik.make_batched_aux(args.chunk)
            lnl, aux = f(thetas)
            return summarize_scan(lnl, aux["var_tot"], aux["n_eff_inj"])

        rows = []
        t0 = time.time()
        r = scan(ev_real)
        rows.append(dict(kind="real", rho_true=np.nan, mock=-1, **r))
        print(f"REAL: rho_hat={r['rho_hat']:+.3f} LR0={r['lr0']:.3f} post mean {r['post_mean']:+.3f} "
              f"P(rho<0)={r['p_rho_neg']:.3f} var_tot@hat={r['var_tot_at_hat']:.2f} n_eff={r['n_eff_at_hat']:.0f} "
              f"({time.time() - t0:.1f}s incl. compile)", flush=True)
        for rho in [0.0] + list(cfg.rho_true_grid):
            with h5py.File(cfg.mocks_path(rho), "r") as fh:
                keys = sorted(k for k in fh if k.startswith("mock_"))
                for k in keys:
                    g = fh[k]
                    ev = {c: np.asarray(g[c]) for c in COLS}
                    ev["ln_prior"] = np.asarray(g["ln_prior"])
                    rows.append(dict(kind="mock", rho_true=rho, mock=int(k.split("_")[1]), **scan(ev)))
            sub = pd.DataFrame([x for x in rows if x["kind"] == "mock" and x["rho_true"] == rho])
            print(f"rho_true={rho:+.2f}: n={len(sub)} rho_hat median {sub.rho_hat.median():+.3f} "
                  f"[{sub.rho_hat.quantile(0.16):+.3f}, {sub.rho_hat.quantile(0.84):+.3f}], LR0 median "
                  f"{sub.lr0.median():.2f}, at-edge {int(sub.at_edge.sum())} ({time.time() - t0:.0f}s)", flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(tables / f"e2_rhoscan_{args.mode}.csv", index=False)
    real = df[df.kind == "real"].iloc[0]
    null = df[(df.kind == "mock") & (df.rho_true == 0.0)]
    out = {"fixed_marginals_from": "copula_indep_plp posterior median", "rho_grid": [float(RHO_GRID[0]), float(RHO_GRID[-1]), len(RHO_GRID)],
           "observed": {k: (float(real[k]) if not isinstance(real[k], (bool, np.bool_)) else bool(real[k]))
                        for k in ("rho_hat", "lr0", "post_mean", "post_median", "p_rho_neg", "var_tot_at_hat")},
           "fpr": {"rho_hat_as_extreme": float(np.mean(null.rho_hat >= real.rho_hat) if real.rho_hat >= 0
                                               else np.mean(null.rho_hat <= real.rho_hat)),
                   "lr0_ge_observed": float(np.mean(null.lr0 >= real.lr0)),
                   "n_null": int(len(null))},
           "response_curve": []}
    for rho in [0.0] + list(cfg.rho_true_grid):
        m = df[(df.kind == "mock") & np.isclose(df.rho_true, rho)]
        out["response_curve"].append(dict(rho_true=rho, n=int(len(m)), rho_hat_median=float(m.rho_hat.median()),
                                          rho_hat_p16=float(m.rho_hat.quantile(0.16)), rho_hat_p84=float(m.rho_hat.quantile(0.84)),
                                          rho_hat_mean=float(m.rho_hat.mean()), lr0_median=float(m.lr0.median()),
                                          frac_rho_hat_as_extreme=float(np.mean(m.rho_hat >= real.rho_hat) if real.rho_hat >= 0
                                                                        else np.mean(m.rho_hat <= real.rho_hat)),
                                          n_at_edge=int(m.at_edge.sum())))
    with open(tables / f"e2_rhoscan_{args.mode}.json", "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=1), flush=True)


if __name__ == "__main__":
    main()
