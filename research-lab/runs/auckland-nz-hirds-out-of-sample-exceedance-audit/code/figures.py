"""Figures (PNG + .txt caption). Written after analyse.py on the corrected data.

  F1  observed/expected exceedances with 95% water-year block intervals, by duration and AEP, out of sample
  F2  year-by-year O/E for the primary (6 h, 10% AEP)
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T, F = RUN / "results" / "tables", RUN / "results" / "figures"
F.mkdir(parents=True, exist_ok=True)
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"
BLUE, ORANGE = "#2a78d6", "#d6532a"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def f1():
    s = json.loads((T / "secondary.json").read_text())
    p = json.loads((T / "primary.json").read_text())
    rows = [("1 h", "1h_10pct", "1h_2pct"), ("6 h (primary)", "6h_10pct", "6h_2pct"), ("24 h", "24h_10pct", "24h_2pct")]
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    fig.subplots_adjust(left=0.2, right=0.97, bottom=0.17, top=0.86)
    for i, (lab, k10, k2) in enumerate(rows):
        for dy, k, col, name in ((0.12, k10, BLUE, "10% AEP (10-year)"), (-0.12, k2, ORANGE, "2% AEP (50-year)")):
            r = s[k]
            ax.plot(r["ci"], [i + dy] * 2, color=col, lw=2, solid_capstyle="round")
            ax.plot(r["OE"], i + dy, "o", color=col, ms=8, mec=SURF, mew=2, label=name if i == 0 else None)
            ax.text(r["ci"][1] + 0.08, i + dy, f"{r['OE']:.2f}", va="center", fontsize=8, color=INK2)
    ins = p["sanity_in_sample"]
    ax.plot(ins["ci"], [-0.9] * 2, color="#9a9893", lw=2)
    ax.plot(ins["OE"], -0.9, "o", color="#9a9893", ms=8, mec=SURF, mew=2)
    ax.text(ins["ci"][1] + 0.08, -0.9, f"{ins['OE']:.2f}", va="center", fontsize=8, color=INK2)
    ax.set_yticks([-0.9, 0, 1, 2], ["in-sample control\n(6 h, 10%)", "1 h", "6 h (primary)", "24 h"])
    for x, ls in ((1.0, "-"), (1.3, "--")):
        ax.axvline(x, color=INK2, lw=0.8, ls=ls, zorder=0)
    ax.text(1.3, 2.55, "H1 bar (1.3)", fontsize=8, color=INK2, ha="center")
    ax.set_xlabel("observed / expected exceedances of HIRDS v4 depths (water years 2017/18-2025/26)")
    ax.set_xlim(0, 5.6); ax.set_ylim(-1.3, 2.75); ax.grid(axis="x", color=GRID, lw=0.5)
    ax.legend(frameon=False, loc="lower right", fontsize=8)
    fig.suptitle("HIRDS v4 depths exceeded more often than stated since 2017, with wide intervals",
                 x=0.02, ha="left", fontsize=9.5, color=INK)
    fig.savefig(F / "F1_oe_by_duration.png", dpi=170); plt.close(fig)
    caption("F1_oe_by_duration", f"""Observed over expected annual-maximum exceedances of HIRDS v4 historical depths at the
    gauges' coordinates, water years 2017/18-2025/26 (2018/19 onward where HIRDS fitted a gauge into 2017), with 95%
    water-year block bootstrap intervals (2,000 resamples). Expected = AEP x complete gauge-years. Grey: the in-sample
    control, water years up to 2014/15. {p['H1']['gauges']} council gauges from seven Hilltop servers; Auckland Council's
    gauges were harvested but none met the inclusion rule.""")


def f2():
    y = pd.read_csv(T / "year_by_year.csv")
    fig, ax = plt.subplots(figsize=(6.4, 3.0))
    fig.subplots_adjust(left=0.1, right=0.97, bottom=0.18, top=0.85)
    ax.bar([f"{w}/{(w + 1) % 100:02d}" for w in y.wy], y.OE, color=BLUE, width=0.62)
    ax.axhline(1.0, color=INK2, lw=0.8)
    for i, r in y.iterrows():
        ax.text(i, r.OE + 0.07, f"{int(r.exceed)}/{int(r.gauges)}", ha="center", fontsize=7.5, color=INK2)
    ax.set_ylabel("O/E (6 h, 10% AEP)"); ax.grid(axis="y", color=GRID, lw=0.5); ax.set_axisbelow(True)
    fig.suptitle("The excess is concentrated in four storm seasons", x=0.02, ha="left", fontsize=9.5, color=INK)
    fig.savefig(F / "F2_year_by_year.png", dpi=170); plt.close(fig)
    caption("F2_year_by_year", """Observed over expected exceedances of the 6-hour, 10% AEP HIRDS v4 depth by water year.
    Labels: exceeding gauges / complete gauge-years. 2022/23 is dominated by Cyclone Gabrielle (February 2023, 48
    Hawke's Bay gauges).""")


if __name__ == "__main__":
    f1(); f2(); print("figures written")
