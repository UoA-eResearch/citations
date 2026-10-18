"""Figures for the report (each PNG has a .txt caption).

  F1  published ROR against recomputed ROR (log-log), one point per eligible signal, coloured by survival after
      calibration (MLE null, BH q < 0.05); the identity line and the 1.25x inflation line
  F2  the empirical null: negative-control log RORs with the fitted N(mu, sigma) (MLE) against the recomputed log RORs
      of the published signals
  F3  share surviving under each protocol variant and null, with the uncalibrated replication share; paper-cluster
      bootstrap intervals for the primary
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T, F = RUN / "results" / "tables", RUN / "results" / "figures"
F.mkdir(parents=True, exist_ok=True)
COL = ["#2a78d6", "#1baf7a", "#eb6834", "#8a5cd1"]
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def main():
    p = json.load(open(T / "primary.json"))
    s = pd.read_csv(T / "signals_results.csv", dtype={"paper": str})
    s = s[np.isfinite(s.primary_ror) & (s.primary_ror > 0)]
    surv = s.primary_survive_mle.fillna(False).astype(bool)
    # F1
    fig, ax = plt.subplots(figsize=(6.4, 5.4)); fig.subplots_adjust(left=0.13, right=0.97, bottom=0.12, top=0.9)
    ax.scatter(s.primary_ror[~surv], s.estimate[~surv], s=16, color=COL[2], alpha=0.65, lw=0, label="does not survive")
    ax.scatter(s.primary_ror[surv], s.estimate[surv], s=16, color=COL[0], alpha=0.75, lw=0, label="survives calibration")
    lim = [min(s.primary_ror.min(), s.estimate.min()) * 0.8, max(s.primary_ror.max(), s.estimate.max()) * 1.25]
    ax.plot(lim, lim, color=INK2, lw=1); ax.plot(lim, [1.25 * v for v in lim], color=INK2, lw=0.8, ls=":")
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("recomputed ROR (one protocol, public FAERS)"); ax.set_ylabel("published ROR")
    ax.legend(frameon=False, loc="upper left", fontsize=8); ax.grid(color=GRID, lw=0.5)
    h2 = p["H2"]
    fig.suptitle(f"Published against recomputed: median ratio {h2['median_ratio']:.2f}", x=0.13, ha="left", fontsize=10.5, color=INK)
    fig.savefig(F / "F1_published_vs_recomputed.png", dpi=170); plt.close(fig)
    caption("F1_published_vs_recomputed", f"""Each point is one eligible published signal (n = {len(s)}) whose recomputation gave an
    estimate. Solid line: identity; dotted: published = 1.25 x recomputed. Blue: recomputed ROR > 1 and calibrated BH
    q < 0.05 against the MLE empirical null.""")
    # F2
    nc = pd.read_csv(RUN / "data" / "negative_controls_computed.csv")
    nc = nc[(nc.status == "ok") & (nc.a >= 1) & np.isfinite(nc.se)]
    mu, sg = p["null"]["mle"]["mu"], p["null"]["mle"]["sigma"]
    fig, ax = plt.subplots(figsize=(7.4, 3.6)); fig.subplots_adjust(left=0.1, right=0.97, bottom=0.16, top=0.86)
    bins = np.linspace(-6, 8, 57)
    ax.hist(np.log(nc.ror), bins=bins, density=True, color=COL[1], alpha=0.55, label=f"negative controls (n = {len(nc)})")
    ax.hist(np.log(s.primary_ror), bins=bins, density=True, histtype="step", color=COL[0], lw=1.8, label=f"published signals, recomputed (n = {len(s)})")
    xx = np.linspace(-6, 8, 400); ax.plot(xx, stats.norm.pdf(xx, mu, sg), color=INK, lw=1.2, label=f"fitted null N({mu:.2f}, {sg:.2f}²)")
    ax.axvline(0, color=GRID, lw=1); ax.set_xlabel("log ROR"); ax.set_ylabel("density"); ax.legend(frameon=False, fontsize=8)
    fig.suptitle("The empirical null from negative controls, against the published signals", x=0.1, ha="left", fontsize=10.5, color=INK)
    fig.savefig(F / "F2_null.png", dpi=170); plt.close(fig)
    caption("F2_null", f"""Recomputed log RORs of the OHDSI negative-control pairs with at least one report (green), the
    maximum-likelihood systematic-error distribution fitted to them (black; mu = {mu:.2f}, sigma = {sg:.2f}), and the
    recomputed log RORs of the eligible published signals (blue outline).""")
    # F3
    rows = [("primary protocol, MLE null", p["H1"]["share_surviving"], p["H1"]["ci"])]
    if "H1_null_propagated" in p:   # D4
        rows.append(("  … with the null's uncertainty", p["H1"]["share_surviving"], p["H1_null_propagated"]["ci"]))
    rows += [
            ("primary protocol, sample-SD null", p["H1_sd_null"]["share"], p["H1_sd_null"]["ci"]),
            ("uncalibrated (lower bound > 1, a ≥ 3)", p["uncalibrated_replication"]["share"], p["uncalibrated_replication"]["ci"])]
    for v, lab in (("allsuspect", "all suspect roles"), ("nodedup", "no deduplication"), ("fullwindow", "full window")):
        rows.append((f"{lab}, MLE null", p["variants"][v]["survive_mle"], None))
    if "faersonly" in p["variants"]:   # D4
        rows.append((f"FAERS era only ({p['variants']['faersonly']['n']}), MLE null", p["variants"]["faersonly"]["survive_mle"], None))
    if "all_drugs_only" in p:
        rows.append(("'all drugs' label only†, MLE null", p["all_drugs_only"]["share_surviving"], p["all_drugs_only"]["ci"]))
    ns = T / "null_sensitivity.json"
    if ns.exists():   # exploratory, added after the primary results were seen
        z = json.load(open(ns))["centre_zero"]
        rows.append(("exploratory: MLE width, centred at 0", z["share"], z["ci"]))
    fig, ax = plt.subplots(figsize=(7.4, 4.6)); fig.subplots_adjust(left=0.38, right=0.97, bottom=0.12, top=0.88)
    for i, (lab, v, ci) in enumerate(rows):
        y = len(rows) - 1 - i
        c = COL[1] if lab.startswith("exploratory") else COL[0]
        if ci:
            ax.plot(ci, [y, y], color=c, lw=2)
        ax.plot(v, y, "o", color=c, ms=7, mec=SURF, mew=1.5)
        ax.text(v, y + 0.25, f"{v:.0%}", ha="center", fontsize=7.5, color=INK2)
    ax.axvline(0.6, color=COL[2], lw=1.2, ls="--"); ax.text(0.6, len(rows) - 0.4, "H1 bar 60%", color=COL[2], fontsize=8, ha="left")
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows][::-1]); ax.set_xlim(0, 1)
    ax.set_xlabel("share of published signals that survive"); ax.grid(axis="x", color=GRID, lw=0.6)
    fig.suptitle("How many published signals survive", x=0.38, ha="left", fontsize=10.5, color=INK)
    fig.savefig(F / "F3_survival.png", dpi=170); plt.close(fig)
    caption("F3_survival", """Share of eligible published signals that survive: recomputed ROR > 1 and calibrated BH q < 0.05
    (or, for the uncalibrated row, recomputed lower bound > 1 with at least 3 reports). Bars: paper-cluster bootstrap
    95% intervals where computed; the second row's interval also resamples the negative controls and refits the null
    in each draw (added after review, D4). FAERS era only: windows truncated to start at 2012Q4 (the preregistered
    sensitivity, run after review). †The 'all drugs' comparison label was right for only 76% of a fresh review sample.
    The last row (second colour) is exploratory, added after the primary results were seen: the fitted null's width
    with its centre moved to zero.""")
    print("figures written")


if __name__ == "__main__":
    main()
