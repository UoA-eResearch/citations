#!/usr/bin/env python
"""Self-consistency of the fitted populations (2026-09-25): population-informed event posteriors vs the
predicted detected distribution, for the primary mass (fraction >= 40 Msun) and a few other marginals.
For a well-specified fit the two agree; a gap points at the selection term or the Monte Carlo variance cut."""
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
rng = np.random.default_rng(2)
sub = rng.choice(len(inj["mass_1"]), 300000, replace=False)
di = {k: jnp.asarray(inj[k][sub]) for k in ("mass_1", "mass_ratio", "chi_eff", "redshift")}
posts, meta = read_sample_table(cfg.sample_table_path())
names_ev = sorted(posts)
comp = inj.get("component")
def run(model):
    s = load_json(cfg.fit_dir(model) / "summary.json")
    spec, names, fixed, _ = build_model(model, cfg)
    p = {n: s["quantiles"][n]["median"] for n in names}; p.update(fixed)
    p = resolve_derived({k: jnp.asarray(float(v)) for k, v in p.items()}, spec)
    # predicted detected
    lw = np.asarray(log_population(di, p, spec, G)) - inj["ln_prior"][sub]
    w = np.exp(lw - lw.max()); w /= w.sum()
    pred = {"m1>=40": float(w[inj["mass_1"][sub] >= 40].sum()), "z>=0.5": float(w[inj["redshift"][sub] >= 0.5].sum()),
            "q<0.6": float(w[inj["mass_ratio"][sub] < 0.6].sum())}
    # population-informed event posteriors (median per event)
    ev_m1, ev_z, ev_q = [], [], []
    for n in names_ev:
        d = posts[n]
        dd = {k: jnp.asarray(d[k].values) for k in ("mass_1", "mass_ratio", "chi_eff", "redshift")}
        lwe = np.asarray(log_population(dd, p, spec, G)) - d["ln_prior"].values
        we = np.exp(lwe - lwe.max()); we /= we.sum()
        for arr, out in ((d["mass_1"].values, ev_m1), (d["redshift"].values, ev_z), (d["mass_ratio"].values, ev_q)):
            o = np.argsort(arr); out.append(np.interp(0.5, np.cumsum(we[o]), arr[o]))
    ev_m1, ev_z, ev_q = map(np.array, (ev_m1, ev_z, ev_q))
    obs = {"m1>=40": float(np.mean(ev_m1 >= 40)), "z>=0.5": float(np.mean(ev_z >= 0.5)), "q<0.6": float(np.mean(ev_q < 0.6))}
    print(f"{model:<22}" + "  ".join(f"{k}: predicted {pred[k]:.3f} vs pop-informed events {obs[k]:.3f}" for k in pred), flush=True)
    return {"predicted": pred, "population_informed_events": obs}
out = {m: run(m) for m in (sys.argv[1:] or ["baseline_plp_null", "lvk_bpl2p_null", "baseline_splm1_null"])}
# per-run-component view of the injections: found counts and detected-weight share at the lvk_bpl2p_null median
if comp is not None:
    c = np.asarray(comp)[sub]
    print("injection components in the subsample:", {str(u): int((c == u).sum()) for u in np.unique(c)})
json.dump(out, open(HERE.parent.parent / "results" / "tables" / "ppc_selfconsistency_full.json", "w"), indent=2)
