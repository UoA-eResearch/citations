#!/usr/bin/env python
"""Figures F10-F14 for the 2026-09-25 analyses (E2 under four measures, the hierarchical rho scan, the joint
tau-vs-rho_hat check, the LVK-configuration ablation, the point-estimate marginal check). One caption file each.

Usage: ../venv/bin/python analysis/make_e2_figures.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RUN = Path(__file__).resolve().parents[2]
TAB, FIG = RUN / "results" / "tables", RUN / "results" / "figures"
BLUE, ORANGE, AQUA, INK, MUTED, GRID = "#2a78d6", "#eb6834", "#1baf7a", "#0b0b0b", "#898781", "#e1e0d9"
MEAS_LABEL = {"post": "PE-prior posterior medians", "flattheta": "flat in (m1, q, chi_eff, z)",
              "flatx": "flat in internal coords (mocks' native)", "pop": "population-informed (null population)"}
SHORT = {"post": "PE prior", "pop": "population-informed", "flattheta": "flat in theta", "flatx": "flat internal (mocks' native)"}
RHO_COLORS = {-0.6: "#104281", -0.4: "#256abf", -0.2: "#6da7ec", 0.0: MUTED, 0.2: ORANGE}

plt.rcParams.update({"font.size": 9, "axes.edgecolor": "#c3c2b7", "axes.linewidth": 0.8, "axes.grid": True,
                     "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True, "xtick.color": "#52514e",
                     "ytick.color": "#52514e", "axes.labelcolor": INK, "axes.titlesize": 9.5, "legend.frameon": False,
                     "savefig.dpi": 160, "savefig.bbox": "tight", "figure.constrained_layout.use": True})


def caption(name, text):
    (FIG / f"full_{name}.txt").write_text(text.strip() + "\n")


def primary_measure(j):
    """D21 rule: the measure under which the null mocks reproduce the observed m1>=40 point-estimate fraction."""
    order = ["post", "pop", "flattheta", "flatx"]
    ok = [m for m in order if j["marginal_check_frac_m1ge40"][m]["null_p2p5"] <= j["marginal_check_frac_m1ge40"][m]["observed"]
          <= j["marginal_check_frac_m1ge40"][m]["null_p97p5"]]
    return (ok[0] if ok else None), ok


def main():
    t = pd.read_csv(TAB / "e2_tau_full.csv")
    tj = json.load(open(TAB / "e2_tau_full.json"))
    r = pd.read_csv(TAB / "e2_rhoscan_full.csv")
    rj = json.load(open(TAB / "e2_rhoscan_full.json"))
    t["rho_true"], r["rho_true"] = t["rho_true"].round(2), r["rho_true"].round(2)
    real_t, real_r = t[t.kind == "real"].iloc[0], r[r.kind == "real"].iloc[0]
    mocks = t[t.kind == "mock"].merge(r[r.kind == "mock"], on=["kind", "rho_true", "mock"])
    null = mocks[mocks.rho_true == 0.0]
    prim, passing = primary_measure(tj)

    # ---- F10: tau null distributions per measure -------------------------------------------------------------
    fig, axes = plt.subplots(1, 4, figsize=(12, 3.1), sharey=True)
    for ax, M in zip(axes, ["post", "pop", "flattheta", "flatx"]):
        v = null[f"tau_{M}"].values
        obs = real_t[f"tau_{M}"]
        s = tj["stats"][f"tau_{M}"]
        ax.hist(v, bins=np.linspace(-0.3, 0.2, 41), color=BLUE if M == prim else "#86b6ef", alpha=0.9,
                edgecolor="white", linewidth=0.4)
        ax.axvline(obs, color=ORANGE, lw=2)
        ax.set_title(("PRIMARY: " if M == prim else "") + "medians: " + SHORT[M], fontsize=8.5)
        ax.text(0.03, 0.95, f"observed {obs:+.3f}\nFPR {s['fpr_one_sided']:.3f} (two-sided {s['fpr_two_sided']:.3f})",
                transform=ax.transAxes, va="top", fontsize=8, color=INK)
    fig.supxlabel("Kendall tau(q, chi_eff) of per-event medians", fontsize=9)
    axes[0].set_ylabel("rho_true = 0 mock catalogs")
    fig.suptitle("E2: observed rank correlation of point estimates vs 200 zero-correlation mocks, by measure", fontsize=10)
    fig.savefig(FIG / "full_F10_e2_tau_measures.png")
    plt.close(fig)
    caption("F10_e2_tau_measures", f"""
