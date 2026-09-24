#!/usr/bin/env python
"""Diagnose the stage-05 MAP failure on mock catalogs (2026-09-25, task: rho_MAP stuck at theta0).

Evaluates ln L_soft and its gradient at the stage-05 starting points (posterior medians of the real-data
copula fits) on the real catalog and on null mock 0, for both copula models, and runs the same L-BFGS-B
call as MAPFitter with verbose output. CPU only.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("JAX_PLATFORMS", "cpu")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

import h5py  # noqa: E402
import jax  # noqa: E402
import numpy as np  # noqa: E402

jax.config.update("jax_enable_x64", True)
from config import load_config  # noqa: E402
from fit_models import load_event_arrays  # noqa: E402
from io_utils import load_json, read_injection_table  # noqa: E402
from jaxmodels import Grids, HierarchicalLikelihood  # noqa: E402
from models_registry import build_model  # noqa: E402

COLS = ("mass_1", "mass_ratio", "chi_eff", "redshift")
cfg = load_config(mode="full", config_path=str(HERE.parent / "config.yaml"))
G = Grids(cfg, cfg.mode_value("mass_spline_nodes"), cfg.mode_value("marginal_spline_nodes"))
ev_real, names_ev, _ = load_event_arrays(cfg, cfg.rng("fit_subsample"), max_samples=2000)
inj_full = read_injection_table(cfg.injection_table_path())
sub = int(cfg.mode_value("map_injection_subsample", 150000))
idx = np.sort(cfg.rng("map_inj_sub").choice(len(inj_full["mass_1"]), sub, replace=False))
inj = {**{k: inj_full[k][idx] for k in COLS + ("ln_prior",)},
       "total_generated": inj_full["total_generated"] * len(idx) / len(inj_full["mass_1"])}
with h5py.File(cfg.mocks_path(0.0), "r") as f:
    g = f["mock_0000"]
    ev_mock = {c: np.asarray(g[c]) for c in COLS}
    ev_mock["ln_prior"] = np.asarray(g["ln_prior"])

print("real ev shapes", {k: np.shape(v) for k, v in ev_real.items()}, "| mock", {k: v.shape for k, v in ev_mock.items()})
for k in COLS + ("ln_prior",):
    x = ev_mock[k]
    print(f"mock {k:<10} finite {np.isfinite(x).mean():.4f}  min {np.nanmin(x):.4g}  max {np.nanmax(x):.4g}")
print("mock chi_eff |x|>1 fraction:", float(np.mean(np.abs(ev_mock['chi_eff']) > 1)),
      "| q>=1:", float(np.mean(ev_mock['mass_ratio'] >= 1)), "| q<0.05:", float(np.mean(ev_mock['mass_ratio'] < 0.05)))

for model in ("copula_gauss_plp", "copula_indep_plp"):
    s = load_json(cfg.fit_dir(model) / "summary.json")
    spec, pnames, fixed, prior = build_model(model, cfg)
    theta0 = np.array([s["quantiles"][n]["median"] for n in s["names"]])
    for label, ev in (("real", ev_real), ("mock0", ev_mock)):
        lik = HierarchicalLikelihood(spec, pnames, fixed, ev, inj, G, max_variance=1e9,
                                     enforce_injection_convergence=False, cache_key=f"dbg_{model}",
                                     gradient_mode="forward")
        vg = lik.soft_value_and_grad()
        v, gr = vg(theta0)
        # per-event contributions: which events are non-finite / extreme?
        import jax.numpy as jnp
        p = lik.unpack(jnp.asarray(theta0))
        lnL_i, var_i = lik.per_event_data(p, lik.ev)
        lnL_i, var_i = np.asarray(lnL_i), np.asarray(var_i)
        print(f"\n[{model} | {label}] ln L_soft = {v:.3f} finite={np.isfinite(v)}; grad finite={np.isfinite(gr).all()} "
              f"|grad|={np.linalg.norm(gr[np.isfinite(gr)]):.3g}; n non-finite grad comps={int((~np.isfinite(gr)).sum())}")
        print(f"   per-event lnL_i: min {np.nanmin(lnL_i):.3g} (event {int(np.nanargmin(lnL_i))}), "
              f"non-finite {int((~np.isfinite(lnL_i)).sum())}; var_i max {np.nanmax(var_i):.3g}")
        if not np.isfinite(gr).all():
            bad = [pnames[i] for i in np.where(~np.isfinite(gr))[0]]
            print("   non-finite gradient components:", bad[:12])
