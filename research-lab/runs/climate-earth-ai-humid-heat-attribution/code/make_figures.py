#!/usr/bin/env python
"""Figures for the report (results/figures/F*.png, each with a caption file)."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB, FIG = RUN / "results" / "tables", RUN / "results" / "figures"
BLUE, ORANGE, AQUA, INK, MUTED, GRID, NAVY, RED = "#2a78d6", "#eb6834", "#1baf7a", "#0b0b0b", "#898781", "#e1e0d9", "#104281", "#c0392b"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": "#c3c2b7", "axes.linewidth": 0.8, "axes.grid": True,
                     "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True, "xtick.color": "#52514e",
                     "ytick.color": "#52514e", "axes.labelcolor": INK, "axes.titlesize": 9.5, "legend.frameon": False,
                     "savefig.dpi": 160, "savefig.bbox": "tight", "figure.constrained_layout.use": True})


def caption(name, text):
    (FIG / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def label(ev, eid):
    r = ev.set_index("event_id").loc[eid]
    return f"{eid} {r.region}\n{str(r.date)[:10]}"


def f1_skill(ev):
    p = pd.read_csv(TAB / "per_forecast.csv")
    fig, ax = plt.subplots(figsize=(8, 3.2))
    x = np.arange(len(ev))
    for j, (L, col) in enumerate(zip((2, 4, 6), (NAVY, BLUE, MUTED))):
        s = p[p.lead == L].set_index("event").reindex(ev.event_id)
        ax.bar(x + (j - 1) * 0.26, s.err_peak, 0.26, color=col, label=f"lead {L} days")
    ax.axhline(0, color=INK, lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([label(ev, e) for e in ev.event_id], fontsize=7.5)
    ax.set_ylabel("forecast minus ERA5 peak\nwet-bulb temperature (degC)")
    ax.legend(fontsize=8)
    fig.savefig(FIG / "F1_skill.png")
    plt.close(fig)
    caption("F1_skill", """F1. How well the factual AIFS forecasts reproduce each event: forecast minus ERA5 event-peak
2 m wet-bulb temperature (regional maximum on the event day), by lead time.""")


def f2_attribution(ev):
    a = pd.read_csv(TAB / "attribution.csv")
    fig, ax = plt.subplots(figsize=(9, 3.6))
    x = np.arange(len(ev))
    for j, (col, lab, c) in enumerate((("dA_peak", "temperature only (A), forecast", ORANGE),
                                       ("dB_peak", "constant relative humidity (B), forecast", NAVY),
                                       ("static_dA_peak", "A, static (no forecast)", "#f5b49a"),
                                       ("static_dB_peak", "B, static (no forecast)", "#8fb3de"))):
        g = a[a.lead == 2].groupby("event")[col]
        m, lo, hi = g.mean().reindex(ev.event_id), g.min().reindex(ev.event_id), g.max().reindex(ev.event_id)
        xx = x + (j - 1.5) * 0.2
        ax.errorbar(xx, m, yerr=[m - lo, hi - m], fmt="o", color=c, ms=5, capsize=2, label=lab)
    ax.set_xticks(x)
    ax.set_xticklabels([label(ev, e) for e in ev.event_id], fontsize=7.5)
    ax.set_ylabel("attributable change in peak\nwet-bulb temperature (degC)")
    ax.axhline(0, color=INK, lw=0.8)
    ax.legend(fontsize=7.5, ncol=2, loc="upper right")
    fig.savefig(FIG / "F2_attribution.png")
    plt.close(fig)
    caption("F2_attribution", """F2. How much warmer the event-peak wet-bulb temperature is in the factual forecast than in a
