"""Figures for the report (each PNG has a .txt caption).

  F1  MEF by horizon with 95% bootstrap intervals; horizons with a first-stage F below 10 drawn hollow and clipped;
      the 2015-2024 mean AEF as a reference line
  F2  where weather-driven demand is met: the 2SLS response of hydro, thermal and geothermal generation per MWh of
      extra demand, for the strongly identified horizons (0.5 h to 7 d)
  F3  time-of-day MEF at 1 day by 6-hour block of the window's start, against the block's mean AEF
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

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
    m = json.load(open(T / "mef.json")); sim = json.load(open(T / "simulation.json"))
    H = m["horizons"]
    aef = float(np.mean(list(sim["aef_by_block_mean"].values())))
    hours = np.array([r["h"] / 2 for r in H])
    # F1
    fig, ax = plt.subplots(figsize=(7.4, 3.8)); fig.subplots_adjust(left=0.1, right=0.97, bottom=0.16, top=0.86)
    top = 1.6
    for x, r in zip(hours, H):
        strong = r["first_stage_F"] >= 10
        lo, hi = max(r["ci"][0], -0.2), min(r["ci"][1], top)
        ax.plot([x, x], [lo, hi], color=COL[0], lw=2, alpha=1 if strong else 0.45, solid_capstyle="round")
        y = min(r["mef"], top)
        ax.plot(x, y, "o", ms=7, mfc=COL[0] if strong else SURF, mec=COL[0], mew=1.6)
        if not strong:
            off = "" if r["mef"] <= top else f"\nestimate {r['mef']:.1f}, off scale"
            ax.annotate(f"F = {r['first_stage_F']:.1f} (weak){off}", (x, y if off == "" else 0.45), xytext=(-10, -4),
                        textcoords="offset points", ha="right", fontsize=7.5, color=INK2)
    ax.axhline(aef, color=COL[2], lw=1.4, ls="--")
    ax.text(hours[0], aef - 0.09, f"mean average emissions factor (AEF) {aef:.2f}", color=COL[2], fontsize=8)
    ax.set_xscale("log"); ax.set_xticks(hours); ax.set_xticklabels([r["label"] for r in H])
    ax.set_ylim(-0.2, top + 0.15); ax.grid(axis="y", color=GRID, lw=0.6)
    ax.set_ylabel("t CO₂ per MWh of extra demand"); ax.set_xlabel("horizon over which emissions are counted")
    fig.suptitle("Marginal emissions rise with the horizon over which they are counted (preregistered specification)", x=0.1, ha="left", fontsize=10.5, color=INK)
    fig.savefig(F / "F1_mef_by_horizon.png", dpi=170); plt.close(fig)
    caption("F1_mef_by_horizon", f"""Marginal emissions factor MEF(h) by horizon, 2SLS with the heating-degree anomaly as instrument,
    2015-2024, n = {m['n']:,} half-hours. Bars are 95% calendar-month block-bootstrap intervals (999 resamples). Hollow
    markers: first-stage F below 10 (14 and 30 days), intervals clipped at the axis. Dashed line: mean AEF over the
    period ({aef:.3f} t/MWh). The levels depend on the control set (results/tables/sensitivity.json: 1 h -0.16 to 0.23,
    7 d 0.13 to 0.79 across 17 specifications); the rise from 1 h to 1 d and to 7 d holds in every one.""")
    # F2
    S = [r for r in H if r["first_stage_F"] >= 10]
    x = np.array([r["h"] / 2 for r in S])
    fig, ax = plt.subplots(figsize=(7.4, 3.6)); fig.subplots_adjust(left=0.1, right=0.8, bottom=0.16, top=0.86)
    for k, (key, lab) in enumerate((("hydro", "hydro"), ("thermal", "thermal (coal, gas, diesel)"), ("geo", "geothermal"))):
        y = [r[key] for r in S]
        ax.plot(x, y, "-o", color=COL[k], lw=2, ms=5, mec=SURF, mew=1.2)
        ax.text(x[-1] * 1.12, y[-1], lab, color=INK2, va="center", fontsize=8.5)
    ax.axhline(0, color=GRID, lw=1); ax.axhline(1, color=GRID, lw=1, ls=":")
    ax.set_xscale("log"); ax.set_xticks(x); ax.set_xticklabels([r["label"] for r in S])
    ax.set_ylabel("MWh generated per MWh of extra demand"); ax.set_xlabel("horizon"); ax.grid(axis="y", color=GRID, lw=0.6)
    fig.suptitle("Where weather-driven demand is met under the preregistered controls (not robust; see text)", x=0.1, ha="left", fontsize=10.5, color=INK)
    fig.savefig(F / "F2_generation_response.png", dpi=170); plt.close(fig)
    caption("F2_generation_response", """2SLS response of cumulative hydro, thermal and geothermal generation to weather-driven demand,
    per MWh of extra demand, for the horizons with a first-stage F of at least 10. Wind over the window is held fixed by
    design. Point estimates under the preregistered controls; the split changes materially with the control set (with
    window inflow controlled, hydro 0.49 and thermal 0.50 at 7 days).""")
    # F3
    bl = m["blocks_1d"]; ab = sim["aef_by_block_mean"]
    fig, ax = plt.subplots(figsize=(7.4, 3.6)); fig.subplots_adjust(left=0.1, right=0.97, bottom=0.16, top=0.86)
    for i, b in enumerate(bl):
        strong = b["F"] >= 10
        lo, hi = max(b["ci"][0], -0.5), min(b["ci"][1], 0.8)
        ax.plot([i, i], [lo, hi], color=COL[0], lw=2, alpha=1 if strong else 0.45)
        ax.plot(i, max(b["mef"], -0.5), "o", ms=8, mfc=COL[0] if strong else SURF, mec=COL[0], mew=1.6)
        ax.plot(i + 0.18, ab[str(i)], "s", ms=7, color=COL[2])
        if not strong:
            ax.annotate(f"F = {b['F']:.1f} (weak);\ninterval to {b['ci'][0]:.1f}", (i, max(b["mef"], -0.5)), xytext=(10, -4), textcoords="offset points",
                        ha="left", fontsize=7.5, color=INK2)
    ax.set_xticks(range(4)); ax.set_xticklabels([f"{b['block'][:2]}:00–{b['block'][3:]}:00" for b in bl])
    ax.axhline(0, color=GRID, lw=1); ax.set_ylim(-0.6, 0.85); ax.grid(axis="y", color=GRID, lw=0.6)
    ax.set_ylabel("t CO₂ per MWh"); ax.set_xlabel("start of the window (local time)")
    ax.plot([], [], "o", color=COL[0], label="MEF at 1 day (95% interval)"); ax.plot([], [], "s", color=COL[2], label="mean AEF")
    ax.legend(frameon=False, loc="upper left", fontsize=8)
    fig.suptitle("1-day MEF of windows starting in each block, against the block's average factor", x=0.1, ha="left", fontsize=10.5, color=INK)
    fig.savefig(F / "F3_blocks.png", dpi=170); plt.close(fig)
    caption("F3_blocks", """MEF at the 1-day horizon by 6-hour block of the window's start (fully interacted 2SLS), with
    95% month-block bootstrap intervals, against each block's mean AEF. The 00:00-06:00 block has a first-stage F of 4.2
    and is weakly identified (hollow; interval clipped).""")
    print("figures written")


if __name__ == "__main__":
    main()
