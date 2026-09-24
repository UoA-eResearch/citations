#!/usr/bin/env python
"""D27 validation: do the mock catalogs look like the real catalog? Real vs stage-04 (v1) vs rebuilt (v2) null mocks.

Per catalog, under the flat-internal measure (the measure mock samples are drawn under; real samples reweighted by
pi_flatx / pi_PE):
  q09   per-event likelihood mass at q > 0.9 -> catalog median, and fraction of events with > 50%
  wq    per-event 90% width of q -> catalog median
  wchi  per-event 90% width of chi_eff -> catalog median
and var_tot (total Monte Carlo variance of the hierarchical log-likelihood, 2000 samples per event, all injections) of
copula_indep_plp at a plausible population: for the real catalog at 20 posterior draws, for each mock at its own
generating population (v2) or at the posterior median (v1).

Output: results/tables/mock_validation_full.json (+ printed table)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("JAX_PLATFORMS", "cpu")
import h5py  # noqa: E402
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
import jax  # noqa: E402

jax.config.update("jax_enable_x64", True)
from config import load_config  # noqa: E402
from fit_models import load_event_arrays  # noqa: E402
from io_utils import load_json, read_injection_table  # noqa: E402
from jaxmodels import Grids, HierarchicalLikelihood  # noqa: E402
from mock_catalogs import ln_flat_internal_prior  # noqa: E402
from models_registry import build_model  # noqa: E402

COLS = ("mass_1", "mass_ratio", "chi_eff", "redshift")
N_MOCK = int(os.environ.get("N_MOCK", 30))


def wq(x, w, qs):
    o = np.argsort(x, axis=1)
    xs, ws = np.take_along_axis(x, o, 1), np.take_along_axis(w, o, 1)
    c = np.cumsum(ws, 1)
    c /= c[:, -1:]
    return [xs[np.arange(len(x)), np.minimum((c < qq).sum(1), x.shape[1] - 1)] for qq in qs]


def shape_stats(ev, native_is_flatx=None):
    # reweight every catalog from its own stored prior (ln_prior column) to the flat-internal measure
    m1, q, chi, z, lp = (ev[c] for c in COLS + ("ln_prior",))
    lw = ln_flat_internal_prior(m1, q, chi, z) - lp
    if np.allclose(lw, lw[:, :1]):
        w = np.ones_like(m1)
    else:
        w = np.exp(lw - lw.max(axis=1, keepdims=True))
        w = np.minimum(w, np.quantile(w, 0.999, axis=1, keepdims=True))
    w = w / w.sum(axis=1, keepdims=True)
    q09 = (w * (q > 0.9)).sum(axis=1)
    q5, q95 = wq(q, w, (0.05, 0.95))
    c5, c95 = wq(chi, w, (0.05, 0.95))
    return dict(q09_median=float(np.median(q09)), q09_frac_gt_half=float(np.mean(q09 > 0.5)),
                wq_median=float(np.median(q95 - q5)), wchi_median=float(np.median(c95 - c5)))


def main():
    cfg = load_config(mode="full", config_path=str(HERE.parent / "config.yaml"))
    G = Grids(cfg, cfg.mode_value("mass_spline_nodes"), cfg.mode_value("marginal_spline_nodes"))
    inj = read_injection_table(cfg.injection_table_path())
    spec, names, fixed, _ = build_model("copula_indep_plp", cfg)
    post = np.load(cfg.fit_dir("copula_indep_plp") / "posterior.npz", allow_pickle=True)
    pnames = [str(x) for x in post["names"]]
    med = load_json(cfg.fit_dir("copula_indep_plp") / "summary.json")["quantiles"]
    theta_med = np.array([med[n]["median"] for n in names])
    rng = np.random.default_rng(7)

    def var_tot(ev, thetas):
        lik = HierarchicalLikelihood(spec, names, fixed, ev, inj, G, max_variance=1e12,
                                     enforce_injection_convergence=False, cache_key="validate")
        _, aux = lik.make_batched_aux(4)(np.atleast_2d(thetas))
        return aux["var_tot"]

    out = {}
    ev_real, _, _ = load_event_arrays(cfg, cfg.rng("fit_subsample"), max_samples=2000)
    draws = post["samples"][rng.choice(len(post["samples"]), 20, replace=False)]
    th = np.array([[d[pnames.index(n)] for n in names] for d in draws])
    vt = var_tot(ev_real, th)
    out["real"] = dict(**shape_stats(ev_real, False), var_tot_median=float(np.median(vt)),
                       var_tot_p16=float(np.quantile(vt, 0.16)), var_tot_p84=float(np.quantile(vt, 0.84)),
                       var_tot_at_median=float(var_tot(ev_real, theta_med)[0]))
    print("real   ", out["real"], flush=True)
    sets = [(lab, cfg.mocks_path(0.0) if lab == "v1" else cfg.path("mocks_dir") / lab / "mocks_full_rho+0.00.h5")
            for lab in os.environ.get("SETS", "v1,v2,v3").split(",")]
    for label, path in sets:
        if not path.exists():
            continue
        rows = []
        with h5py.File(path, "r") as f:
            keys = sorted(k for k in f if k.startswith("mock_"))[:N_MOCK]
            for k in keys:
                g = f[k]
                ev = {c: np.asarray(g[c]) for c in COLS}
                ev["ln_prior"] = np.asarray(g["ln_prior"])
                st = shape_stats(ev)
                if "params" in g.attrs:
                    p = json.loads(g.attrs["params"])
                    theta = np.array([p[n] for n in names])
                else:
                    theta = theta_med
                st["var_tot"] = float(var_tot(ev, theta)[0])
                rows.append(st)
        agg = {k: float(np.median([r[k] for r in rows])) for k in rows[0]}
        agg.update(var_tot_p16=float(np.quantile([r["var_tot"] for r in rows], 0.16)),
                   var_tot_p84=float(np.quantile([r["var_tot"] for r in rows], 0.84)), n=len(rows))
        out[label] = agg
        print(f"mocks {label}", agg, flush=True)
    prev = cfg.path("tables_dir") / "mock_validation_full.json"
    old = json.load(open(prev)) if prev.exists() else {}
    old.update(out)
    json.dump(old, open(prev, "w"), indent=2)


if __name__ == "__main__":
    main()
