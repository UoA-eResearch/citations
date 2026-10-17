"""Figures for the report (each PNG has a .txt caption).

  F1  how often the top-ranked treatment changes, by size of the update (latest year, newest ~10%, newest ~25%,
      oldest half -> all), with the random-holdout control and the rate when new entrants are counted
  F2  calibration: pre-update probability of being best (binned) against the share of networks whose top treatment
      keeps its place, for the primary holdout and the oldest-half horizon
  F3  which networks flip: the pre-update gap between the top two P-scores against the flip, with the fitted logistic
      curve of the H3 model at the median network size

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


def wilson(k, n, z=1.959964):
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - h, c + h


def load():
    n = pd.read_csv(T / "network_results.csv", dtype={"record": str})
    return n[n.included & (n.set == "primary")].copy()


def f1():
    P = load()
    rows = []
    for name, lab in [("S2", "latest year only"), ("T10", "newest ~10% (primary)"), ("S1", "newest ~25%"), ("S3", "oldest half → all")]:
        x = P.dropna(subset=[f"{name}_flip"])
        k, n = int(x[f"{name}_flip"].sum()), len(x)
        both = int(((x[f"{name}_flip"] == 1) | (x[f"{name}_new_entrant_top"] == 1)).sum())
        rows.append((lab, k / n, wilson(k, n), both / n, n))
    fig, ax = plt.subplots(figsize=(7.4, 3.6))
    fig.subplots_adjust(left=0.27, right=0.97, bottom=0.17, top=0.8)
    for i, (lab, p, (lo, hi), pb, n) in enumerate(rows):
        y = len(rows) - 1 - i
        ax.plot([lo, hi], [y, y], color=COL[0], lw=2, solid_capstyle="round")
        ax.plot(p, y, "o", color=COL[0], ms=8, mec=SURF, mew=2)
        ax.plot(pb, y, "D", color=COL[2], ms=6, mec=SURF, mew=1.5)
        ax.text(p, y + 0.22, f"{p:.0%}", ha="center", va="bottom", color=INK, fontsize=8)
        ax.text(pb, y + 0.22, f"{pb:.0%}", ha="center", va="bottom", color=INK2, fontsize=7.5)
    rc = P.random_flip_prob.mean()
    ax.axvline(rc, color=COL[1], lw=1.5, ls="--")
    ax.text(rc + 0.005, -0.75, f"random holdout, same size as primary: {rc:.0%}", color=INK2, fontsize=7.5)
    ax.axvline(0.30, color=INK2, lw=0.8, ls=":")
    ax.text(0.302, len(rows) - 0.45, "H1 threshold 30%", color=INK2, fontsize=7.5)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows][::-1])
    ax.set_xlim(0, 0.55); ax.set_ylim(-0.9, len(rows) - 0.2)
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.set_xlabel("share of networks whose top-ranked treatment changes")
    ax.grid(axis="x", color=GRID, lw=0.6); ax.set_axisbelow(True)
    h1 = plt.Line2D([], [], color=COL[0], marker="o", lw=2, label="among treatments already in the network (95% CI)")
    h2 = plt.Line2D([], [], color=COL[2], marker="D", lw=0, label="counting a newly added treatment that ranks first")
    ax.legend(handles=[h1, h2], loc="lower left", bbox_to_anchor=(-0.02, 1.0), ncol=1, frameon=False, fontsize=7.5)
    fig.savefig(F / "F1_flip_rates.png", dpi=200); plt.close(fig)
    caption("F1_flip_rates", f"""Share of {len(P)} arm-level networks whose top-ranked treatment (by P-score) changes when the
    withheld studies are added back, by size of the update. Circles count changes among treatments present before the
    update (the preregistered definition); diamonds also count a newly added treatment that ranks first. The dashed
    line is the mean flip probability over 200 random holdouts of the same size as the primary tranche.""")


def f2():
    P = load()
    fig, ax = plt.subplots(figsize=(4.8, 4.2))
    fig.subplots_adjust(left=0.15, right=0.96, bottom=0.14, top=0.92)
    ax.plot([0, 1], [0, 1], color=INK2, lw=0.8, ls=":")
    for name, lab, c, dx in [("T10", "newest ~10% withheld (primary)", COL[0], -0.01), ("S3", "oldest half → all", COL[2], 0.01)]:
        x = P.dropna(subset=[f"{name}_pbest_top", f"{name}_flip"])
        bins = [0, .2, .4, .6, .8, 1.0001]
        xs, ys, los, his, ns = [], [], [], [], []
        for a, b in zip(bins[:-1], bins[1:]):
            g = x[(x[f"{name}_pbest_top"] >= a) & (x[f"{name}_pbest_top"] < b)]
            if len(g) < 3:
                continue
            k = int((1 - g[f"{name}_flip"]).sum()); n = len(g)
            lo, hi = wilson(k, n)
            xs.append(g[f"{name}_pbest_top"].mean() + dx); ys.append(k / n); los.append(lo); his.append(hi); ns.append(n)
        ax.vlines(xs, los, his, color=c, lw=2)
        ax.plot(xs, ys, "o-", color=c, ms=7, mec=SURF, mew=2, lw=1.2, label=lab)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1.02)
    ax.set_xlabel("probability of being best, before the update (bin mean)")
    ax.set_ylabel("top treatment keeps its place")
    ax.grid(color=GRID, lw=0.6); ax.set_axisbelow(True)
    ax.legend(loc="lower right", frameon=False, fontsize=7.5)
    ax.text(0.03, 0.95, "above the diagonal: the probability\nunderstates how often the top holds", fontsize=7, color=INK2, va="top")
    fig.savefig(F / "F2_calibration.png", dpi=200); plt.close(fig)
    caption("F2_calibration", """Calibration of the pre-update probability of being best of the top-ranked treatment against
    the share of networks in which that treatment is still top-ranked once the withheld studies are added back. Bins
    of width 0.2 with at least 3 networks; bars are 95% Wilson intervals. Points above the diagonal mean the stated
    probability understates how often the top rank holds.""")


def f3():
    P = load()
    p = json.load(open(T / "primary.json"))["H3"]
    x = P.dropna(subset=["T10_gap", "T10_n_studies_pre"])
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    fig.subplots_adjust(left=0.12, right=0.97, bottom=0.17, top=0.9)
    rng = np.random.default_rng(1)
    jit = rng.uniform(-0.04, 0.04, len(x))
    for v, c, lab in [(0, COL[0], "top treatment holds"), (1, COL[2], "top treatment changes")]:
        g = x[x.T10_flip == v]
        ax.plot(g.T10_gap, g.T10_flip + jit[x.T10_flip.values == v], "o", color=c, ms=4.5, alpha=0.75, mec=SURF, mew=0.6, label=lab)
    gs = np.linspace(0, x.T10_gap.max(), 200)
    lk = np.log(x.T10_n_studies_pre.median())
    cf = p["coef"]
    ax.plot(gs, 1 / (1 + np.exp(-(cf["const"] + cf["gap"] * gs + cf["log_k"] * lk))), color=INK, lw=1.5,
            label=f"fitted probability of a change (median network); R² = {p['nagelkerke_r2']:.2f}")
    ax.set_xlabel("gap between the top two P-scores before the update")
    ax.set_yticks([0, 0.5, 1]); ax.set_ylabel("change")
    ax.grid(color=GRID, lw=0.6); ax.set_axisbelow(True)
    ax.legend(loc="center right", frameon=False, fontsize=7.5)
    fig.savefig(F / "F3_gap.png", dpi=200); plt.close(fig)
    caption("F3_gap", f"""Each point is one of {len(x)} networks, by the pre-update gap between its top two P-scores and whether
    its top treatment changed when the newest tranche was added back (jittered vertically). The curve is the H3
    logistic model at the median number of pre-update studies; with network size it explains a Nagelkerke R² of
    {p['nagelkerke_r2']:.2f} of which networks flip.""")


if __name__ == "__main__":
    f1(); f2(); f3()
    print(sorted(p.name for p in F.iterdir()))
