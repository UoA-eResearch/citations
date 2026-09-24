#!/usr/bin/env python
"""Stage 07: figures (results/figures/<mode>_*.png).

F1 data: posterior medians q vs chi_eff (colour = m1) with 68% error bars
F2 baseline chi_eff mean/width slopes (E3 variants + NUTS cross-check)
F3 copula dependence parameter posteriors with prior and SDDR (E1)
F4 ln BF table as a bar chart
F5 E2: null distribution of tau and rho_MAP vs observed values
F6 calibration curve: fraction as extreme vs rho_true
F7 fitted flexible marginals (q, chi_eff) with 90% bands, dependence vs independence
F8 LOO: rho median/90% interval when each event is removed
F9 PPC per mass bin
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("JAX_PLATFORMS", "cpu")

from config import add_common_args, load_config, setup_logging  # noqa: E402
from io_utils import load_json, read_sample_table  # noqa: E402
from models_registry import build_model  # noqa: E402

plt.rcParams.update({"figure.dpi": 130, "savefig.dpi": 130, "font.size": 9, "axes.grid": True, "grid.alpha": 0.3})
COLORS = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3", "#937860", "#DA8BC3"]


def load_fit(cfg, m):
    d = cfg.fit_dir(m)
    if (d / "summary.json").exists():
        return load_json(d / "summary.json"), np.load(d / "posterior.npz", allow_pickle=True)
    return None, None


def col(post, name):
    names = list(post["names"])
    return post["samples"][:, names.index(name)]


def fig_data(cfg, out, logger):
    posteriors, meta = read_sample_table(cfg.sample_table_path())
    fig, ax = plt.subplots(figsize=(6, 4.2))
    m1 = np.array([np.median(p["mass_1"]) for p in posteriors.values()])
    for i, (n, p) in enumerate(posteriors.items()):
        q = np.percentile(p["mass_ratio"], [16, 50, 84])
        c = np.percentile(p["chi_eff"], [16, 50, 84])
        ax.errorbar(q[1], c[1], xerr=[[q[1] - q[0]], [q[2] - q[1]]], yerr=[[c[1] - c[0]], [c[2] - c[1]]],
                    fmt="o", ms=3, lw=0.6, alpha=0.7, color=plt.cm.viridis((np.log(m1[i]) - np.log(5)) / (np.log(300) - np.log(5))))
    sm = plt.cm.ScalarMappable(cmap="viridis", norm=matplotlib.colors.LogNorm(5, 300))
    fig.colorbar(sm, ax=ax, label=r"median $m_1$ [$M_\odot$]")
    ax.set(xlabel="mass ratio q (median, 68%)", ylabel=r"$\chi_{\rm eff}$ (median, 68%)",
           title=f"GWTC BBH sample ({len(posteriors)} events)")
    fig.tight_layout()
    fig.savefig(out / f"{cfg.mode}_F1_data_q_chieff.png")
    plt.close(fig)


def fig_baseline(cfg, out, logger):
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.4))
    for i, m in enumerate(["baseline_plp_both", "baseline_plp_mean", "baseline_plp_width", "baseline_bpq_both",
                           "baseline_splm1_both", "lvk_bpl2p_both"]):   # + the LVK mass model (D15)
        s, post = load_fit(cfg, m)
        if s is None:
            continue
        names = list(post["names"])
        for ax, par in zip(axes, ("mu_chi_eff_1", "sigma_chi_eff_1")):
            if par in names:
                ax.hist(col(post, par), bins=40, density=True, histtype="step", color=COLORS[i % 7], label=m)
    nuts = cfg.fit_dir("baseline_plp_both") / "posterior_nuts.npz"
    if nuts.exists():
        p = np.load(nuts, allow_pickle=True)
        for ax, par in zip(axes, ("mu_chi_eff_1", "sigma_chi_eff_1")):
            if par in list(p["names"]):
                ax.hist(p["samples"][:, list(p["names"]).index(par)], bins=40, density=True, histtype="step",
                        ls="--", color="k", label="NUTS cross-check")
    axes[0].set(xlabel=r"$d\mu_{\chi}/dq$ (chi_eff mean slope)", ylabel="posterior density")
    axes[0].axvline(0, color="k", lw=0.6)
    axes[1].set(xlabel=r"$d\ln\sigma_{\chi}/dq$ (chi_eff log-width slope)")
    axes[1].axvline(0, color="k", lw=0.6)
    axes[0].legend(fontsize=6)
    axes[1].legend(fontsize=6)   # the width-only variant has no curve in the left panel
    fig.suptitle("E3: baseline (LVK-style) chi_eff-q slopes")
    fig.tight_layout()
    fig.savefig(out / f"{cfg.mode}_F2_baseline_slopes.png")
    plt.close(fig)


def fig_copula(cfg, out, diag, logger):
    fig, ax = plt.subplots(figsize=(5.5, 3.6))
    for i, m in enumerate(["copula_gauss_plp", "copula_gauss_splm1"]):
        s, post = load_fit(cfg, m)
        if s is None:
            continue
        rho = col(post, "gaussian_copula_rho")
        sd = diag.get(f"sddr_ln_bf_dependence_{m}", np.nan)
        ax.hist(rho, bins=40, density=True, histtype="stepfilled", alpha=0.4, color=COLORS[i],
                label=f"{m}: SDDR ln BF = {sd:+.2f}")
    s, post = load_fit(cfg, "copula_frank_plp")
    if s is not None:
        th = col(post, "frank_copula_theta")
        # Frank theta -> Kendall tau -> approx equivalent Gaussian rho for display
        ax2 = ax.twiny()
        ax2.hist(th, bins=40, density=True, histtype="step", color=COLORS[3], label="Frank theta (top axis)")
        ax2.set_xlabel(r"Frank $\theta$")
        ax2.legend(loc="upper left", fontsize=7)
    lo, hi = cfg.prior_bounds("gaussian_copula_rho")
    ax.axhline(1 / (hi - lo), color="grey", ls=":", label="prior")
    ax.axvline(0, color="k", lw=0.6)
    e1 = diag.get("E1_ln_bf_dependence", np.nan)
    ax.set(xlabel=r"Gaussian copula $\rho$", ylabel="posterior density",
           title=f"E1: nested-sampling ln BF(dep vs indep) = {e1:+.2f}")
    ax.legend(fontsize=7, loc="upper right")
    fig.tight_layout()
    fig.savefig(out / f"{cfg.mode}_F3_copula_rho.png")
    plt.close(fig)


def fig_bf(cfg, out, diag, logger):
    comps = diag.get("comparisons", [])
    if not comps:
        return
    fig, ax = plt.subplots(figsize=(7, 3.6))
    y = np.arange(len(comps))
    vals = [c["ln_bf"] for c in comps]
    ax.barh(y, vals, color=[COLORS[0] if v < np.log(3) else COLORS[3] for v in vals])
    ax.set_yticks(y)
    ax.set_yticklabels([f"{c['endpoint']}: {c['model']} vs {c['reference']}" for c in comps], fontsize=7)
    ax.axvline(np.log(3), color="k", ls="--", lw=0.8, label="ln 3")
    ax.axvline(-np.log(3), color="k", ls="--", lw=0.8)
    ax.axvline(0, color="k", lw=0.6)
    ax.set(xlabel="ln Bayes factor (model vs reference)", title="Evidence table (nautilus)")
    ax.legend(fontsize=7)
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(out / f"{cfg.mode}_F4_bf_table.png")
    plt.close(fig)


def fig_mocks(cfg, out, logger):
    tables = cfg.path("tables_dir")
    csv = tables / f"mock_stats_{cfg.mode}.csv"
    fpr_path = tables / f"fpr_{cfg.mode}.json"
    if not csv.exists():
        return
    df = pd.read_csv(csv)
    fpr = load_json(fpr_path) if fpr_path.exists() else {}
    real = df[df.kind == "real"].iloc[0]
    m0 = df[(df.kind == "mock") & (df.rho_true == 0.0)]
    fig, axes = plt.subplots(1, 3, figsize=(10, 3.3))
    for ax, stat, label, key in zip(axes, ("tau", "rho_map", "lr_stat"),
                                    (r"Kendall $\tau$ (medians)", r"$\hat\rho_{\rm MAP}$", "profile LR statistic"),
                                    ("fpr_tau", "fpr_rho_map", "fpr_lr")):
        ax.hist(m0[stat].dropna(), bins=25, color=COLORS[0], alpha=0.6, label=r"$\rho_{\rm true}=0$ mocks")
        ax.axvline(real[stat], color=COLORS[3], lw=1.5, label=f"observed = {real[stat]:.3f}")
        ax.set(xlabel=label, title=f"FPR = {fpr.get(key, np.nan):.3f}")
        ax.legend(fontsize=7)
    axes[0].set_ylabel("number of mocks")
    fig.suptitle(f"E2: null calibration ({len(m0)} zero-correlation mocks)")
    fig.tight_layout()
    fig.savefig(out / f"{cfg.mode}_F5_mock_null.png")
    plt.close(fig)
    if fpr.get("calibration_curve"):
        cc = pd.DataFrame(fpr["calibration_curve"]).sort_values("rho_true")
        fig, axes = plt.subplots(1, 2, figsize=(8, 3.3))
        axes[0].plot(cc.rho_true, cc.frac_tau_as_extreme, "o-", label=r"$\tau$ statistic")
        axes[0].plot(cc.rho_true, cc.frac_rho_map_as_extreme, "s-", label=r"$\hat\rho_{\rm MAP}$ statistic")
        axes[0].axhline(0.05, color="k", ls="--", lw=0.8, label="5%")
        axes[0].set(xlabel=r"$\rho_{\rm true}$", ylabel="fraction of mocks at least as extreme as observed",
                    title="Calibration curve")
        axes[0].legend(fontsize=7)
        axes[1].errorbar(cc.rho_true, cc.tau_median, yerr=[cc.tau_median - cc.tau_p16, cc.tau_p84 - cc.tau_median],
                         fmt="o-", label=r"mock $\tau$ (68%)")
        axes[1].errorbar(cc.rho_true, cc.rho_map_median, yerr=[cc.rho_map_median - cc.rho_map_p16, cc.rho_map_p84 - cc.rho_map_median],
                         fmt="s-", label=r"mock $\hat\rho_{\rm MAP}$ (68%)")
        axes[1].axhline(real["tau"], color=COLORS[3], ls="-", lw=1, label=r"observed $\tau$")
        axes[1].axhline(real["rho_map"], color=COLORS[3], ls=":", lw=1, label=r"observed $\hat\rho$")
        axes[1].set(xlabel=r"$\rho_{\rm true}$", ylabel="statistic", title="Statistic vs injected correlation")
        axes[1].legend(fontsize=7)
        fig.tight_layout()
        fig.savefig(out / f"{cfg.mode}_F6_calibration_curve.png")
        plt.close(fig)


def fig_marginals(cfg, out, logger):
    from jaxmodels import Grids, log_p_m1, q_conditional, chi_sector
    import jax.numpy as jnp
    G = Grids(cfg, cfg.mode_value("mass_spline_nodes"), cfg.mode_value("marginal_spline_nodes"))
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.3))
    qs, chis, m1s = np.linspace(0.1, 1, 120), np.linspace(-1, 1, 160), np.geomspace(3, 100, 160)
    for i, m in enumerate(["copula_indep_plp", "copula_gauss_plp", "baseline_plp_both"]):
        s, post = load_fit(cfg, m)
        if s is None:
            continue
        spec, names, fixed, _ = build_model(m, cfg)
        rng = np.random.default_rng(0)
        idx = rng.choice(len(post["samples"]), size=min(150, len(post["samples"])), replace=False)
        pq, pc, pm = [], [], []
        for si in idx:
            p = {n: jnp.asarray(float(v)) for n, v in zip(names, post["samples"][si])}
            p.update({k: jnp.asarray(float(v)) for k, v in fixed.items()})
            m1_ref = jnp.full(qs.shape, 35.0)
            pq.append(np.exp(np.asarray(q_conditional(m1_ref, jnp.asarray(qs), p, spec, G, False)[0])))
            pc.append(np.exp(np.asarray(chi_sector(jnp.full(chis.shape, 0.7), jnp.asarray(chis), p, spec, G, False)[0])))
            pm.append(np.exp(np.asarray(log_p_m1(jnp.asarray(m1s), p, spec, G))))
        for ax, arr, x in zip(axes, (pm, pq, pc), (m1s, qs, chis)):
            lo, med, hi = np.percentile(np.array(arr), [5, 50, 95], axis=0)
            ax.plot(x, med, color=COLORS[i], label=m)
            ax.fill_between(x, lo, hi, color=COLORS[i], alpha=0.2)
    axes[0].set(xscale="log", yscale="log", xlabel=r"$m_1$ [$M_\odot$]", ylabel=r"$p(m_1)$", ylim=(1e-4, 1))
    axes[1].set(xlabel="q", ylabel=r"$p(q\,|\,m_1=35)$")
    axes[2].set(xlabel=r"$\chi_{\rm eff}$", ylabel=r"$p(\chi_{\rm eff}\,|\,q=0.7)$")
    axes[0].legend(fontsize=7)
    fig.suptitle("Fitted marginals (median and 90% band)")
    fig.tight_layout()
    fig.savefig(out / f"{cfg.mode}_F7_marginals.png")
    plt.close(fig)


def fig_loo_ppc(cfg, out, logger):
    tables = cfg.path("tables_dir")
    loo = tables / f"loo_{cfg.mode}.csv"
    if loo.exists():
        df = pd.read_csv(loo)
        diag = load_json(tables / f"diagnostics_{cfg.mode}.json")
        full = diag["loo"]["full_rho_p5_50_95"]
        fig, ax = plt.subplots(figsize=(max(5, 0.12 * len(df) + 2), 3.4))
        x = np.arange(len(df))
        ax.errorbar(x, df["median"], yerr=[df["median"] - df["p5"], df["p95"] - df["median"]], fmt="o", ms=3,
                    color=COLORS[0], lw=0.8)
        ax.axhspan(full[0], full[2], color="grey", alpha=0.2, label="all events (90%)")
        ax.axhline(full[1], color="k", lw=0.8)
        ax.axhline(0, color="k", ls=":", lw=0.6)
        unreliable = ~df["loo_reliable"].astype(bool)
        if unreliable.any():
            ax.plot(x[unreliable], df["median"][unreliable], "x", color=COLORS[3], label="LOO ESS too low")
        ax.set_xticks(x)
        ax.set_xticklabels(df["event"], rotation=90, fontsize=5)
        ax.set(ylabel=r"$\rho$ with event removed (median, 90%)", title="E5: leave-one-out stability of the copula dependence")
        ax.legend(fontsize=7)
        fig.tight_layout()
        fig.savefig(out / f"{cfg.mode}_F8_loo.png")
        plt.close(fig)
    ppc = tables / f"ppc_{cfg.mode}.csv"
    if ppc.exists():
        df = pd.read_csv(ppc)
        taus = np.load(tables / f"ppc_taus_{cfg.mode}.npy")
        fig, axes = plt.subplots(1, len(df), figsize=(3.3 * len(df), 3.2), squeeze=False)
        for b, (ax, r) in enumerate(zip(axes[0], df.itertuples())):
            t = taus[:, b][np.isfinite(taus[:, b])]
            ax.hist(t, bins=20, color=COLORS[0], alpha=0.6, label="posterior predictive")
            ax.axvline(r.tau_obs, color=COLORS[3], lw=1.5, label=f"observed ({r.tau_obs:+.2f})")
            ax.set(xlabel=r"Kendall $\tau$", title=f"$m_1\\in[{r.m1_lo:.0f},{r.m1_hi:.0f})$, n={r.n_events}, p={r.p_value_two_sided:.2f}")
            ax.legend(fontsize=6)
        fig.suptitle("E5: mass-binned posterior predictive checks (copula_gauss_plp)")
        fig.tight_layout()
        fig.savefig(out / f"{cfg.mode}_F9_ppc.png")
        plt.close(fig)


def write_captions(cfg, out, diag, logger):
    """One caption file per figure (results/figures/<mode>_F<n>_<name>.txt)."""
    tables = cfg.path("tables_dir")
    fpr_path = tables / f"fpr_{cfg.mode}.json"
    fpr = load_json(fpr_path) if fpr_path.exists() else {}
    e1 = diag.get("E1_ln_bf_dependence", np.nan)
    n_ev = diag.get("loo", {}).get("n_events", "N")
    caps = {
        "F1_data_q_chieff": (
            f"F1. Posterior medians of mass ratio q = m2/m1 (x axis, dimensionless) and effective inspiral spin "
            f"chi_eff (y axis, dimensionless) for the {n_ev} BBH events of the sample, with 68% (16th-84th percentile) "
            "error bars from each event's preferred 'Mixed' PE posterior. Colour: median source-frame primary mass "
            "m1 in solar masses (log scale)."),
        "F2_baseline_slopes": (
            "F2 (E3). Posterior densities of the chi_eff-q slope hyperparameters of the LVK-style 'Linear' truncated-"
            "Gaussian chi_eff model: left, d mu/dq = delta mu_eff|q (slope of the chi_eff mean with mass ratio, "
            "dimensionless); right, d ln sigma/dq = delta ln sigma_eff|q (slope of the natural-log width). Curves: the "
            "mean+width model (baseline_plp_both), the mean-only and width-only E3 variants, and the same spin model "
            "with a broken-power-law pairing function and with a spline primary-mass model (E4). Also shown: the same spin model on the LVK Broken Power Law + 2 Peaks mass model (lvk_bpl2p_both, D15). Dashed black: numpyro "
            "NUTS cross-check of baseline_plp_both. Vertical line: zero slope (no correlation)."),
        "F3_copula_rho": (
            f"F3 (E1). Posterior density of the Gaussian-copula dependence parameter rho (x axis, dimensionless, "
            "rank-correlation-like; negative = anticorrelation) for the PowerLaw+Peak and spline-m1 mass models, with "
            f"the uniform prior (dotted) and the Savage-Dickey ln BF in the legend. Nested-sampling ln BF(dependence vs "
            f"independence) = {e1:+.2f} (title). Step curve / top axis: Frank-copula theta posterior."),
        "F4_bf_table": (
            "F4. Natural-log Bayes factors (x axis) from nautilus nested sampling for every preregistered model "
            "comparison (E1 copula dependence vs independence; E3 mean/width decomposition; E4 pairing-function and "
            "mass-model generalisations). Dashed lines: +/- ln 3, the plan's decision threshold; blue bars are below "
            "ln 3, red at or above."),
        "F5_mock_null": (
            f"F5 (E2). Null distributions over {fpr.get('n_mocks_rho0', 'N')} zero-correlation mock catalogs "
            "(matched marginals, real O1-O4a selection function, real-event PE kernels) of three correlation "
            "statistics: Kendall's tau of per-event posterior medians (left, dimensionless), the MAP Gaussian-copula "
            "rho with all other hyperparameters re-optimised (middle), and the profile log-likelihood-ratio statistic "
            "2[lnL(rho_hat) - lnL(rho=0)] (right). Red line: the real-data value; title: false-positive rate = fraction "
            f"of mocks at least as extreme in the observed direction (FPR(tau) = {fpr.get('fpr_tau', np.nan)})."),
        "F6_calibration_curve": (
            "F6 (E2 calibration curve). Left: fraction of mock catalogs whose statistic is at least as extreme as the "
            "real-data value (y axis) versus the injected Gaussian-copula correlation rho_true (x axis), for the tau "
            "and rho_MAP statistics; dashed line: 5%. Right: median and 68% range of the mock statistics versus "
            "rho_true, with the observed values as horizontal lines."),
        "F7_marginals": (
            "F7. Fitted population marginals (median and 90% band over posterior draws): p(m1) in 1/Msun versus "
            "source-frame primary mass m1 in Msun (log-log); the conditional mass-ratio density p(q | m1 = 35 Msun) "
            "versus q; and the chi_eff density p(chi_eff | q = 0.7) versus chi_eff. Colours: copula independence "
            "model, Gaussian-copula dependence model (identical marginal parameterisation), and the LVK-style "
            "baseline with truncated-Gaussian chi_eff."),
        "F8_loo": (
            "F8 (E5). Leave-one-out stability: median and 90% interval of the Gaussian-copula rho (y axis, "
            "dimensionless) when each event (x axis) is removed by importance reweighting of the full posterior; grey "
            "band / black line: the all-events posterior; red crosses: events whose LOO effective sample size is too "
            "low for the reweighting to be reliable."),
        "F9_ppc": (
            "F9 (E5). Mass-binned posterior predictive checks: histogram of Kendall's tau (x axis) between the "
            "observed q and chi_eff medians predicted by draws from the copula_gauss_plp posterior (propagated through "
            "the selection function and the PE kernels), per bin of median primary mass m1 (Msun); red line: the "
            "observed tau in that bin; title: number of events and two-sided p-value."),
    }
    n = 0
    for stem, text in caps.items():
        png = out / f"{cfg.mode}_{stem}.png"
        if png.exists():
            (out / f"{cfg.mode}_{stem}.txt").write_text(text + "\n")
            n += 1
    logger.info("wrote %d caption files", n)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_common_args(parser)
    args = parser.parse_args()
    cfg = load_config(mode=args.mode)
    logger = setup_logging(cfg, "07_make_figures")
    out = cfg.path("figures_dir")
    done = out / f"{cfg.mode}_F8_loo.png"   # F9 (copula PPC) retired 2026-09-25, see results/obsolete_20260925
    if not args.force and done.exists():
        logger.info("figures exist, skipping (use --force to redo)")
        return
    diag_path = cfg.path("tables_dir") / f"diagnostics_{cfg.mode}.json"
    diag = load_json(diag_path) if diag_path.exists() else {}
    for fn, fargs in ((fig_data, (cfg, out, logger)), (fig_baseline, (cfg, out, logger)),
                      (fig_copula, (cfg, out, diag, logger)), (fig_bf, (cfg, out, diag, logger)),
                      (fig_mocks, (cfg, out, logger)), (fig_marginals, (cfg, out, logger)),
                      (fig_loo_ppc, (cfg, out, logger))):
        try:
            fn(*fargs)
            logger.info("%s done", fn.__name__)
        except Exception as e:  # noqa: BLE001
            logger.exception("%s failed: %s", fn.__name__, e)
            raise
    write_captions(cfg, out, diag, logger)
    logger.info("stage 07 (make_figures) complete: %s", sorted(p.name for p in out.glob(f"{cfg.mode}_*.png")))


if __name__ == "__main__":
    main()