counterfactual forecast without the warming since 1850-1900, at a 2-day lead: dots are means over the six CMIP6 warming
signals, bars their range. Orange: warming removed from temperature only (specific humidity unchanged); blue: relative
humidity held fixed, so moisture is removed too. Pale colours: the same changes applied to the ERA5 event-day fields
with no forecast (static).""")


def f3_lead():
    a = pd.read_csv(TAB / "attribution.csv")
    g = a.groupby("lead")[["dA_peak", "dB_peak"]].mean()
    s = a.groupby("lead")[["static_dA_peak", "static_dB_peak"]].mean()
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.2))
    ax = axes[0]
    ax.plot(g.index, g.dA_peak, "o-", color=ORANGE, label="temperature only (A)")
    ax.plot(g.index, g.dB_peak, "o-", color=NAVY, label="constant relative humidity (B)")
    ax.axhline(s.static_dA_peak.mean(), color=ORANGE, ls=":", lw=1)
    ax.axhline(s.static_dB_peak.mean(), color=NAVY, ls=":", lw=1)
    ax.set_xlabel("lead time (days)")
    ax.set_ylabel("mean attributable change (degC)")
    ax.legend(fontsize=8)
    ax.set_xticks([2, 4, 6])
    ax = axes[1]
    r = a.groupby(["lead"]).apply(lambda d: d.dB_peak.mean() / d.dA_peak.mean())
    rs = a.static_dB_peak.mean() / a.static_dA_peak.mean()
    ax.plot(r.index, r.values, "o-", color=INK, label="forecast")
    ax.axhline(rs, color=MUTED, ls=":", label="static")
    ax.axhline(1.5, color=RED, ls="--", lw=0.8, label="H1 threshold")
    ax.set_xlabel("lead time (days)")
    ax.set_ylabel("ratio B / A")
    ax.set_xticks([2, 4, 6])
    ax.legend(fontsize=8)
    fig.savefig(FIG / "F3_lead.png")
    plt.close(fig)
    caption("F3_lead", """F3. Left: mean attributable change in event-peak wet-bulb temperature by lead time, for the two
moisture treatments (solid), against the static values (dotted). Right: the ratio of the two (H1), with the static ratio
and the preregistered threshold of 1.5.""")


def f4_drift():
    a = pd.read_csv(TAB / "attribution.csv")
    fig, ax = plt.subplots(figsize=(5, 3.4))
    for L, col in zip((2, 4, 6), (NAVY, BLUE, MUTED)):
        s = a[a.lead == L]
        ax.scatter(s.gm_imposed, s.gm_2t_F_minus_B, s=12, color=col, label=f"lead {L} days")
    lim = [0, max(a.gm_imposed.max(), a.gm_2t_F_minus_B.max()) * 1.1]
    ax.plot(lim, lim, color=INK, lw=0.8, ls=":")
    ax.set_xlabel("imposed global-mean 2 m cooling (degC)")
    ax.set_ylabel("factual minus counterfactual (B)\nglobal-mean 2 m temperature at the end (degC)")
    ax.legend(fontsize=8)
    fig.savefig(FIG / "F4_drift.png")
    plt.close(fig)
    caption("F4_drift", """F4. Does the AI model keep the imposed warming signal? Global-mean (cos-latitude weighted) 2 m temperature difference
between the factual and constant-relative-humidity counterfactual forecasts at the end of each forecast, against the
global-mean signal imposed at the start (dotted: kept in full).""")


def f5_linearity():
    c = pd.read_csv(TAB / "control_linearity.csv")
    fig, ax = plt.subplots(figsize=(5.4, 3.6))
    for w, col, off in (("A", ORANGE, -0.03), ("B", NAVY, 0.03)):
        s = c[c.world == w]
        ax.scatter(s.scale + off, s.dTW_peak, s=12, color=col, alpha=0.5)
        g = s.groupby("scale").dTW_peak.mean()
        ax.plot(g.index, g.values, "o-", color=col, lw=1.5,
                label={"A": "temperature only (A)", "B": "constant relative humidity (B)"}[w])
    ax.axhline(0, color=INK, lw=0.8)
    ax.axvline(0, color=INK, lw=0.8)
    ax.plot([-1, 1], [-1.4, 1.4], color=MUTED, ls=":", lw=1)
    ax.set_xticks([-1, 0, 0.5, 1])
    ax.set_xticklabels(["-1\n(warming added)", "0", "0.5", "1\n(warming removed)"], fontsize=8)
    ax.set_xlabel("scale applied to the CMIP6 warming signal")
    ax.set_ylabel("change in event-peak wet-bulb\ntemperature, factual minus scaled (degC)")
    ax.legend(fontsize=8, loc="upper left")
    fig.savefig(FIG / "F5_linearity.png")
    plt.close(fig)
    caption("F5_linearity", """F5. Control: does the forecast respond to the imposed signal, or to any disturbance of the
starting state? For two events (E1, E5) at a 2-day lead, the warming signal was scaled by 1 (removed, as in the main
runs), 0.5, and -1 (added instead). Dots: the six CMIP6 signals; lines: their means. The change flips sign and scales
roughly in proportion, so it is a real response to the signal, with only a small component that keeps its sign.""")


if __name__ == "__main__":
    FIG.mkdir(parents=True, exist_ok=True)
    ev = pd.read_csv(TAB / "events.csv")
    for f in (lambda: f1_skill(ev), lambda: f2_attribution(ev), f3_lead, f4_drift, f5_linearity):
        f()
    print("figures written")
