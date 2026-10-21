"""Figures for the report (each PNG has a .txt caption). Written after the results.

  F1  installed distributed solar by month (behind-the-meter and all), with the panel's disclosure years
  F2  the four slopes against their thresholds and expected ranges, with minimum detectable effects
  F3  change in summer offtake per ICP against change in solar per ICP, 2014/15 to 2025/26: midday and evening
"""
import io
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_panel as bp  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T, F = RUN / "results" / "tables", RUN / "results" / "figures"
F.mkdir(parents=True, exist_ok=True)
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"
SUN, ALL, EVE = "#e8a317", "#2a78d6", "#8a5cd1"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def main():
    p = json.load(open(T / "primary.json"))
    rob = json.load(open(T / "robustness.json"))
    s = pd.read_csv(T / "panel_summer.csv")

    # F1 installed solar
    cap = bp.capacity()
    cap = cap[cap.pid.isin(bp.PARTICIPANT)].groupby("month")[["btm_mw", "solar_all_mw"]].sum()
    fig, ax = plt.subplots(figsize=(7.4, 3.4))
    fig.subplots_adjust(left=0.1, right=0.97, bottom=0.13, top=0.85)
    ax.plot(cap.index, cap.solar_all_mw, color=ALL, lw=2, label="all distribution-connected solar (incl. farms)")
    ax.plot(cap.index, cap.btm_mw, color=SUN, lw=2, label="behind the meter (residential + commercial)")
    ax.set_ylabel("installed capacity, MW"); ax.grid(axis="y", color=GRID, lw=0.5)
    ax.axvspan(pd.Timestamp("2014-04-01"), pd.Timestamp("2025-03-31"), color=GRID, alpha=0.45, lw=0)
    ax.text(pd.Timestamp("2014-07-01"), ax.get_ylim()[1] * 0.92, "disclosure years in the panel (2015-2025)",
            fontsize=7.5, color=INK2)
    ax.legend(frameon=False, fontsize=8, loc="upper left", bbox_to_anchor=(0.0, 0.86))
    fig.suptitle("New Zealand's distributed solar on the 29 distributors' networks", x=0.1, ha="left",
                 fontsize=10.5, color=INK)
    fig.savefig(F / "F1_installed_solar.png", dpi=170); plt.close(fig)
    caption("F1_installed_solar", """Installed distributed solar on the 29 distributors' networks, month-end, from the
    Electricity Authority's registry-based series. Behind-the-meter solar is the residential and commercial segments;
    the gap to all solar is the industrial segment, which holds the solar farms.""")

    # F2 slopes against thresholds
    rows = [("H1 net grid supply\nGWh per MW (annual)", p["H1"], -1.0, (-1.4, -1.0)),
            ("H2 energy delivered\nGWh per MW (annual)", p["H2"], -0.3, (-0.7, -0.35)),
            ("H3 winter peak\nMW per MW (annual)", p["H3"], None, (-0.05, 0.05)),
            ("H4 summer-midday offtake\nMW per MW (12 summers)", p["H4"], -0.3, (-0.6, -0.4)),
            ("midday minus evening\n(exploratory, D4)", {**rob["H4"]["mid_minus_eve"], "verdict": "not tested"},
             -0.3, (-0.6, -0.4))]
    fig, axs = plt.subplots(len(rows), 1, figsize=(7.4, 6.4))
    fig.subplots_adjust(left=0.27, right=0.97, bottom=0.06, top=0.9, hspace=0.95)
    for ax, (lab, r, thr, exp) in zip(axs, rows):
        lo, hi = r["ci"]
        ax.axvspan(*exp, color=SUN, alpha=0.25, lw=0)
        ax.axvline(0, color=INK2, lw=0.8)
        if thr is not None:
            ax.axvline(thr, color=INK, lw=1.0, ls="--")
        else:
            ax.axvspan(-0.2, 0.2, color=GRID, alpha=0.6, lw=0)
        ax.plot([lo, hi], [0, 0], color=ALL, lw=2.4, solid_capstyle="round")
        ax.plot([r["estimate"]], [0], "o", color=ALL, ms=6)
        ax.set_yticks([]); ax.set_ylabel(lab, rotation=0, ha="right", va="center", fontsize=8, color=INK)
        span = max(abs(lo), abs(hi), 1.5) * 1.1
        ax.set_xlim(-span, span)
        ax.text(1.0, 1.15, f"{r['estimate']:+.2f} ({lo:+.2f} to {hi:+.2f}); {r['verdict']}; MDE {r['mde_80']:.2f}",
                transform=ax.transAxes, ha="right", fontsize=7.5, color=INK2)
    fig.suptitle("Annual totals cannot see the solar; the half-hourly grid data can", x=0.03, ha="left",
                 fontsize=10.5, color=INK)
    fig.savefig(F / "F2_slopes.png", dpi=170); plt.close(fig)
    caption("F2_slopes", """Each preregistered slope with its 95% distributor-cluster bootstrap interval (blue), the
    preregistered threshold (dashed; for H3 the grey band is the +/-0.2 equivalence band) and the range expected from
    yield and self-consumption (shaded). The last row is the exploratory midday-minus-evening contrast of D4, which
    nets out changes in offtake common to all hours. Note the different horizontal scales: the annual intervals for H1-H3 are many
    times wider than the effects they were meant to detect.""")

    # F3 change vs change: midday, evening, and midday minus evening
    s["mid_pi"] = s.mid_mw * 1000 / s.icps
    s["eve_pi"] = s.eve_mw * 1000 / s.icps
    s["con_pi"] = s.mid_pi - s.eve_pi
    s["sol_pi"] = s.solar_all_mw * 1000 / s.icps
    a, b = s[s.summer == s.summer.min()].set_index("unit"), s[s.summer == s.summer.max()].set_index("unit")
    d = (b[["mid_pi", "eve_pi", "con_pi", "sol_pi"]] - a[["mid_pi", "eve_pi", "con_pi", "sol_pi"]]).dropna()
    names = {pid: n for pid, n in bp.PARTICIPANT.items()}
    fig, axs = plt.subplots(1, 3, figsize=(8.6, 3.6), sharey=True)
    fig.subplots_adjust(left=0.09, right=0.98, bottom=0.15, top=0.8, wspace=0.08)
    for ax, col, c, t in ((axs[0], "mid_pi", SUN, "midday 12:00-15:00"), (axs[1], "eve_pi", EVE, "evening 18:00-21:00"),
                          (axs[2], "con_pi", ALL, "midday minus evening")):
        ax.axhline(0, color=INK2, lw=0.8)
        ax.scatter(d.sol_pi, d[col], s=22, color=c, edgecolor=SURF, lw=0.8, zorder=3)
        ax.set_title(t, fontsize=8.5, color=INK, loc="left")
        ax.set_xlabel("change in solar, kW per ICP"); ax.grid(color=GRID, lw=0.5)
        for u, off in zip(d.sol_pi.nlargest(2).index, ((-7, -11), (-7, 6))):
            ax.annotate(names.get(u, u), (d.sol_pi[u], d[col][u]), xytext=off, textcoords="offset points",
                        fontsize=6.8, color=INK2, ha="right")
    axs[0].set_ylabel("change in summer grid offtake,\nkW per ICP")
    fig.suptitle("Summer 2014/15 to 2025/26: offtake fell most where solar grew, at midday and in the evening alike",
                 x=0.09, ha="left", fontsize=9.6, color=INK)
    fig.savefig(F / "F3_change_vs_change.png", dpi=170); plt.close(fig)
    caption("F3_change_vs_change", """Each point is one of the 24 grid-exit units (networks sharing grid exit points
    merged): the change between the first and last summers in mean net grid offtake per ICP against the change in
    installed solar per ICP (all distribution-connected solar, including farms). The two units with the largest
    solar growth per ICP are labelled; both added solar farms. Evening offtake fell with solar too, so the right-hand
    panel nets it out. The estimates in the report use all twelve summers with unit and summer fixed effects and
    temperature; this figure is descriptive.""")
    print("figures written")


if __name__ == "__main__":
    main()
