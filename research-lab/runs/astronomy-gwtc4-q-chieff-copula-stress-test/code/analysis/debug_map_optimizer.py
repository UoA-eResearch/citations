#!/usr/bin/env python
"""Trace the L-BFGS-B call of stage-05 MAPFitter on null mock 0 (copula_gauss_plp), logging every
function evaluation, to find why it stops at theta0 after ~3 evaluations. CPU by default."""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

os.environ.setdefault("JAX_PLATFORMS", "cpu")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

import h5py  # noqa: E402
import jax  # noqa: E402
import numpy as np  # noqa: E402
from scipy.optimize import minimize  # noqa: E402

jax.config.update("jax_enable_x64", True)
from config import load_config  # noqa: E402
from io_utils import load_json, read_injection_table  # noqa: E402
from jaxmodels import Grids, HierarchicalLikelihood  # noqa: E402
from models_registry import build_model  # noqa: E402

COLS = ("mass_1", "mass_ratio", "chi_eff", "redshift")
model = sys.argv[1] if len(sys.argv) > 1 else "copula_gauss_plp"
cfg = load_config(mode="full", config_path=str(HERE.parent / "config.yaml"))
G = Grids(cfg, cfg.mode_value("mass_spline_nodes"), cfg.mode_value("marginal_spline_nodes"))
inj_full = read_injection_table(cfg.injection_table_path())
idx = np.sort(cfg.rng("map_inj_sub").choice(len(inj_full["mass_1"]), int(cfg.mode_value("map_injection_subsample", 150000)), replace=False))
inj = {**{k: inj_full[k][idx] for k in COLS + ("ln_prior",)},
       "total_generated": inj_full["total_generated"] * len(idx) / len(inj_full["mass_1"])}
with h5py.File(cfg.mocks_path(0.0), "r") as f:
    g = f["mock_0000"]
    ev = {c: np.asarray(g[c]) for c in COLS}
    ev["ln_prior"] = np.asarray(g["ln_prior"])

s = load_json(cfg.fit_dir(model) / "summary.json")
spec, names, fixed, prior = build_model(model, cfg)
theta0 = np.array([s["quantiles"][n]["median"] for n in s["names"]])
lik = HierarchicalLikelihood(spec, names, fixed, ev, inj, G, max_variance=1e9, enforce_injection_convergence=False,
                             cache_key=f"trace_{model}", gradient_mode="forward")
vg = lik.soft_value_and_grad()
groups = [np.array(v) for v in prior.groups.values()]
log = []


def f(x):
    t = time.time()
    v, gr = vg(x)
    lp, glp = 0.0, np.zeros_like(gr)
    for idxs in groups:
        vals = x[idxs]
        lp -= 0.5 * (vals[0] / prior.s_first) ** 2 + 0.5 * np.sum((np.diff(vals) / prior.s_step) ** 2)
        d = np.diff(vals) / prior.s_step**2
        glp[idxs[0]] -= vals[0] / prior.s_first**2
        glp[idxs[:-1]] += d
        glp[idxs[1:]] -= d
    fin = np.isfinite(v)
    val = -(v + lp) if fin else 1e30
    grad = -(gr + glp) if fin else np.zeros_like(gr)
    dx = x - theta0
    log.append((val, v, lp, np.linalg.norm(dx), np.isfinite(gr).all()))
    big = np.argsort(-np.abs(dx))[:4]
    print(f"eval {len(log):3d}: f={val:.6g} lnL={v:.4f} lp={lp:.3f} |dx|={np.linalg.norm(dx):.3g} "
          f"|grad|={np.linalg.norm(grad):.3g} ({time.time() - t:.1f}s)  top moves: "
          + ", ".join(f"{names[i]}{dx[i]:+.3g}" for i in big), flush=True)
    return val, grad


bounds = [(lo + 1e-6 * (hi - lo), hi - 1e-6 * (hi - lo)) if k == "uniform" else (-25.0, 25.0)
          for lo, hi, k in zip(prior.lo, prior.hi, prior.kind)]
x0 = np.clip(theta0, [b[0] for b in bounds], [b[1] for b in bounds])
print("x0 clipped differs from theta0 in:", [names[i] for i in np.where(x0 != theta0)[0]])
print("params at bounds (within 1e-3 of the box):",
      [names[i] for i, (b, x) in enumerate(zip(bounds, x0)) if min(x - b[0], b[1] - x) < 1e-3 * (b[1] - b[0])])
res = minimize(f, x0, jac=True, method="L-BFGS-B", bounds=bounds, options={"maxiter": int(os.environ.get("MAXITER", 60))})
print("\nRESULT:", res.message, "| success", res.success, "| nit", res.nit, "| nfev", res.nfev)
print("rho:", theta0[names.index("gaussian_copula_rho")] if "gaussian_copula_rho" in names else None, "->",
      res.x[names.index("gaussian_copula_rho")] if "gaussian_copula_rho" in names else None)
print("final lnL:", vg(res.x)[0])
