"""Figures (each PNG has a .txt caption). Written after multiverse.py.

  F1  specification curve for H1 (total mortality): standardised estimates sorted, coloured by WCR significance,
      with the window and economic-weakness measure marked below
  F2  share of specifications negative and significant, by window and measure (H1), and the H2 drug-poisoning curve
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
from multiverse import H1_DIMS, outcome  # noqa: E402

T, F = RUN / "results" / "tables", RUN / "results" / "figures"
F.mkdir(parents=True, exist_ok=True)
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"
NEG, POS, NS = "#2a78d6", "#d6532a", "#b9b7b0"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def standardise(df, P):
    sd = {}
    for o, w in df[["outcome", "window"]].drop_duplicates().itertuples(index=False):
        a, b = map(int, w.split("-"))
        sd[(o, w)] = float(np.nanstd(outcome(P[(P.year >= a) & (P.year <= b)], o)))
    s = np.array([sd[(o, w)] for o, w in zip(df.outcome, df.window)])
    return df.beta / s * 100, df.se / s * 100          # per 1 pp, in % of the outcome's SD


def curve(ax, df, P, sign):
    z, zs = standardise(df, P)
    order = np.argsort(z.to_numpy())
    z, zs = z.to_numpy()[order], zs.to_numpy()[order]
    sig = (df.p_wcr.to_numpy()[order] < 0.05)
    col = np.where(~sig, NS, np.where(z < 0, NEG, POS))
    x = np.arange(len(z))
    ax.vlines(x, z - 1.96 * zs, z + 1.96 * zs, color=col, lw=0.4, alpha=0.35)
    ax.scatter(x, z, c=col, s=2, lw=0)
    ax.axhline(0, color=INK2, lw=0.6)
    ax.set_xlim(-5, len(z) + 5)
    ax.grid(axis="y", color=GRID, lw=0.5)
    return order


def f1(p):
    P = pd.read_parquet(RUN / "data" / "interim" / "panel.parquet")
    h1 = pd.read_csv(T / "specs_h1.csv")
    fig = plt.figure(figsize=(8.2, 5.4))
    gs = fig.add_gridspec(3, 1, height_ratios=[3.2, 1.4, 0.5], hspace=0.08, left=0.15, right=0.98, top=0.88, bottom=0.08)
    ax = fig.add_subplot(gs[0])
    order = curve(ax, h1, P, -1)
    ax.set_ylabel("effect of +1 pp weakness\n(% of outcome SD)")
    ax.set_xticks([])
    ax2 = fig.add_subplot(gs[1], sharex=ax)
    wins = H1_DIMS["window"]
    for i, w in enumerate(wins):
        m = (h1.window.to_numpy()[order] == w)
        ax2.scatter(np.where(m)[0], np.full(m.sum(), i), s=1.2, color=INK2, lw=0)
    ax2.set_yticks(range(len(wins))); ax2.set_yticklabels(wins, fontsize=7); ax2.set_xticks([])
    ax2.invert_yaxis(); ax2.spines["left"].set_visible(False)
    ax3 = fig.add_subplot(gs[2], sharex=ax)
    m = (h1.treat.to_numpy()[order] == "ur")
    ax3.scatter(np.where(m)[0], np.zeros(m.sum()), s=1.2, color=INK2, lw=0)
    ax3.set_yticks([0]); ax3.set_yticklabels(["uses unemployment rate"], fontsize=7)
    ax3.set_xlabel(f"{len(h1):,} specifications, sorted by estimate"); ax3.spines["left"].set_visible(False)
    h = p["H1"]
    fig.suptitle(f"Total mortality: negative and significant in {h['S1_wcr']:.0%} of specifications; "
                 f"negative in {h['share_negative']:.0%}", x=0.02, ha="left", fontsize=10, color=INK)
    fig.text(0.02, 0.905, "blue: negative, WCR p < 0.05 · orange: positive, p < 0.05 · grey: not significant",
             fontsize=7.5, color=INK2)
    fig.savefig(F / "F1_spec_curve_h1.png", dpi=170); plt.close(fig)
    caption("F1_spec_curve_h1", f"""US states and DC, total mortality against economic weakness (the unemployment rate,
    or the negative employment-to-population ratio). Each point is one specification of the preregistered multiverse
    (outcome, measure, weighting, trends, lags, window, estimator, controls), standardised as the effect of a 1-point
    rise in weakness in percent of the outcome's standard deviation in that window, with 95% CR1 intervals. Colour is
    significance under the wild cluster restricted bootstrap (9,999 draws). Lower panels mark each specification's
    window and whether it uses the unemployment rate. Joint test: {h['joint_test']['observed_S1_cr1']:.0%} significant
    negative (CR1) against a null median of {h['joint_test']['null_median']:.1%}.""")


def f2(p):
    P = pd.read_parquet(RUN / "data" / "interim" / "panel.parquet")
    h1 = pd.read_csv(T / "specs_h1.csv")
    h2 = pd.read_csv(T / "specs_h2.csv")
    fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.4), gridspec_kw={"width_ratios": [1.1, 1]})
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.25, top=0.8, wspace=0.3)
    ax = axes[0]
    wins = H1_DIMS["window"]
    x = np.arange(len(wins))
    for k, (t, lab, col) in enumerate((("ur", "unemployment rate", "#2a78d6"), ("epop_neg", "−employment/population", "#9a9893"))):
        sh = [((h1.window == w) & (h1.treat == t) & (h1.beta < 0) & (h1.p_wcr < 0.05)).sum() / ((h1.window == w) & (h1.treat == t)).sum()
              for w in wins]
        ax.bar(x + (k - 0.5) * 0.38, sh, width=0.36, color=col, label=lab)
    ax.axhspan(0.4, 0.6, color="#e8a317", alpha=0.15, lw=0)
    ax.set_xticks(x); ax.set_xticklabels(wins, rotation=30, fontsize=7.5, ha="right")
    ax.set_ylim(0, 1); ax.set_ylabel("share negative and significant"); ax.grid(axis="y", color=GRID, lw=0.5)
    ax.legend(frameon=False, fontsize=7.5, loc="upper right")
    ax.set_title("H1 by window (band: Inconclusive zone)", fontsize=9, color=INK, loc="left")
    ax = axes[1]
    curve(ax, h2, P, 1)
    ax.set_xticks([]); ax.set_xlabel(f"{len(h2)} drug-poisoning specifications\n(windows 2011–2019 and 2011–2023)", fontsize=8)
    ax.set_title(f"H2: positive and significant in {p['H2']['S2_wcr']:.1%}", fontsize=9, color=INK, loc="left")
    ax.set_ylabel("% of outcome SD per +1 pp")
    fig.suptitle("The procyclical pattern needs the unemployment rate and pre-1992 years; post-2010 drug deaths do not track the cycle",
                 x=0.02, ha="left", fontsize=9.5, color=INK)
    fig.savefig(F / "F2_windows_h2.png", dpi=170); plt.close(fig)
    caption("F2_windows_h2", """Left: share of the H1 total-mortality specifications in each window that are negative and
    significant (WCR p < 0.05), by economic-weakness measure; the shaded band is the preregistered Inconclusive zone
    (0.40 to 0.60) for the pooled share. Right: the H2 specification curve for drug-poisoning mortality in post-2010
    windows, standardised as in F1; orange marks positive and significant (countercyclical) estimates.""")


if __name__ == "__main__":
    p = json.load(open(T / "primary.json"))
    f1(p); f2(p)
    print("figures written")