F10 (E2, point-estimate statistic). Histograms: Kendall tau between per-event medians of mass ratio q and effective
spin chi_eff (dimensionless) in 200 mock catalogs with zero intrinsic q-chi_eff dependence (null population =
copula_indep_plp posterior median, real O1-O4a selection, real-event PE scatter). Orange line: the real GWTC-4.0
catalog (153 BBHs). Each panel computes the medians under a different measure, applied identically to real and
mock samples (deviations D21): the PE prior, the fitted null population, flat in (m1, q, chi_eff, z), flat in the
mock generator's internal coordinates. FPR = fraction of null mocks at least as extreme as observed. The primary
panel ({prim}) is fixed by the pre-committed D21 rule (null mocks must reproduce the observed fraction of events with
point-estimate m1 >= 40 Msun); measures passing that check: {', '.join(passing) or 'none'}.""")

    # ---- F11: rho scan: estimator response + null ------------------------------------------------------------
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 3.4), gridspec_kw={"width_ratios": [1.3, 1]})
    grid = sorted(mocks.rho_true.unique())
    data = [mocks[mocks.rho_true == g].rho_hat.values for g in grid]
    parts = a1.violinplot(data, positions=grid, widths=0.13, showmedians=True, showextrema=False)
    for b in parts["bodies"]:
        b.set_facecolor(BLUE); b.set_alpha(0.35); b.set_edgecolor("none")
    parts["cmedians"].set_color(BLUE)
    a1.plot([-0.7, 0.3], [-0.7, 0.3], color=MUTED, lw=0.8, ls="-", zorder=0)
    a1.axhline(real_r.rho_hat, color=ORANGE, lw=2, label=f"real catalog rho_hat = {real_r.rho_hat:+.3f}")
    a1.set(xlabel="true copula rho of the mock population", ylabel="rho_hat (likelihood scan, fixed marginals)",
           xlim=(-0.72, 0.32))
    a1.legend(loc="upper left", fontsize=8)
    a1.set_title("estimator response under real selection and PE scatter")
    a2.hist(null.rho_hat, bins=np.linspace(-0.45, 0.4, 35), color=BLUE, alpha=0.9, edgecolor="white", linewidth=0.4)
    a2.axvline(real_r.rho_hat, color=ORANGE, lw=2)
    a2.text(0.03, 0.95, f"FPR(rho_hat) = {rj['fpr']['rho_hat_as_extreme']:.2f}\nFPR(LR vs rho=0) = {rj['fpr']['lr0_ge_observed']:.2f}",
            transform=a2.transAxes, va="top", fontsize=8)
    a2.set(xlabel="rho_hat", ylabel="rho_true = 0 mocks")
    a2.set_title("null distribution (200 mocks)")
    fig.savefig(FIG / "full_F11_rho_scan.png")
    plt.close(fig)
    caption("F11_rho_scan", f"""
