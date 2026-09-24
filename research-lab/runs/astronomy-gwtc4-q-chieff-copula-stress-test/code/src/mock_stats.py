#!/usr/bin/env python
"""Stage 05: correlation statistics on the real data and on every mock, and
the E2 false-positive rate / calibration curve.

Statistics (plan sec 4.5: two different summaries so the FPR is not an
artifact of the statistic choice):
  A. Kendall's tau of per-event posterior medians (q, chi_eff);
  B. rho_hat: MAP of the Gaussian-copula dependence parameter with all other
     hyperparameters re-optimized on the same catalog (MAP under the hyper-
     prior, L-BFGS-B with jax gradients), plus the profile log-likelihood
     ratio 2[lnL(rho_hat) - lnL(rho=0)] (rho=0 re-optimized);
  C. (subset of n_mock_full_refits rho=0 mocks) full nautilus refits of the
     dependence and independence models -> mock ln BF, for the hierarchical-
     posterior version of the statistic.
FPR = fraction of rho_true=0 mocks whose statistic is at least as extreme
(same sign) as the real-data value. Calibration curve = the same fraction
for every rho_true in the grid.

The stage is resumable at the level of individual mocks: finished rows are
appended to results/tables/mock_stats_<mode>_partial.csv and reloaded.
Outputs: results/tables/mock_stats_<mode>.csv, fpr_<mode>.json
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import kendalltau

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import add_common_args, load_config, setup_logging  # noqa: E402
from fit_models import load_event_arrays, run_nautilus  # noqa: E402
from gpu import GPUSession  # noqa: E402
from io_utils import load_json, read_injection_table, save_json  # noqa: E402
from models_registry import build_model  # noqa: E402

COLS = ("mass_1", "mass_ratio", "chi_eff", "redshift")
MAP_MODELS = ("copula_gauss_plp", "copula_indep_plp")


def kendall_medians(ev):
    qm = np.median(ev["mass_ratio"], axis=1)
    cm = np.median(ev["chi_eff"], axis=1)
    tau, p = kendalltau(qm, cm)
    return float(tau), float(p)


class MAPFitter:
    """MAP fits of the two copula models. The compiled value-and-gradient of
    ln L_soft is cached per (model, data shape) inside HierarchicalLikelihood,
    so every mock with the same (N, K, M) shapes reuses one compilation.

    D20 (2026-09-25): the optimiser works in scaled variables z = (x - x0) / scale, with scale = half the 68%
    width of the real-data posterior of each hyperparameter, and treats values contaminated by the model's
    "log zero" sentinel (NEG = -1e300, finite) as invalid. Unscaled, the first L-BFGS-B trial step on the mocks
    moved |dx| ~ 15 into the sentinel region (ln L ~ -2e300, finite), the line search collapsed and scipy
    reported convergence at x0 -- every mock returned rho_MAP = x0."""

    INVALID_LNL = -1e8

    def __init__(self, cfg, G):
        self.cfg, self.G = cfg, G
        self.specs = {name: build_model(name, cfg) for name in MAP_MODELS}
        self.scales = {}
        for name in MAP_MODELS:
            summ = load_json(cfg.fit_dir(name) / "summary.json")
            _, names, _, prior = self.specs[name]
            sc = []
            for i, n in enumerate(names):
                q = summ["quantiles"][n]
                span = (prior.hi[i] - prior.lo[i]) if prior.kind[i] == "uniform" else 50.0
                sc.append(max(0.5 * (q["p84"] - q["p16"]), 1e-3 * span))
            self.scales[name] = np.asarray(sc, float)

    def fit(self, name, ev, inj, theta0):
        """Returns dict(params, x, lnl, obj, ok, nfev, message); obj = ln L_soft + ln(spline hyper-prior)."""
        from jaxmodels import HierarchicalLikelihood
        spec, names, fixed, prior = self.specs[name]
        lik = HierarchicalLikelihood(spec, names, fixed, ev, inj, self.G, max_variance=1e9,
                                     enforce_injection_convergence=False, cache_key=f"map_{name}",
                                     gradient_mode=self.cfg.raw["likelihood"].get("gradient_mode", "auto"))
        vg = lik.soft_value_and_grad()
        s_first, s_step = prior.s_first, prior.s_step
        groups = [np.array(v) for v in prior.groups.values()]

        def log_hyper(x):
            lp, glp = 0.0, np.zeros_like(x)
            for idxs in groups:                      # Gaussian random-walk hyper-prior on the spline nodes
                vals = x[idxs]
                lp -= 0.5 * (vals[0] / s_first) ** 2 + 0.5 * np.sum((np.diff(vals) / s_step) ** 2)
                d = np.diff(vals) / s_step**2
                glp[idxs[0]] -= vals[0] / s_first**2
                glp[idxs[:-1]] += d
                glp[idxs[1:]] -= d
            return lp, glp

        bounds = np.array([(lo + 1e-6 * (hi - lo), hi - 1e-6 * (hi - lo)) if k == "uniform" else (-25.0, 25.0)
                           for lo, hi, k in zip(prior.lo, prior.hi, prior.kind)])
        x0 = np.clip(np.asarray(theta0, float), bounds[:, 0], bounds[:, 1])
        scale = self.scales[name]

        def f(z):
            x = x0 + z * scale
            v, g = vg(x)
            if not np.isfinite(v) or v < self.INVALID_LNL or not np.all(np.isfinite(g)):
                return 1e30, np.zeros_like(z)
            lp, glp = log_hyper(x)
            return -(v + lp), -(g + glp) * scale

        zb = [((b0 - a) / c, (b1 - a) / c) for (b0, b1), a, c in zip(bounds, x0, scale)]
        res = minimize(f, np.zeros_like(x0), jac=True, method="L-BFGS-B", bounds=zb, options={"maxiter": 1000})
        x = x0 + res.x * scale
        lnl = float(vg(x)[0])
        obj = lnl + log_hyper(x)[0]
        ok = bool(res.success) and np.isfinite(lnl) and lnl > self.INVALID_LNL
        return dict(params=dict(zip(names, x)), x=x, lnl=lnl, obj=float(obj), ok=ok, nfev=int(res.nfev),
                    message=str(res.message))


def map_statistics(fitter, ev, inj, theta0_gauss, theta0_indep, logger=None):
    """rho_MAP and the (hyper-prior-penalised) profile likelihood-ratio statistic for one catalog.

    D20: the independence model is fitted first; the Gaussian-copula model is then fitted from two starts --
    the independence optimum with rho = 0 (so that LR >= 0 up to optimiser tolerance, since the copula model
    nests independence at rho = 0) and the real-data posterior median -- and the better optimum is kept."""
    fi = fitter.fit("copula_indep_plp", ev, inj, theta0_indep)
    names_g = fitter.specs["copula_gauss_plp"][1]
    nested = np.array([fi["params"].get(n, 0.0) for n in names_g])      # rho = 0, all else at the indep optimum
    starts = [fitter.fit("copula_gauss_plp", ev, inj, nested), fitter.fit("copula_gauss_plp", ev, inj, theta0_gauss)]
    fg = max(starts, key=lambda r: r["obj"] if r["ok"] else -np.inf)
    alt = starts[1] if fg is starts[0] else starts[0]
    lr = float(2 * (fg["obj"] - fi["obj"]))
    if lr < -0.1 and logger is not None:
        logger.warning("penalised profile LR = %.3f < 0 (indep ok=%s nfev=%d; gauss ok=%s nfev=%d: %s)", lr,
                       fi["ok"], fi["nfev"], fg["ok"], fg["nfev"], fg["message"])
    return dict(rho_map=float(fg["params"]["gaussian_copula_rho"]), lr_stat=lr, map_ok=bool(fi["ok"] and fg["ok"]),
                map_nfev=int(fi["nfev"] + starts[0]["nfev"] + starts[1]["nfev"]), lnl_gauss=float(fg["lnl"]),
                lnl_indep=float(fi["lnl"]), rho_map_alt=float(alt["params"]["gaussian_copula_rho"]),
                obj_gap_alt=float(fg["obj"] - alt["obj"]), start_used="nested" if fg is starts[0] else "theta0")


def extreme_fraction(stat_mock, stat_obs):
    """Fraction of mocks at least as extreme as the observation, in the observed direction."""
    stat_mock = np.asarray(stat_mock, float)
    stat_mock = stat_mock[np.isfinite(stat_mock)]
    if len(stat_mock) == 0 or not np.isfinite(stat_obs):
        return np.nan
    if stat_obs <= 0:
        return float(np.mean(stat_mock <= stat_obs))
    return float(np.mean(stat_mock >= stat_obs))


def summarize(df, rhos, csv_path, fpr_path, logger):
    df.to_csv(csv_path, index=False)
    mocks0 = df[(df.kind == "mock") & (df.rho_true == 0.0)]
    real = df[df.kind == "real"].iloc[0]
    fpr = {
        "n_mocks_rho0": int(len(mocks0)),
        "tau_obs": float(real["tau"]), "rho_map_obs": float(real["rho_map"]), "lr_obs": float(real["lr_stat"]),
        "ln_bf_dep_obs": float(real["ln_bf_dep"]),
        "fpr_tau": extreme_fraction(mocks0["tau"], real["tau"]),
        "fpr_rho_map": extreme_fraction(mocks0["rho_map"], real["rho_map"]),
        "fpr_lr": float(np.mean(mocks0["lr_stat"] >= real["lr_stat"])) if len(mocks0) else np.nan,
        "fpr_tau_two_sided": float(np.mean(np.abs(mocks0["tau"]) >= abs(real["tau"]))) if len(mocks0) else np.nan,
        "mock_ln_bf_dep_rho0": [float(x) for x in mocks0["ln_bf_dep"].dropna()],
        "calibration_curve": [],
    }
    for rho in rhos:
        m = df[(df.kind == "mock") & (df.rho_true == rho)]
        if not len(m):
            continue
        fpr["calibration_curve"].append(dict(
            rho_true=rho, n=int(len(m)), frac_tau_as_extreme=extreme_fraction(m["tau"], real["tau"]),
            frac_rho_map_as_extreme=extreme_fraction(m["rho_map"], real["rho_map"]),
            tau_median=float(m["tau"].median()), rho_map_median=float(m["rho_map"].median()),
            tau_p16=float(m["tau"].quantile(0.16)), tau_p84=float(m["tau"].quantile(0.84)),
            rho_map_p16=float(m["rho_map"].quantile(0.16)), rho_map_p84=float(m["rho_map"].quantile(0.84))))
    save_json(fpr, fpr_path)
    logger.info("E2: FPR(tau) = %.3f, FPR(rho_MAP) = %.3f, FPR(LR) = %.3f over %d rho=0 mocks", fpr["fpr_tau"],
                fpr["fpr_rho_map"], fpr["fpr_lr"], fpr["n_mocks_rho0"])


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_common_args(parser)
    args = parser.parse_args()
    cfg = load_config(mode=args.mode)
    logger = setup_logging(cfg, "05_mock_stats")
    tables = cfg.path("tables_dir")
    csv_path, fpr_path = tables / f"mock_stats_{cfg.mode}.csv", tables / f"fpr_{cfg.mode}.json"
    partial_path = tables / f"mock_stats_{cfg.mode}_partial.csv"
    if not args.force and csv_path.exists() and fpr_path.exists():
        logger.info("outputs exist, skipping (use --force to redo)")
        return
    if args.force and partial_path.exists():
        partial_path.unlink()
    done = pd.read_csv(partial_path) if partial_path.exists() else pd.DataFrame()
    done_keys = set(zip(done["kind"], done["rho_true"].fillna(-99.0), done["mock"])) if len(done) else set()
    if len(done):
        logger.info("resuming: %d rows already computed in %s", len(done), partial_path)

    def append_row(row):
        pd.DataFrame([row]).to_csv(partial_path, mode="a", header=not partial_path.exists(), index=False)

    ev_real, names, meta = load_event_arrays(cfg, cfg.rng("fit_subsample"), max_samples=2000)
    inj_full = read_injection_table(cfg.injection_table_path())
    inj = inj_full
    sub = cfg.mode_value("map_injection_subsample", None)
    if sub and sub < len(inj_full["mass_1"]):
        idx = np.sort(cfg.rng("map_inj_sub").choice(len(inj_full["mass_1"]), int(sub), replace=False))
        frac = len(idx) / len(inj_full["mass_1"])
        inj = {**{k: inj_full[k][idx] for k in COLS + ("ln_prior",)}, "total_generated": inj_full["total_generated"] * frac}
        logger.info("MAP statistics use a %d-injection subsample (total_generated rescaled)", len(idx))
    gauss = load_json(cfg.fit_dir("copula_gauss_plp") / "summary.json")
    indep = load_json(cfg.fit_dir("copula_indep_plp") / "summary.json")
    theta0_g = np.array([gauss["quantiles"][n]["median"] for n in gauss["names"]])
    theta0_i = np.array([indep["quantiles"][n]["median"] for n in indep["names"]])
    rhos = [0.0] + cfg.rho_true_grid
    n_full = int(cfg.mode_value("n_mock_full_refits"))

    with GPUSession(cfg, args.backend) as gs:
        from jaxmodels import Grids, HierarchicalLikelihood
        chunk = int(cfg.raw["run"][gs.chunk_key])
        G = Grids(cfg, cfg.mode_value("mass_spline_nodes"), cfg.mode_value("marginal_spline_nodes"))
        fitter = MAPFitter(cfg, G)
        # ---- real data --------------------------------------------------------------
        if ("real", -99.0, -1) not in done_keys:
            tau_obs, p_obs = kendall_medians(ev_real)
            t0 = time.time()
            obs = map_statistics(fitter, ev_real, inj, theta0_g, theta0_i, logger)
            logger.info("REAL DATA: Kendall tau = %.4f (p=%.3g); rho_MAP = %.3f, LR = %.2f (MAP fits %.1fs, ok=%s)",
                        tau_obs, p_obs, obs["rho_map"], obs["lr_stat"], time.time() - t0, obs["map_ok"])
            append_row(dict(kind="real", rho_true=np.nan, mock=-1, tau=tau_obs, tau_p=p_obs, **obs,
                            rho_posterior_median=gauss["quantiles"]["gaussian_copula_rho"]["median"],
                            ln_bf_dep=gauss["log_z"] - indep["log_z"], log_z_g=gauss["log_z"], log_z_i=indep["log_z"],
                            wall_s=time.time() - t0))
        # ---- mocks -------------------------------------------------------------------
        for rho in rhos:
            path = cfg.mocks_path(rho)
            with h5py.File(path, "r") as f:
                keys = sorted(k for k in f if k.startswith("mock_"))
                for i, k in enumerate(keys):
                    if ("mock", rho, i) in done_keys:
                        continue
                    g = f[k]
                    ev = {c: np.asarray(g[c]) for c in COLS}
                    ev["ln_prior"] = np.asarray(g["ln_prior"]) if "ln_prior" in g else np.zeros_like(ev["mass_1"])
                    tau, p = kendall_medians(ev)
                    t0 = time.time()
                    st = map_statistics(fitter, ev, inj, theta0_g, theta0_i, logger)
                    row = dict(kind="mock", rho_true=rho, mock=i, tau=tau, tau_p=p, **st,
                               rho_posterior_median=np.nan, ln_bf_dep=np.nan, log_z_g=np.nan, log_z_i=np.nan)
                    if rho == 0.0 and i < n_full:
                        for mname, key in (("copula_gauss_plp", "g"), ("copula_indep_plp", "i")):
                            spec, pnames, fixed, prior = fitter.specs[mname]
                            lik = HierarchicalLikelihood(spec, pnames, fixed, ev, inj_full, G,
                                                         max_variance=cfg.max_variance,
                                                         enforce_injection_convergence=bool(cfg.raw["likelihood"]["enforce_injection_convergence"]),
                                                         cache_key=f"ns_{mname}",
                                                         cut_mode=cfg.raw["likelihood"].get("cut_mode", "hard"),
                                                         penalty_scale=float(cfg.raw["likelihood"].get("penalty_scale", 1000.0)))
                            fd = cfg.path("fits_dir") / cfg.mode / "mock_refits" / f"mock_{i:04d}_{mname}"
                            fd.mkdir(parents=True, exist_ok=True)
                            res = run_nautilus(lik, prior, cfg, fd, cfg.seed_for(f"mockfit_{i}_{mname}"), chunk,
                                               args.force, logger)
                            row[f"log_z_{key}"] = res["log_z"]
                            if key == "g":
                                row["rho_posterior_median"] = float(np.median(res["eq_points"][:, pnames.index("gaussian_copula_rho")]))
                        row["ln_bf_dep"] = row["log_z_g"] - row["log_z_i"]
                    row["wall_s"] = time.time() - t0
                    append_row(row)
                    logger.info("rho_true=%+.2f mock %3d/%d: tau=%.3f rho_MAP=%.3f LR=%.2f (%.1fs)", rho, i + 1,
                                len(keys), tau, st["rho_map"], st["lr_stat"], row["wall_s"])
    df = pd.read_csv(partial_path)
    summarize(df, rhos, csv_path, fpr_path, logger)
    logger.info("stage 05 (mock_stats) complete")


if __name__ == "__main__":
    main()
