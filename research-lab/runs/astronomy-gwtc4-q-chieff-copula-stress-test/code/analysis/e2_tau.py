#!/usr/bin/env python
"""E2 with the preregistered Kendall-tau statistic, computed like-for-like under several measures (D19, D21).

A "point estimate" (per-event median) depends on the measure the samples are weighted to. Real PE samples are
drawn under the PE prior pi_PE; mock samples are drawn under a prior flat in the internal coordinates
x = (ln m1, logit q, chi_eff, ln z) (stage 04). Each catalog's samples are reweighted from their native prior to a
common target measure M before taking medians, identically for the real catalog and every mock:

  post      pi_PE(theta)                 (real: native; mocks: pi_PE / pi_flatx)
  flattheta 1 (flat in m1, q, chi_eff, z)(real: 1 / pi_PE;    mocks: 1 / pi_flatx)
  flatx     pi_flatx = 1/(m1 q (1-q) z)  (real: pi_flatx/pi_PE; mocks: native)
  pop       p_pop, the null population the mocks were drawn from (copula_indep_plp posterior median)
                                         (real: p_pop / pi_PE;  mocks: p_pop / pi_flatx)

Non-unit weights are clipped at the kernel-bank quantile (mocks.kernel_weight_clip_quantile), the same rule for
real and mocks. For every measure: tau(q, chi_eff) of the medians, m1-partial tau, tau within the diagnostics'
m1 bins, and the number of events per m1 bin (a check that the mocks reproduce the observed point-estimate
distribution under that measure). Plus tau of the mock true / observed points.

Outputs: results/tables/e2_tau_full.csv (one row per catalog), results/tables/e2_tau_full.json.
Usage:   ../venv/bin/python analysis/e2_tau.py [--workers 16]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from multiprocessing import get_context
from pathlib import Path

os.environ.setdefault("JAX_PLATFORMS", "cpu")
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.stats import kendalltau  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from config import load_config  # noqa: E402
from io_utils import load_json, read_sample_table  # noqa: E402
from pe_priors import ChiEffPriorTable, ln_pe_prior  # noqa: E402

COLS = ("mass_1", "mass_ratio", "chi_eff", "redshift")
MEASURES = ("post", "flattheta", "flatx", "pop")
_G = {}


def wmedian(x, w):
    """Row-wise weighted median of x (N, K) with non-negative weights w (N, K)."""
    o = np.argsort(x, axis=1)
    xs, ws = np.take_along_axis(x, o, 1), np.take_along_axis(w, o, 1)
    c = np.cumsum(ws, axis=1)
    c /= c[:, -1:]
    i = np.minimum((c < 0.5).sum(axis=1), x.shape[1] - 1)
    return xs[np.arange(x.shape[0]), i]


def tau(x, y):
    return float(kendalltau(x, y).statistic)


def partial_tau(x, y, z):
    txy, txz, tyz = tau(x, y), tau(x, z), tau(y, z)
    return float((txy - txz * tyz) / np.sqrt(max((1 - txz**2) * (1 - tyz**2), 1e-12)))


def ln_flatx(m1, q, z):
    q = np.clip(q, 1e-6, 1 - 1e-6)
    return -np.log(m1) - np.log(q) - np.log1p(-q) - np.log(np.clip(z, 1e-6, None))


def clipped_weights(lw, clip_q):
    """exp(lw) normalised per event (row), clipped at the per-event quantile clip_q."""
    lw = lw - lw.max(axis=1, keepdims=True)
    w = np.exp(lw)
    if clip_q < 1:
        cap = np.quantile(w, clip_q, axis=1, keepdims=True)
        w = np.minimum(w, cap)
    return w


def ln_pop(m1, q, chi, z):
    import jax.numpy as jnp
    from jaxmodels import log_population
    d = {"mass_1": jnp.asarray(m1), "mass_ratio": jnp.asarray(q), "chi_eff": jnp.asarray(chi), "redshift": jnp.asarray(z)}
    return np.asarray(log_population(d, _G["pop_p"], _G["pop_spec"], _G["G"]))


def catalog_stats(m1, q, chi, z, ln_native, ln_pe, prefix_row):
    """m1, q, chi, z, ln_native, ln_pe: (N, K) arrays. Returns dict of statistics for all measures."""
    edges, clip_q = _G["edges"], _G["clip_q"]
    lnp = ln_pop(m1, q, chi, z)
    target = {"post": ln_pe, "flattheta": np.zeros_like(m1), "flatx": ln_flatx(m1, q, z), "pop": lnp}
    row = dict(prefix_row)
    for M in MEASURES:
        lw = target[M] - ln_native
        same = np.allclose(lw, lw[:, :1])                  # native measure: no reweighting
        w = np.ones_like(m1) if same else clipped_weights(lw, clip_q)
        mm1, mq, mchi = wmedian(m1, w), wmedian(q, w), wmedian(chi, w)
        row[f"tau_{M}"] = tau(mq, mchi)
        row[f"tau_{M}_partial_m1"] = partial_tau(mq, mchi, mm1)
        row[f"frac_m1ge40_{M}"] = float(np.mean(mm1 >= 40))
        for b in range(len(edges) - 1):
            sel = (mm1 >= edges[b]) & (mm1 < edges[b + 1])
            row[f"tau_{M}_bin{b}"] = tau(mq[sel], mchi[sel]) if sel.sum() >= 5 else np.nan
            row[f"n_{M}_bin{b}"] = int(sel.sum())
        row[f"ess_min_{M}"] = float(np.min(w.sum(1) ** 2 / (w**2).sum(1)))
    return row


def _init(cfg_path, mode):
    import jax
    jax.config.update("jax_enable_x64", True)
    import jax.numpy as jnp
    from jaxmodels import Grids, resolve_derived
    from models_registry import build_model
    cfg = load_config(mode=mode, config_path=cfg_path)
    s = cfg.raw["sample"]
    table = ChiEffPriorTable(0.99, cfg.path("processed_dir") / "chieff_prior_cache",
                             n_mc=int(s["chieff_prior_mc_samples"]), n_q=int(s["chieff_prior_q_grid"]),
                             n_chi=int(s["chieff_prior_chi_grid"]), seed=cfg.seed_for("chieff_prior"))
    _, meta = read_sample_table(cfg.sample_table_path())
    names = sorted(meta)                                    # == PEKernelBank.names ordering (stage 04)
    ref = load_json(cfg.fit_dir("copula_indep_plp") / "summary.json")
    spec, pnames, fixed, _ = build_model("copula_indep_plp", cfg)
    p = {n: ref["quantiles"][n]["median"] for n in pnames}
    p.update(fixed)
    _G.update(cfg=cfg, table=table, zprior=[meta[n]["redshift_prior"] for n in names],
              edges=np.asarray(cfg.raw["diagnostics"][f"mass_bin_edges_{mode}"], float),
              clip_q=float(cfg.raw["mocks"]["kernel_weight_clip_quantile"]),
              G=Grids(cfg, cfg.mode_value("mass_spline_nodes"), cfg.mode_value("marginal_spline_nodes")),
              pop_spec=spec, pop_p=resolve_derived({k: jnp.asarray(float(v)) for k, v in p.items()}, spec))


def _mock_row(task):
    import h5py
    rho, path, key = task
    table = _G["table"]
    with h5py.File(path, "r") as f:
        g = f[key]
        m1, q, chi, z = (np.asarray(g[c]) for c in COLS)
        ln_native = np.asarray(g["ln_prior"])
        kern = np.asarray(g["kernel_event"]).astype(int)
        true, obs = np.asarray(g["true"]), np.asarray(g["observed"])
    ln_pe = np.empty_like(m1)
    for e in range(m1.shape[0]):
        ln_pe[e] = ln_pe_prior(m1[e], q[e], z[e], chi[e], _G["zprior"][kern[e]], table)
    row = catalog_stats(m1, q, chi, z, ln_native, ln_pe, dict(kind="mock", rho_true=rho, mock=int(key.split("_")[1])))
    row["tau_true"] = tau(true[:, 1], true[:, 2])
    row["tau_obspt"] = tau(obs[:, 1], obs[:, 2])
    row["frac_m1ge40_true"] = float(np.mean(true[:, 0] >= 40))
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="full")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--config", default=str(HERE.parent / "config.yaml"))
    args = ap.parse_args()
    _init(args.config, args.mode)
    cfg = _G["cfg"]

    # ---- real catalog (common K = 4000 samples per event, drawn without replacement where possible) -------------
    posts, _ = read_sample_table(cfg.sample_table_path())
    names = sorted(posts)
    K = 4000
    rng = np.random.default_rng(20260925)
    arr = {c: np.empty((len(names), K)) for c in COLS + ("ln_prior",)}
    for i, n in enumerate(names):
        d = posts[n]
        idx = rng.choice(len(d), K, replace=len(d) < K)
        for c in COLS + ("ln_prior",):
            arr[c][i] = d[c].values[idx]
    real = catalog_stats(arr["mass_1"], arr["mass_ratio"], arr["chi_eff"], arr["redshift"], arr["ln_prior"],
                         arr["ln_prior"], dict(kind="real", rho_true=np.nan, mock=-1))
    print("real: " + ", ".join(f"tau_{M} = {real[f'tau_{M}']:+.4f}" for M in MEASURES)
          + " | frac m1>=40: " + ", ".join(f"{M} {real[f'frac_m1ge40_{M}']:.3f}" for M in MEASURES), flush=True)

    # ---- mock catalogs -----------------------------------------------------------------------------------------
    import h5py
    rhos = [0.0] + list(cfg.rho_true_grid)
    tasks = []
    for rho in rhos:
        path = cfg.mocks_path(rho)
        with h5py.File(path, "r") as f:
            tasks += [(rho, str(path), k) for k in sorted(k for k in f if k.startswith("mock_"))]
    print(f"{len(tasks)} mock catalogs over rho_true = {rhos}", flush=True)
    rows = [real]
    # 'spawn', not fork: the parent has already initialised JAX (real-catalog statistics), and forking a process
    # that holds JAX's threads deadlocks the workers
    with get_context("spawn").Pool(args.workers, initializer=_init, initargs=(args.config, args.mode)) as pool:
        for i, r in enumerate(pool.imap_unordered(_mock_row, tasks, chunksize=2)):
            rows.append(r)
            if (i + 1) % 40 == 0:
                print(f"  {i + 1}/{len(tasks)} done", flush=True)
    df = pd.DataFrame(rows).sort_values(["kind", "rho_true", "mock"])
    tables = cfg.path("tables_dir")
    df.to_csv(tables / f"e2_tau_{args.mode}.csv", index=False)

    # ---- summary: FPR, calibration curve, marginal check per measure --------------------------------------------
    out = {"n_events": len(names), "measures": list(MEASURES), "observed": {k: v for k, v in real.items()
                                                                            if k.startswith(("tau_", "frac_", "n_"))}, "stats": {}}
    for M in MEASURES:
        for stat in (f"tau_{M}", f"tau_{M}_partial_m1"):
            obs = real[stat]
            s = {"observed": obs, "curve": []}
            for rho in rhos:
                v = df[(df.kind == "mock") & np.isclose(df.rho_true, rho)][stat].dropna().values
                s["curve"].append(dict(rho_true=rho, n=int(len(v)), median=float(np.median(v)),
                                       p16=float(np.quantile(v, 0.16)), p84=float(np.quantile(v, 0.84)),
                                       p2p5=float(np.quantile(v, 0.025)), p97p5=float(np.quantile(v, 0.975)),
                                       frac_as_extreme=float(np.mean(v <= obs) if obs <= 0 else np.mean(v >= obs))))
            null = s["curve"][0]
            vnull = df[(df.kind == "mock") & (df.rho_true == 0.0)][stat].dropna().values
            s["fpr_one_sided"] = null["frac_as_extreme"]
            s["fpr_two_sided"] = float(np.mean(np.abs(vnull - np.median(vnull)) >= abs(obs - np.median(vnull))))
            cur = sorted(s["curve"], key=lambda r: r["rho_true"])
            xs, ys = np.array([r["rho_true"] for r in cur]), np.array([r["median"] for r in cur])
            o = np.argsort(ys)
            s["rho_true_matching_median"] = float(np.interp(obs, ys[o], xs[o])) if ys.min() <= obs <= ys.max() else None
            out["stats"][stat] = s
        v = df[(df.kind == "mock") & (df.rho_true == 0.0)][f"frac_m1ge40_{M}"].values
        out.setdefault("marginal_check_frac_m1ge40", {})[M] = dict(
            observed=real[f"frac_m1ge40_{M}"], null_median=float(np.median(v)), null_p2p5=float(np.quantile(v, 0.025)),
            null_p97p5=float(np.quantile(v, 0.975)), frac_null_ge_observed=float(np.mean(v >= real[f"frac_m1ge40_{M}"])))
    null = df[(df.kind == "mock") & (df.rho_true == 0.0)]
    out["null_diagnostics"] = {k: dict(median=float(null[k].median()), p16=float(null[k].quantile(0.16)),
                                       p84=float(null[k].quantile(0.84)))
                               for k in ("tau_true", "tau_obspt", "frac_m1ge40_true") + tuple(f"tau_{M}" for M in MEASURES)}
    with open(tables / f"e2_tau_{args.mode}.json", "w") as f:
        json.dump(out, f, indent=2)
    for M in MEASURES:
        s = out["stats"][f"tau_{M}"]
        mc = out["marginal_check_frac_m1ge40"][M]
        print(f"tau_{M:<10} observed {s['observed']:+.4f} | null median {s['curve'][0]['median']:+.4f} "
              f"[{s['curve'][0]['p2p5']:+.4f}, {s['curve'][0]['p97p5']:+.4f}] (95%) | FPR one-sided {s['fpr_one_sided']:.3f} "
              f"two-sided {s['fpr_two_sided']:.3f} | rho_true at median {s['rho_true_matching_median']} || frac m1>=40: "
              f"observed {mc['observed']:.3f} vs null {mc['null_median']:.3f} [{mc['null_p2p5']:.3f}, {mc['null_p97p5']:.3f}]")
    print("null diagnostics:", json.dumps(out["null_diagnostics"]))


if __name__ == "__main__":
    main()