F11 (E2, hierarchical statistic; deviations D20). Left: rho_hat, the maximum of the selection-corrected Gaussian-copula
likelihood scanned in rho with all other hyperparameters fixed at the null population, for 40 mock catalogs at each
rho_true in (-0.6, -0.4, -0.2, +0.2) and 200 at rho_true = 0 (violins; grey line rho_hat = rho_true). The estimator is
unbiased under the real selection function and real-event PE scatter. Orange: the real catalog, rho_hat = {real_r.rho_hat:+.3f}.
Right: the rho_true = 0 distribution of rho_hat with the real value; FPR = fraction of null mocks with rho_hat at
least as large ({rj['fpr']['rho_hat_as_extreme']:.2f}) and with a likelihood-ratio statistic against rho = 0 at least as large
({rj['fpr']['lr0_ge_observed']:.2f}).""")

    # ---- F12: joint tau vs rho_hat ---------------------------------------------------------------------------
    meas = [m for m in (prim or "pop", "flatx")] if prim != "flatx" else ["flatx"]
    fig, axes = plt.subplots(1, len(meas), figsize=(4.6 * len(meas), 3.6), squeeze=False)
    for ax, M in zip(axes[0], meas):
        for g in grid:
            sub = mocks[mocks.rho_true == g]
            ax.scatter(sub[f"tau_{M}"], sub.rho_hat, s=9, color=RHO_COLORS.get(g, MUTED), alpha=0.75,
                       edgecolors="white", linewidths=0.3, label=f"rho_true {g:+.1f}")
        ax.scatter([real_t[f"tau_{M}"]], [real_r.rho_hat], s=90, marker="*", color=ORANGE, edgecolors=INK,
                   linewidths=0.6, zorder=5, label="real catalog")
        c = np.corrcoef(mocks[f"tau_{M}"], mocks.rho_hat)[0, 1]
        ax.set(xlabel=f"tau of medians ({SHORT[M]})", ylabel="rho_hat (likelihood scan)")
        ax.set_title(f"mocks: corr = {c:+.2f}", fontsize=9)
    axes[0][0].legend(fontsize=7, loc="upper left", ncol=2)
    fig.savefig(FIG / "full_F12_tau_vs_rhohat.png")
    plt.close(fig)
    caption("F12_tau_vs_rhohat", """
F12. Point-estimate rank correlation (x: Kendall tau of per-event medians under the stated measure) against the
hierarchical estimator (y: rho_hat from the likelihood scan) for all 360 mock catalogs, coloured by the true copula
rho, and the real catalog (star). In mocks the two statistics track each other; the real catalog's position shows
whether its point estimates and its full likelihoods tell the same story.""")

    # ---- F13: ablation ---------------------------------------------------------------------------------------
    sc = pd.read_csv(TAB / "slope_credibilities_full.csv") if (TAB / "slope_credibilities_full.csv").exists() else None
    if sc is not None and len(sc):
        order = ["baseline_plp_both", "abl_plp_m2taper_both", "abl_plp_lvkspin_both", "baseline_bpq_both",
                 "baseline_splm1_both", "abl_bpl2p_plpspin_both", "abl_bpl2p_sharedtaper_both", "lvk_bpl2p_both"]
        label = {"baseline_plp_both": "PowerLaw+Peak (baseline)", "abl_plp_m2taper_both": "PLP + separate m2 taper",
                 "abl_plp_lvkspin_both": "PLP + log-uniform sigma_0", "baseline_bpq_both": "PLP + broken pairing",
                 "baseline_splm1_both": "14-node spline m1", "abl_bpl2p_plpspin_both": "BPL+2P + uniform sigma_0",
                 "abl_bpl2p_sharedtaper_both": "BPL+2P + shared taper", "lvk_bpl2p_both": "BPL+2P (full LVK config)"}
        sc = sc.set_index("model").reindex([o for o in order if o in set(sc.model)])
        y = np.arange(len(sc))[::-1]
        fig, ax = plt.subplots(figsize=(7.2, 3.6))
        ax.scatter(sc.p_mu1_negative, y, s=36, color=BLUE, label="P(delta mu_eff|q < 0)  (mean shift)", zorder=3)
        ax.scatter(sc.p_lnsigma1_negative, y, s=36, color=ORANGE, marker="D", label="P(delta ln sigma_eff|q < 0)  (width)", zorder=3)
        ax.axvline(0.82, color=BLUE, lw=0.9, ls=":", label="LVK GWTC-4.0: 0.82 (mean)")
        ax.axvline(0.95, color=ORANGE, lw=0.9, ls=":", label="LVK GWTC-4.0: 0.95 (width)")
        ax.set_yticks(y)
        ax.set_yticklabels([label[m] for m in sc.index])
        ax.set_xlim(0.6, 1.005)
        ax.set_xlabel("posterior credibility (Linear q-chi_eff spin model)")
        ax.legend(fontsize=7.5, loc="upper left", bbox_to_anchor=(1.01, 1.0))
        ax.set_title("which ingredient of the LVK configuration moves the verdict?")
        fig.savefig(FIG / "full_F13_ablation.png")
        plt.close(fig)
        caption("F13_ablation", """
