#!/usr/bin/env python
"""Posterior-predictive check of the detected primary-mass distribution (2026-09-25).
Fraction of detected BBHs with m1 >= 40 Msun (and the 50/90% detected-m1 quantiles) predicted by
(a) each model's posterior-median hyperparameters and (b) its posterior predictive (100 equal-weight draws),
versus the observed fraction. CPU, 300k-injection subsample."""
import os, sys, json
from pathlib import Path
os.environ.setdefault("JAX_PLATFORMS", "cpu")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
import jax, numpy as np, jax.numpy as jnp
jax.config.update("jax_enable_x64", True)
from config import load_config
from io_utils import load_json, read_injection_table, read_sample_table
from jaxmodels import Grids, log_population, resolve_derived
from models_registry import build_model
cfg = load_config(mode="full", config_path=str(HERE.parent / "config.yaml"))
G = Grids(cfg, cfg.mode_value("mass_spline_nodes"), cfg.mode_value("marginal_spline_nodes"))
inj = read_injection_table(cfg.injection_table_path())
rng = np.random.default_rng(1)
sub = rng.choice(len(inj["mass_1"]), 300000, replace=False)
d = {k: jnp.asarray(inj[k][sub]) for k in ("mass_1", "mass_ratio", "chi_eff", "redshift")}
lnp_draw = inj["ln_prior"][sub]
m1 = inj["mass_1"][sub]
posts, _ = read_sample_table(cfg.sample_table_path())
obs_m1 = np.array([np.median(p["mass_1"]) for p in posts.values()])
print(f"observed (posterior medians): frac m1>=40 = {np.mean(obs_m1 >= 40):.3f}; m1 50/90% = {np.percentile(obs_m1, 50):.1f}/{np.percentile(obs_m1, 90):.1f}")
out = {"observed_frac_ge40": float(np.mean(obs_m1 >= 40))}
def detected(model, params):
    spec, names, fixed, _ = build_model(model, cfg)
    p = dict(params); p.update(fixed)
    p = resolve_derived({k: jnp.asarray(float(v)) for k, v in p.items()}, spec)
    lw = np.asarray(log_population(d, p, spec, G)) - lnp_draw
    w = np.exp(lw - lw.max()); w /= w.sum()
    o = np.argsort(m1); c = np.cumsum(w[o])
    return float(w[m1 >= 40].sum()), float(np.interp(0.5, c, m1[o])), float(np.interp(0.9, c, m1[o]))
for model in sys.argv[1:] or ["copula_indep_plp", "baseline_plp_null", "lvk_bpl2p_null", "baseline_splm1_null"]:
    fd = cfg.fit_dir(model)
    if not (fd / "summary.json").exists():
        continue
    s = load_json(fd / "summary.json"); post = np.load(fd / "posterior.npz", allow_pickle=True)
    names = [str(n) for n in post["names"]]
    f_med, q50, q90 = detected(model, {n: s["quantiles"][n]["median"] for n in names})
    draws = post["samples"][rng.choice(len(post["samples"]), 100, replace=False)]
    fr = np.array([detected(model, dict(zip(names, x)))[0] for x in draws])
    print(f"{model:<22} posterior-median params: frac>=40 {f_med:.3f} (m1 50/90% {q50:.1f}/{q90:.1f}) | "
          f"posterior predictive: {np.median(fr):.3f} [{np.percentile(fr, 5):.3f}, {np.percentile(fr, 95):.3f}]  (lnZ {s['log_z']:.2f})", flush=True)
    out[model] = dict(frac_median_params=f_med, m1_q50=q50, m1_q90=q90, frac_pp_median=float(np.median(fr)),
                      frac_pp_p5=float(np.percentile(fr, 5)), frac_pp_p95=float(np.percentile(fr, 95)))
json.dump(out, open(HERE.parent.parent / "results" / "tables" / "ppc_mass_full.json", "w"), indent=2)
