"""Figures for the report (each PNG has a .txt caption). Written after did.py and secondary.py.

  F1  event-study log rate ratios (PPML, Sun-Abraham, cohort-weighted): left, editions (preregistered count outcome;
      D1/D2 separation rules, first-run separated cells marked); right, any new edition (D2, exploratory)
  F2  Project Gutenberg releases of renewed works per 1,000 by years since expiry (D2), against never-renewed works
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T, F = RUN / "results" / "tables", RUN / "results" / "figures"
F.mkdir(parents=True, exist_ok=True)
INK, INK2, GRID, SURF, BLUE, ORANGE, GREY = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb", "#2a78d6", "#e8a317", "#9a9893"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def f1():
    ev = pd.read_csv(T / "event_study.csv").dropna()
    eb = pd.read_csv(T / "event_study_binary.csv").dropna()
    pre = pd.read_csv(T / "event_study_pre_d1.csv")
    p = json.load(open(T / "primary.json"))
    pb = json.load(open(T / "secondary_binary.json"))
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.8), sharey=True)
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.14, top=0.8, wspace=0.08)
    for ax, d, o, title in ((axes[0], ev, p, "New editions per year (preregistered outcome)"),
                            (axes[1], eb, pb, "Any new edition in the year (exploratory)")):
        ax.axhline(0, color=INK2, lw=0.8); ax.axvline(-0.5, color=GREY, lw=0.8, ls=":")
        ax.errorbar(d.event, d.coef, yerr=1.96 * d.se, fmt="o", color=BLUE, ms=5, capsize=2, lw=1.2)
        ax.set_ylim(-3.6, 2.8); ax.set_xticks(range(-8, 7, 2)); ax.grid(axis="y", color=GRID, lw=0.5)
        ax.set_xlabel("years since copyright expiry (-1 is the reference)")
        ax.set_title(f"{title}\nRR (events 0-2) {o['rr']:.2f} ({o['rr_ci'][0]:.2f}-{o['rr_ci'][1]:.2f})",
                     fontsize=8.5, color=INK, loc="left")
    sep = pre[~pre.event.isin(ev.event) | (pre.coef < -2)]
    axes[0].plot(sep.event, sep.coef.clip(lower=-3.4), "x", color=ORANGE, ms=7, mew=1.6,
                 label="first run: separated cells (clipped at -3.4)")
    axes[0].legend(frameon=False, fontsize=7.5, loc="lower left")
    axes[0].set_ylabel("log rate ratio")
    fig.suptitle("A post-expiry rise in Open Library editions: fragile in counts, steadier in whether any edition appears",
                 x=0.02, ha="left", fontsize=10, color=INK)
    fig.savefig(F / "F1_event_study.png", dpi=170); plt.close(fig)
    caption("F1_event_study", f"""PPML with work and calendar-year fixed effects and saturated cohort x event-time dummies
    (Sun-Abraham), cohort-size weighted; 95% intervals clustered by work. {p['treated_works']} treated and
    {p['control_works']} control works have at least one edition in 2008-2025. Cells with zero outcome are separated and
    dropped (D1), as are cohorts with a zero reference cell (D2). Orange crosses: the first run's estimates for the
    separated cells (log RR to -12.8). Left: the preregistered count outcome; it depends on the 2024 cohort (without it,
    RR 1.12). Right: an exploratory binary outcome, any new edition in the year, added after review.""")


def f2():
    s = json.load(open(T / "secondary.json"))["gutenberg"]
    r = s["renewed_release_rate_per_1000_by_lag"]
    ks = sorted(r, key=int)
    fig, ax = plt.subplots(figsize=(7.4, 3.2))
    fig.subplots_adjust(left=0.1, right=0.97, bottom=0.16, top=0.84)
    ax.bar([int(k) for k in ks], [r[k]["rate"] for k in ks], color=BLUE, width=0.6,
           label="renewed works, releases per 1,000 works at risk")
    ax.axhline(s["never_renewed_release_rate_per_1000_per_year"], color=ORANGE, lw=1.6, ls="--",
               label=f"never-renewed works, same calendar years ({s['never_renewed_release_rate_per_1000_per_year']:.2f} per 1,000 per year)")
    for k in ks:
        ax.text(int(k), r[k]["rate"] + 0.1, f"n={r[k]['at_risk']:,}", ha="center", fontsize=6.5, color=INK2)
    ax.set_xlabel("years since US copyright expiry"); ax.set_ylabel("Gutenberg releases per 1,000")
    ax.set_xticks([int(k) for k in ks]); ax.grid(axis="y", color=GRID, lw=0.5); ax.legend(frameon=False, fontsize=7.5)
    fig.suptitle("After expiry, Gutenberg releases renewed books at 4-14 per 1,000 a year; before it, almost never",
                 x=0.02, ha="left", fontsize=10, color=INK)
    fig.savefig(F / "F2_gutenberg.png", dpi=170); plt.close(fig)
    caption("F2_gutenberg", f"""Linked renewed works (registered 1923-1929) released on Project Gutenberg (catalogue of
    2026-10-18; normalised title equal and author surname present), per 1,000 works whose lag year falls on or before 2026
    (n above each bar). Orange: never-renewed works' yearly release rate over the same calendar years. Overall,
    {100 * s['ever_on_gutenberg']['renewed_1923_1929']:.1f}% of renewed and {100 * s['ever_on_gutenberg']['never_renewed']:.2f}% of
    never-renewed linked works are on Gutenberg; {s['renewed_released_before_expiry']} renewed works were released before expiry.
    Long lags are observed only for the oldest cohorts, so the profile mixes cohorts; 2026 is a partial year.""")


if __name__ == "__main__":
    f1(); f2()
    print("figures written")
