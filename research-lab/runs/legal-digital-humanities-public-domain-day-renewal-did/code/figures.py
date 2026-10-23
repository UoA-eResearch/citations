"""Figures for the report (each PNG has a .txt caption). Written after did.py and secondary.py.

  F1  event-study rate ratios (PPML, Sun-Abraham, cohort-weighted), before and after D1's separation rule
  F2  Project Gutenberg releases within 0-2 years of expiry, renewed works by expiry year vs never-renewed
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
    pre = pd.read_csv(T / "event_study_pre_d1.csv")
    p = json.load(open(T / "primary.json"))
    fig, ax = plt.subplots(figsize=(7.4, 3.8))
    fig.subplots_adjust(left=0.1, right=0.97, bottom=0.13, top=0.86)
    ax.axhline(0, color=INK2, lw=0.8); ax.axvline(-0.5, color=GREY, lw=0.8, ls=":")
    ax.errorbar(ev.event, ev.coef, yerr=1.96 * ev.se, fmt="o", color=BLUE, ms=5, capsize=2, lw=1.2,
                label="D1: separated cells dropped")
    sep = pre[~pre.event.isin(ev.event) | (pre.coef < -2)]
    ax.plot(sep.event, sep.coef.clip(lower=-3.4), "x", color=ORANGE, ms=7, mew=1.6,
            label="first run: separated cells (clipped at -3.4)")
    ax.set_ylim(-3.6, 2.6); ax.set_xticks(range(-8, 7))
    ax.set_xlabel("years since copyright expiry (event time; -1 is the reference)")
    ax.set_ylabel("log rate ratio of new editions")
    ax.grid(axis="y", color=GRID, lw=0.5); ax.legend(frameon=False, fontsize=8, loc="lower left")
    fig.suptitle("A post-expiry rise in Open Library editions, on thin data", x=0.02, ha="left", fontsize=10.5, color=INK)
    fig.savefig(F / "F1_event_study.png", dpi=170); plt.close(fig)
    caption("F1_event_study", f"""PPML with work and calendar-year fixed effects and saturated cohort x event-time dummies
    (Sun-Abraham), cohort-size weighted; 95% intervals clustered by work. {p['treated_works']} treated and
    {p['control_works']} control works have at least one edition in 2008-2025. Blue: after D1 (cohort x event cells with
    zero editions are separated and dropped). Orange crosses: the first run's estimates for those cells (log RR to -12.8).
    Primary RR (events 0-2) {p['rr']:.2f} ({p['rr_ci'][0]:.2f}-{p['rr_ci'][1]:.2f}); pre-trend Wald p = {p['pretrend_wald_p']:.2f}.""")


def f2():
    s = json.load(open(T / "secondary.json"))["gutenberg"]
    yrs = sorted(s["by_expiry_year"], key=int)
    fig, ax = plt.subplots(figsize=(7.4, 3.2))
    fig.subplots_adjust(left=0.1, right=0.97, bottom=0.15, top=0.84)
    ax.bar([int(y) for y in yrs], [100 * s["by_expiry_year"][y]["share"] for y in yrs], color=BLUE, width=0.6,
           label="renewed works, by expiry year")
    ax.axhline(100 * s["never_renewed_same_windows"], color=ORANGE, lw=1.6, ls="--",
               label=f"never-renewed works, same calendar windows ({100 * s['never_renewed_same_windows']:.2f}%)")
    ax.set_ylabel("% released on Gutenberg within 0-2 years"); ax.set_xticks([int(y) for y in yrs])
    ax.grid(axis="y", color=GRID, lw=0.5); ax.legend(frameon=False, fontsize=8, loc="upper right")
    fig.suptitle("Project Gutenberg picks up newly expired books", x=0.02, ha="left", fontsize=10.5, color=INK)
    fig.savefig(F / "F2_gutenberg.png", dpi=170); plt.close(fig)
    caption("F2_gutenberg", f"""Linked works released on Project Gutenberg (catalogue of 2026-10-18; normalised title equal and
    author surname present) within 0-2 years after their US expiry. Renewed works {100 * s['renewed_released_0_2y_after_expiry']:.2f}%
    (n = {s['renewed_n']:,}); never-renewed works over the same calendar windows {100 * s['never_renewed_same_windows']:.2f}%
    (n = {s['never_renewed_n']:,}). Recent cohorts have had less time and less backlog clearance.""")


if __name__ == "__main__":
    f1(); f2()
    print("figures written")