F13 (E4 + D17 ablation). Posterior credibility that the chi_eff mean (blue circles) or log-width (orange diamonds)
decreases with mass ratio, under the Linear (q, chi_eff) spin model, for each mass/pairing/prior configuration fitted
to the same 153 BBHs with the same selection function. Dotted lines: the values quoted for GWTC-4.0 by the LVK
(arXiv:2508.18083). The mean-shift credibility is set by the primary-mass shape (PowerLaw+Peak family 0.985-0.995,
Broken Power Law + 2 Peaks 0.80-0.84), independent of the m2 taper and the spin-width prior; the width credibility is
set by the sigma_0 prior (log-uniform 0.88-0.94, uniform 0.77-0.87), independent of the mass model.""")

    # ---- F14: point-estimate marginal check per measure ------------------------------------------------------
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    ms = ["post", "flattheta", "flatx", "pop"]
    for i, M in enumerate(ms):
        mc = tj["marginal_check_frac_m1ge40"][M]
        v = null[f"frac_m1ge40_{M}"].values
        ax.plot([np.quantile(v, 0.025), np.quantile(v, 0.975)], [i, i], color=BLUE, lw=4, alpha=0.35, solid_capstyle="round")
        ax.plot([mc["null_median"]], [i], "o", color=BLUE, ms=5)
        ax.plot([mc["observed"]], [i], "D", color=ORANGE, ms=6)
    ax.set_yticks(range(len(ms)))
    ax.set_yticklabels([SHORT[m] for m in ms], fontsize=8)
    ax.set_xlabel("fraction of events with point-estimate m1 >= 40 Msun")
    ax.plot([], [], "o", color=BLUE, label="null mocks: median and central 95%")
    ax.plot([], [], "D", color=ORANGE, label="real catalog")
    ax.legend(fontsize=7.5, loc="upper left", bbox_to_anchor=(1.01, 1.0))
    ax.set_title("do the mocks reproduce the real point-estimate mass distribution?")
    fig.savefig(FIG / "full_F14_marginal_check.png")
    plt.close(fig)
    caption("F14_marginal_check", f"""
