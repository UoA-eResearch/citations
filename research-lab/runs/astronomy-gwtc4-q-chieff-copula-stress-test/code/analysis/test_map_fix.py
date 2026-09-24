#!/usr/bin/env python
"""Validate the D20 MAP fitter on the real catalog and null mocks 0-1 (CPU)."""
import os, sys, time
from pathlib import Path
os.environ.setdefault("JAX_PLATFORMS", "cpu")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
import h5py, jax, numpy as np
jax.config.update("jax_enable_x64", True)
from config import load_config
from fit_models import load_event_arrays
from io_utils import load_json, read_injection_table
from jaxmodels import Grids
from mock_stats import MAPFitter, map_statistics, kendall_medians, COLS
cfg = load_config(mode="full", config_path=str(HERE.parent / "config.yaml"))
G = Grids(cfg, cfg.mode_value("mass_spline_nodes"), cfg.mode_value("marginal_spline_nodes"))
inj_full = read_injection_table(cfg.injection_table_path())
idx = np.sort(cfg.rng("map_inj_sub").choice(len(inj_full["mass_1"]), int(cfg.mode_value("map_injection_subsample", 150000)), replace=False))
inj = {**{k: inj_full[k][idx] for k in COLS + ("ln_prior",)}, "total_generated": inj_full["total_generated"] * len(idx) / len(inj_full["mass_1"])}
g = load_json(cfg.fit_dir("copula_gauss_plp") / "summary.json"); i_ = load_json(cfg.fit_dir("copula_indep_plp") / "summary.json")
th_g = np.array([g["quantiles"][n]["median"] for n in g["names"]]); th_i = np.array([i_["quantiles"][n]["median"] for n in i_["names"]])
fitter = MAPFitter(cfg, G)
cats = []
ev_real, _, _ = load_event_arrays(cfg, cfg.rng("fit_subsample"), max_samples=2000)
cats.append(("real", ev_real))
which = [int(a) for a in (sys.argv[1:] or ["0", "1"])]
with h5py.File(cfg.mocks_path(0.0), "r") as f:
    for m in which:
        gg = f[f"mock_{m:04d}"]; ev = {c: np.asarray(gg[c]) for c in COLS}; ev["ln_prior"] = np.asarray(gg["ln_prior"])
        cats.append((f"null mock {m}", ev))
for label, ev in cats:
    t = time.time(); st = map_statistics(fitter, ev, inj, th_g, th_i)
    print(f"{label:<12} tau(post-medians)={kendall_medians(ev)[0]:+.3f} rho_MAP={st['rho_map']:+.3f} (alt start {st['rho_map_alt']:+.3f}, "
          f"obj gap {st['obj_gap_alt']:+.3f}, used {st['start_used']}) LR={st['lr_stat']:.3f} ok={st['map_ok']} "
          f"nfev={st['map_nfev']} lnL g/i={st['lnl_gauss']:.2f}/{st['lnl_indep']:.2f} ({time.time()-t:.0f}s)", flush=True)
