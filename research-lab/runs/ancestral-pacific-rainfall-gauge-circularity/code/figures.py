"""Figures for the report (each PNG has a .txt caption).

  F1  blending gain g = 1 - RMSE(CHIRPS)/RMSE(CHIRP) by station, supported (input station within 25 km) against
      independent (none within 100 km) strata, with the station means and the H1 ratio
  F2  station-mean dKGE (CHIRPS - CHIRP) at independent gauges, primary pair and the secondary PERSIANN pair if done
  F3  the share of station-months that are supported, intermediate or independent, by decade, and the stations a
      CHIRPS input lies on (within 5 km)
Palette: the dataviz skill's reference slots in fixed order.
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
COL = ["#2a78d6", "#1baf7a", "#eb6834", "#8a5cd1"]
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def main():
    p = json.load(open(T / "primary.json")); r = p["results"]["primary"]
    sk = pd.read_csv(T / "station_skill.csv")
    pr = sk[sk.variant == "primary"]
    rng = np.random.default_rng(1)
    # F1
    fig, ax = plt.subplots(figsize=(7.4, 3.8)); fig.subplots_adjust(left=0.1, right=0.88, bottom=0.14, top=0.84)
    for i, (st, lab) in enumerate((("supported", "supported (input ≤ 25 km)"), ("independent", "independent (none ≤ 100 km)"))):
        g = pr[pr.stratum == st].gain.values
        ax.scatter(i + rng.uniform(-0.18, 0.18, len(g)), g, s=14, color=COL[i], alpha=0.6, lw=0)
        m = r["gain_supported"] if st == "supported" else r["gain_independent"]
        ci = r["gain_supported_ci"] if st == "supported" else r["gain_independent_ci"]
        ax.plot([i - 0.3, i + 0.3], [m, m], color=INK, lw=2); ax.plot([i, i], ci, color=INK, lw=1.2)
        ax.text(i + 0.33, m, f"{m:.3f}\n(n = {len(g)})", va="center", fontsize=8, color=INK2)
    ax.axhline(0, color=GRID, lw=1)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["supported (input ≤ 25 km)", "independent (none ≤ 100 km)"])
    ax.set_ylabel("blending gain  1 − RMSE(CHIRPS)/RMSE(CHIRP)"); ax.grid(axis="y", color=GRID, lw=0.6)
    lo, hi = r["ratio_ci"]
    fig.suptitle(f"Blending gain at gauges CHIRPS ingested versus gauges it did not: ratio {r['ratio']:.2f} ({lo:.2f}–{hi:.2f})",
                 x=0.1, ha="left", fontsize=10.5, color=INK)
    fig.savefig(F / "F1_gain_by_stratum.png", dpi=170); plt.close(fig)
    caption("F1_gain_by_stratum", f"""Blending gain per station and stratum on pentad totals (1981-2025), primary thresholds
    (25 / 100 km). Points: stations with at least 30 pentads in the stratum. Black bars: station means with 95% station-block
    bootstrap intervals (2,000 resamples). The H1 ratio is the independent mean over the supported mean.""")
    # F2
    rows = [("CHIRPS vs CHIRP (primary)", r["dkge_independent"], r["dkge_independent_ci"], pr[pr.stratum == "independent"].dkge.values)]
    sec = p.get("secondary", {})
    if sec.get("status") == "done" and "dkge_independent" in sec:
        ss = pd.read_csv(T / "station_skill_secondary.csv")
        rows.append(("PERSIANN-CDR vs PERSIANN (secondary)", sec["dkge_independent"], sec["dkge_independent_ci"],
                     ss[ss.stratum == "independent"].dkge.values))
    fig, ax = plt.subplots(figsize=(7.4, 1.6 + 1.0 * len(rows))); fig.subplots_adjust(left=0.42, right=0.97, bottom=0.25, top=0.78)
    for i, (lab, m, ci, v) in enumerate(rows):
        y = len(rows) - 1 - i
        ax.scatter(v, y + rng.uniform(-0.15, 0.15, len(v)), s=12, color=COL[0], alpha=0.45, lw=0)
        ax.plot(ci, [y, y], color=INK, lw=2); ax.plot(m, y, "o", color=INK, ms=7)
    ax.axvline(0, color=COL[2], lw=1.2, ls="--")
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([x[0] for x in rows][::-1])
    ax.set_xlabel("ΔKGE at independent gauges (blended − satellite-only)"); ax.grid(axis="x", color=GRID, lw=0.6)
    fig.suptitle("Is the blended product better where it saw no gauge? (H2)", x=0.42, ha="left", fontsize=10.5, color=INK)
    fig.savefig(F / "F2_dkge_independent.png", dpi=170); plt.close(fig)
    caption("F2_dkge_independent", """Station ΔKGE (blended minus satellite-only twin) at independent gauges (dots) with the
    station mean and its 95% station-block bootstrap interval. Left of the dashed line the satellite-only twin is better.""")
    # F3
    lab = pd.read_csv(RUN / "data" / "labels.csv")
    lab["decade"] = lab.ym.str[:3] + "0s"
    lab["cls"] = np.where(lab.nearest_km <= 25, "supported", np.where(lab.nearest_km > 100, "independent", "intermediate"))
    sh = lab.groupby("decade").cls.value_counts(normalize=True).unstack().fillna(0)[["supported", "intermediate", "independent"]]
    fig, ax = plt.subplots(figsize=(7.4, 3.4)); fig.subplots_adjust(left=0.1, right=0.78, bottom=0.14, top=0.84)
    bottom = np.zeros(len(sh))
    for k, c in enumerate(sh.columns):
        ax.bar(sh.index, sh[c], bottom=bottom, color=COL[k], width=0.7, edgecolor=SURF, linewidth=2)
        bottom += sh[c].values
    for k, c in enumerate(sh.columns):
        ax.text(len(sh) - 0.55, sh.iloc[-1][: k + 1].sum() - sh.iloc[-1][c] / 2, c, va="center", fontsize=8.5, color=INK2)
    ax.set_ylabel("share of gauge-months (all 148 stations)"); ax.set_ylim(0, 1)
    fig.suptitle("How often a Pacific gauge has a CHIRPS input station nearby", x=0.1, ha="left", fontsize=10.5, color=INK)
    fig.savefig(F / "F3_label_shares.png", dpi=170); plt.close(fig)
    caption("F3_label_shares", """Share of station-months whose nearest CHIRPS input station that month is within 25 km
    (supported), 25-100 km (intermediate) or beyond 100 km (independent), by decade, from the CHIRPS monthly
    stations-used lists, for all 148 GHCN-Daily Pacific stations whether or not they report.""")
    print("figures written")


if __name__ == "__main__":
    main()