F14 (D21 validity check). Fraction of events whose per-event median primary mass is >= 40 Msun, for the real catalog
(orange) and the 200 null mock catalogs (blue: median and central 95%), under each measure. The mocks reproduce the
real point-estimate distribution only where the orange diamond falls inside the blue band ({', '.join(passing) or 'none'});
under the other measures point estimates of real events are not comparable with mock point estimates.""")
    # ---- F15: E5 per-mass-bin tau vs the null mocks, per measure --------------------------------------------
    e5p = TAB / "e5_mass_bins_full.csv"
    if e5p.exists():
        e5 = pd.read_csv(e5p)
        ms = ["post", "pop", "flattheta", "flatx"]
        bins = sorted(e5[["m1_lo", "m1_hi"]].drop_duplicates().itertuples(index=False), key=lambda b: b[0])
        fig, axes = plt.subplots(1, len(bins), figsize=(3.7 * len(bins), 3.2), sharey=True)
        for ax, (lo, hi) in zip(axes, bins):
            sub = e5[(e5.m1_lo == lo) & (e5.m1_hi == hi)].set_index("measure").reindex(ms)
            y = np.arange(len(ms))[::-1]
            for yi, (M, rr) in zip(y, sub.iterrows()):
                ax.plot([rr.null_p16, rr.null_p84], [yi, yi], color=BLUE, lw=4, alpha=0.35, solid_capstyle="round")
                ax.plot([rr.null_median], [yi], "o", color=BLUE, ms=4)
                ax.plot([rr.tau_obs], [yi], "D", color=ORANGE, ms=5.5)
                ax.text(1.0, yi - 0.32, f"FPR {rr.fpr_one_sided:.2f}", transform=ax.get_yaxis_transform(), ha="right",
                        fontsize=7, color="#52514e")
            ax.axvline(0, color="#c3c2b7", lw=0.8)
            ax.set_title(f"m1 in [{lo:.0f}, {hi:.0f}) Msun  (n_obs = {int(sub.n_obs.iloc[0])})", fontsize=8.5)
            ax.set_xlabel("Kendall tau of medians")
            ax.set_yticks(y)
            ax.set_yticklabels([SHORT[m].split(" (")[0] for m in ms], fontsize=7.5)
            ax.set_ylim(-0.7, len(ms) - 0.4)
        axes[0].plot([], [], "o", color=BLUE, label="null mocks: median, 68%")
        axes[0].plot([], [], "D", color=ORANGE, label="real catalog")
        fig.legend(fontsize=7.5, loc="outside lower center", ncol=2)
        fig.suptitle("E5: q-chi_eff rank correlation within primary-mass bins vs zero-correlation mocks", fontsize=9.5)
        fig.savefig(FIG / "full_F15_e5_mass_bins.png")
        plt.close(fig)
        caption("F15_e5_mass_bins", """
F15 (E5, replaces the retired copula PPC F9). Kendall tau between per-event medians of q and chi_eff within the
preregistered primary-mass bins [2, 20), [20, 40), [40, 200) Msun, for the real catalog (orange diamonds) and the
200 zero-correlation mock catalogs (blue: median and central 68%), under each measure. FPR = one-sided fraction of
null mocks at least as extreme as observed. Bins are assigned by the median m1 under the same measure, so bin
populations differ between measures; the null mocks do not reproduce the real point-estimate mass distribution
(F14), which limits how far these point-estimate comparisons can be trusted.""")
    # ---- F16: mass-binned copula scan (D22) -------------------------------------------------------------------
    mbp = TAB / "e2_rhoscan_mbin_full.csv"
    if mbp.exists():
        mb = pd.read_csv(mbp)
        mb["rho_true"] = mb["rho_true"].round(2)
        realm = mb[mb.kind == "real"].iloc[0]
        labels = ["m1 < 20 Msun", "20 <= m1 < 40", "m1 >= 40 Msun"]
        fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.3), gridspec_kw={"width_ratios": [1, 1.25]})
        nullm = mb[(mb.kind == "mock") & (mb.rho_true == 0.0)]
        for b in range(3):
            v = nullm[f"rho_hat_b{b}"].values
            a1.plot([np.quantile(v, 0.16), np.quantile(v, 0.84)], [b, b], color=BLUE, lw=5, alpha=0.35, solid_capstyle="round")
            a1.plot([np.quantile(v, 0.025), np.quantile(v, 0.975)], [b, b], color=BLUE, lw=1.2, alpha=0.6)
            a1.plot([np.median(v)], [b], "o", color=BLUE, ms=5)
            a1.plot([realm[f"rho_hat_b{b}"]], [b], "D", color=ORANGE, ms=6.5)
        a1.set_yticks(range(3))
        a1.set_yticklabels(labels)
        a1.invert_yaxis()
        a1.set_xlabel("rho_hat in the mass bin")
        a1.set_title("real catalog (orange) vs 200 null mocks (68% / 95%)")
        grid_r = sorted(mb[mb.kind == "mock"].rho_true.unique())
        for b, col in zip(range(3), (BLUE, AQUA, "#4a3aa7")):
            med = [mb[(mb.kind == "mock") & (mb.rho_true == g)][f"rho_hat_b{b}"].median() for g in grid_r]
            a2.plot(grid_r, med, "o-", color=col, lw=1.6, ms=4, label=labels[b])
        a2.plot([-0.7, 0.3], [-0.7, 0.3], color=MUTED, lw=0.8, zorder=0)
        a2.set(xlabel="true copula rho of the mock population (all bins)", ylabel="median rho_hat")
        a2.legend(fontsize=7.5, loc="upper left")
        a2.set_title("estimator response per bin")
        fig.suptitle("D22: no mass-localised q-chi_eff dependence", fontsize=10)
        fig.savefig(FIG / "full_F16_mass_binned_scan.png")
        plt.close(fig)
        caption("F16_mass_binned_scan", f"""
