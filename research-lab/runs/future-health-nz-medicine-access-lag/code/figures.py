"""Figures for the report (each PNG has a .txt caption).

  F1  where the time goes: median days per stage (sponsor T0->T1, Medsafe T1->T2, funding T2->T3) among funded
      substances with all four dates, by period of first international approval (results/tables/stage_table.csv)
  F2  cumulative share reaching each milestone after first international approval (Kaplan-Meier, 1 - S): Medsafe
      consent, TGA registration, PHARMAC funding (whole cohort), and PBS listing for T0 2019-2024
  F3  the denominator problem: Medsafe consent to funding (years) under three denominators, against 7.7 years

Palette: the dataviz skill's reference slots in fixed order; one hue per milestone.
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from lifelines import KaplanMeierFitter  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analysis import load  # noqa: E402

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


def f1():
    st = pd.read_csv(T / "stage_table.csv")
    fig, ax = plt.subplots(figsize=(7.6, 3.2))
    fig.subplots_adjust(left=0.2, right=0.97, bottom=0.18, top=0.86)
    labs = ["sponsor files in NZ", "Medsafe review", "funding (PHARMAC)"]
    for i, r in enumerate(st.itertuples()):
        y = len(st) - 1 - i; left = 0
        for k, v in enumerate([r.sponsor_median, r.medsafe_median, r.funding_median]):
            ax.barh(y, v, left=left, color=COL[k], height=0.6, edgecolor=SURF, lw=2, label=labs[k] if i == 0 else None)
            left += v
    ax.set_yticks(range(len(st))); ax.set_yticklabels([f"{p} (n = {n})" for p, n in zip(st.period, st.n)][::-1])
    ax.set_xlabel("median days per stage (stacked), from first FDA/EMA approval")
    ax.grid(axis="x", color=GRID, lw=0.6); ax.set_axisbelow(True)
    ax.legend(frameon=False, ncol=3, loc="lower left", bbox_to_anchor=(0, 1.0), fontsize=8)
    fig.savefig(F / "F1_stages.png", dpi=200); plt.close(fig)
    caption("F1_stages", """Median days in each stage for new active substances that were eventually funded and have
    all four dates, by period of first international approval. Stacked medians do not sum to the median total.""")


def f2():
    d, cutoff = load()
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    fig.subplots_adjust(left=0.1, right=0.97, bottom=0.14, top=0.92)
    tga_cut = min(cutoff, d.t_tga.max()) if d.t_tga.notna().any() else cutoff
    au = d[(d.t0.dt.year >= 2019)]
    series = [("Medsafe consent (NZ)", d, "t2", cutoff), ("TGA registration (AU)", d, "t_tga", tga_cut),
              ("PHARMAC funded listing (NZ)", d, "t3", cutoff), ("PBS listing (AU, T0 2019-24)", au, "t3_au", min(cutoff, pd.Timestamp("2026-10-01")))]
    for k, (lab, x, col, cut) in enumerate(series):
        ev = x[col].notna() & (x[col] <= cut)
        dur = (x[col].where(ev).fillna(cut) - x.t0).dt.days.clip(lower=0) / 365.25
        kmf = KaplanMeierFitter().fit(dur, ev)
        sf = kmf.survival_function_
        ax.step(sf.index, 1 - sf.iloc[:, 0], where="post", color=COL[k], lw=2, label=f"{lab} (n = {len(x)})")
    ax.set_xlim(0, 12); ax.set_ylim(0, 1)
    ax.set_xlabel("years since first FDA/EMA approval"); ax.set_ylabel("share reached (Kaplan-Meier)")
    ax.grid(color=GRID, lw=0.6); ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    fig.savefig(F / "F2_milestones.png", dpi=200); plt.close(fig)
    caption("F2_milestones", """Cumulative share of new active substances (first approved by FDA or EMA 2010-2024)
    reaching each milestone, by years since that first approval; substances not yet reaching it are censored at the
    data cutoff. The PBS curve covers only substances first approved 2019-2024, the era the Medicine Status Website
    records.""")


def f3():
    p = json.load(open(T / "primary.json"))
    h = p["H3_denominators_T2_T3_years"]
    rows = [("Funded only: mean", h["funded_only"]["mean"]), ("Funded only: median", h["funded_only"]["median"]),
            ("All consented: KM median", h["consented_km"]["median"]), ("All consented: mean to 10 y (RMST)", h["consented_km"]["rmst_10y"])]
    fig, ax = plt.subplots(figsize=(7.0, 2.6))
    fig.subplots_adjust(left=0.36, right=0.96, bottom=0.2, top=0.9)
    for i, (lab, v) in enumerate(rows):
        y = len(rows) - 1 - i
        if v is None:
            ax.text(0.1, y, "not reached", va="center", color=INK2, fontsize=8)
        else:
            ax.barh(y, v, color=COL[0], height=0.55)
            ax.text(v + 0.1, y, f"{v:.1f}", va="center", color=INK, fontsize=8)
    ax.axvline(7.7, color=COL[2], ls="--", lw=1); ax.text(7.75, len(rows) - 0.5, "7.7 years (industry figure)", color=INK2, fontsize=7.5, va="bottom")
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows][::-1])
    ax.set_xlabel("years from Medsafe consent to PHARMAC funded listing")
    ax.grid(axis="x", color=GRID, lw=0.6); ax.set_axisbelow(True)
    fig.savefig(F / "F3_denominators.png", dpi=200); plt.close(fig)
    caption("F3_denominators", """Medsafe consent to PHARMAC funding under different denominators. Counting only
    medicines that were funded gives short waits; counting every consented medicine, with those not yet funded
    censored, gives much longer ones. Restricted mean to 10 years caps each wait at 10 years.""")


if __name__ == "__main__":
    f1(); f2(); f3()
    print(sorted(p.name for p in F.iterdir()))