F16 (D22, exploratory). Gaussian copula with a separate dependence parameter in each preregistered primary-mass bin,
scanned on a 17^3 grid with all other hyperparameters at the null population. Left: the real catalog's per-bin
rho_hat (orange) against the distribution over 200 zero-correlation mock catalogs (blue: median, central 68% and 95%).
Right: median per-bin rho_hat against the true (common) rho of the calibration mocks; grey line rho_hat = rho_true.
The two lower-mass bins are unbiased; the m1 >= 40 Msun bin carries a ~-0.3 offset that the null calibration absorbs.
Likelihood ratio against zero dependence in every bin: {realm.lr_zero:.2f} (95% of null mocks larger); for
heterogeneity between bins: {realm.lr_het:.2f}.""")
    # ---- F17: how the PE prior moves per-event medians (D29) --------------------------------------------------
    import sys as _sys
    _sys.path.insert(0, str(RUN / "code" / "src"))
    from io_utils import read_sample_table
    posts, _ = read_sample_table(RUN / "data" / "processed" / "sample_table_full.h5")
    qp, cp, ql, cl = [], [], [], []
    for n in sorted(posts):
        d = posts[n]
        q, c, lp = d["mass_ratio"].values, d["chi_eff"].values, d["ln_prior"].values
        w = np.exp(-(lp - lp.max())); w = np.minimum(w, np.quantile(w, 0.995)); w /= w.sum()
        def wmed(x):
            o = np.argsort(x); return x[o][min(np.searchsorted(np.cumsum(w[o]), 0.5), len(x) - 1)]
        qp.append(np.median(q)); cp.append(np.median(c)); ql.append(wmed(q)); cl.append(wmed(c))
    qp, cp, ql, cl = map(np.array, (qp, cp, ql, cl))
    from scipy.stats import kendalltau
    fig, ax = plt.subplots(figsize=(6.6, 4.6))
    big = np.abs(qp - ql) > 0.06
    for i in range(len(qp)):
        ax.annotate("", xy=(qp[i], cp[i]), xytext=(ql[i], cl[i]),
                    arrowprops=dict(arrowstyle="-|>", color=ORANGE if big[i] else "#b9b8b0", lw=1.2 if big[i] else 0.6,
                                    mutation_scale=7))
    ax.scatter(ql, cl, s=10, color=BLUE, zorder=3, label=f"prior removed (likelihood medians): tau = {kendalltau(ql, cl).statistic:+.3f}")
    ax.scatter(qp, cp, s=10, color=INK, zorder=3, label=f"PE-prior posterior medians: tau = {kendalltau(qp, cp).statistic:+.3f}")
    ax.plot([], [], color=ORANGE, lw=1.2, label="events whose q median moves by > 0.06")
    ax.set(xlabel="mass ratio q (per-event median)", ylabel="chi_eff (per-event median)", xlim=(0.15, 1.0))
    ax.legend(fontsize=7.5, loc="lower left", framealpha=0.9, frameon=True)
    ax.set_title("the isotropic-spin PE prior drags high-chi_eff events to lower q")
    fig.savefig(FIG / "full_F17_prior_shift.png")
    plt.close(fig)
    caption("F17_prior_shift", f"""
F17 (D29). Per-event medians of mass ratio q and chi_eff for the 153 BBHs, before (blue: prior removed, i.e. posterior
samples reweighted by 1/pi_PE) and after (black: the released posterior medians) the parameter-estimation prior acts;
arrows point from the former to the latter. Orange arrows: events whose q median moves by more than 0.06 -- mostly
high-chi_eff events (GW190517_055101, GW231028_153006, GW190620_030421, GW170729, ...) pulled to lower q, because the
isotropic-spin prior allows large chi_eff only at unequal masses. The rank correlation of the medians roughly doubles
({kendalltau(ql, cl).statistic:+.3f} -> {kendalltau(qp, cp).statistic:+.3f}) without any population correlation.""")

    # ---- F18: observed tau vs every simulated hypothesis (v3b mocks, D29) -------------------------------------
    v3p = TAB / "e2_tau_full_v3.csv"
    if v3p.exists():
        v3 = pd.read_csv(v3p)
        v3["rho_true"] = v3["rho_true"].round(2)
        realv = v3[v3.kind == "real"].iloc[0]
        sets = [("null (rho = 0)", 0.0), ("copula rho = -0.2", -0.2), ("copula rho = -0.4", -0.4), ("copula rho = -0.6", -0.6),
                ("copula rho = +0.2", 0.2), ("LVK width effect", -9.0), ("PLP mean shift", -8.0)]
        fig, axes = plt.subplots(1, 2, figsize=(10.5, 3.6), sharey=True)
        for ax, M in zip(axes, ("post", "flattheta")):
            for yi, (lab, code) in enumerate(sets):
                v = v3[(v3.kind == "mock") & np.isclose(v3.rho_true, code)][f"tau_{M}"].values
                ax.plot([np.quantile(v, 0.025), np.quantile(v, 0.975)], [yi, yi], color=BLUE, lw=1.2, alpha=0.6)
                ax.plot([np.quantile(v, 0.16), np.quantile(v, 0.84)], [yi, yi], color=BLUE, lw=5, alpha=0.35, solid_capstyle="round")
                ax.plot([np.median(v)], [yi], "o", color=BLUE, ms=4.5)
            ax.axvline(realv[f"tau_{M}"], color=ORANGE, lw=2, label=f"real catalog ({realv[f'tau_{M}']:+.3f})")
            ax.set_title(f"medians: {SHORT[M]}")
            ax.set_xlabel("Kendall tau(q, chi_eff) of per-event medians")
            ax.legend(fontsize=7.5, loc="lower right")
        axes[0].set_yticks(range(len(sets)))
        axes[0].set_yticklabels([s[0] for s in sets], fontsize=8)
        axes[0].invert_yaxis()
        fig.suptitle("E2 against physical mock PE (v3b): what each hypothesis predicts (median, 68%, 95%)", fontsize=10)
        fig.savefig(FIG / "full_F18_e2_hypotheses_v3.png")
        plt.close(fig)
        caption("F18_e2_hypotheses_v3", """
F18 (D29). Distribution of the point-estimate Kendall tau in mock catalogs built with physical mock PE (v3b: Gaussian
measurement noise in ln chirp mass, symmetric mass ratio, chi_eff and ln distance with each donor event's covariance,
resampled to the PE prior; validated against the real catalog in var_tot and measurement widths) under each simulated
hypothesis: no dependence, Gaussian copulas with rho = -0.6 ... +0.2, the LVK Linear-model width effect, and the
PowerLaw+Peak mean shift (40-200 catalogs each; dots medians, bars 68% and 95%). Orange: the real catalog. Left, the
preregistered statistic (PE-prior posterior medians): the real value lies beyond every simulated hypothesis. Right,
the same statistic with the PE prior removed: the real value is unremarkable.""")
    print("figures written; primary measure:", prim, "| passing:", passing)


if __name__ == "__main__":
    main()
