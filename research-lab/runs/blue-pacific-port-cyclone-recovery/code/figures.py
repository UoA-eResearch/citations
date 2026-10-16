"""Figures for the report. Each PNG gets a .txt caption beside it.

  F1  what the method can see: detection probability against closure length, one line per traffic level
  F2  every computed primary-arm event: recovery days against the port's traffic, small-island ports marked
  F3  the import-share and small-island odds ratios for "detectably disrupted", preregistered and post hoc

Palette: the dataviz skill's reference slots, colour following the entity (blue = other ports, orange = small
island states, also a different marker so identity never rests on colour alone); F1's traffic levels are one
sequential hue, light to dark. Text stays in neutral ink.
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
BLUE, ORANGE = "#2a78d6", "#eb6834"
SEQ = ["#bcd5f3", "#8fb8ea", "#5f99df", "#2a78d6", "#1d5ba6", "#123d72"]
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def style(ax, axis="y"):
    ax.grid(axis=axis, color=GRID, lw=0.6)
    ax.set_axisbelow(True)


def f1():
    g = pd.DataFrame(json.load(open(T / "detectability.json"))["grid"])
    g = g[g.alpha == 0.25]
    fig, ax = plt.subplots(figsize=(7.6, 4.0))
    style(ax)
    ax.axhline(0.8, color=INK2, lw=0.8, ls=":")
    ax.text(28.6, 0.81, "80%", color=INK2, fontsize=8, va="bottom")
    for c, (mu, s) in zip(SEQ, g.groupby("mu")):
        s = s.sort_values("closure_days")
        ax.plot(s.closure_days, s.p_detect, color=c, lw=2, marker="o", ms=4, label=f"{mu:g} calls/day")
    ax.legend(title="port's mean traffic", title_fontsize=8, fontsize=8, frameon=False, loc="lower right")
    ax.set_xlim(-0.5, 30)
    ax.set_ylim(-0.02, 1.04)
    ax.set_xticks([0, 2, 4, 7, 10, 14, 21, 28])
    ax.set_xlabel("length of a complete closure (days of zero calls)")
    ax.set_ylabel("share of simulated closures detected")
    ax.set_title("A week-long closure is mostly missed below one call a day", loc="left", fontsize=10, color=INK)
    fig.tight_layout()
    fig.savefig(F / "F1_detectability.png", dpi=200)
    caption("F1_detectability", """F1. What the method can detect. Simulated ports with a known complete closure, run through exactly
    the preregistered algorithm (120 replicates per point, dispersion 0.25; the full grid, including dispersion 1,
    is in results/tables/detectability.json). The value at 0 days is the false-alarm rate. Of the 62 Pacific island
    ports, 50 average under 0.5 calls a day and 7 more between 0.5 and 1.""")


def f2():
    r = pd.read_csv(T / "recovery_events.csv")
    p = r[(r.cat_at_closest >= 3) & (r.closest_km <= 150)]
    ok = p[p.status == "ok"].copy()
    rng = np.random.default_rng(3)
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    style(ax)
    ax.axvspan(0.4, 1.0, color=GRID, alpha=0.6, lw=0)
    ax.text(0.71, 104, "a 7-day closure\nis mostly missed", ha="center", fontsize=8, color=INK2, va="top")
    for is_sids, col, mk, lab in ((False, BLUE, "o", "other ports"), (True, ORANGE, "D", "small island developing states")):
        d = ok[ok.sids == is_sids]
        y = np.where(d.disrupted, d["T"], 0.0) + np.where(d.disrupted, 0, rng.uniform(-2.2, 2.2, len(d)))
        n_dis = int(d.disrupted.sum())
        ax.scatter(d.mean_calls, y, s=34 if is_sids else 26, marker=mk, facecolor=np.where(d.disrupted, col, "none"),
                   edgecolor=col, lw=1.2, label=f"{lab}: {n_dis} of {len(d)} disrupted", zorder=3)
    cens = ok[ok.disrupted.astype(bool) & (ok.event == 0)]
    for _, e in cens.iterrows():
        ax.annotate("censored\nat 120", (e.mean_calls, 120), xytext=(8, -4), textcoords="offset points", fontsize=7,
                    color=INK2, va="top")
    ax.set_xscale("log")
    ax.set_xlim(0.4, 400)
    ax.set_ylim(-5, 125)
    ax.set_xticks([0.5, 1, 2, 5, 10, 20, 50, 100, 200])
    ax.set_xticklabels(["0.5", "1", "2", "5", "10", "20", "50", "100", "200"])
    ax.set_xlabel("port's mean daily calls, 2019-2026 (log scale)")
    ax.set_ylabel("recovery time, days")
    n_quiet = int(((p.status == "low_activity") & p.sids).sum())
    ax.set_title("Small-island ports almost never showed a detectable disruption", loc="left", fontsize=10, color=INK)
    from matplotlib.lines import Line2D
    hs = [Line2D([], [], ls="", marker=mk, color=col, ms=6, label=f"{lab}: {int(ok[ok.sids == s_].disrupted.sum())} of "
                 f"{int((ok.sids == s_).sum())} disrupted")
          for s_, col, mk, lab in ((False, BLUE, "o", "other ports"), (True, ORANGE, "D", "small island developing states"))]
    hs += [Line2D([], [], ls="", marker="o", mfc="none", mec=INK2, ms=6, label="hollow: no disruption detected")]
    ax.legend(handles=hs, frameon=False, loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(F / "F2_events.png", dpi=200)
    caption("F2_events", f"""F2. Every primary-arm event (Category 3+ within 150 km) whose port averages at least 0.5 calls a day
    and has the history and follow-up the method needs: {len(ok)} events, {ok.sid.nunique()} storms. Filled markers are
    detected disruptions, plotted at their recovery time; hollow markers are events with no detectable disruption,
    jittered around zero. Another {n_quiet} small-island events, at ports below 0.5 calls a day, could not be analysed.
    The shaded band is where simulation shows a complete week-long closure is detected less than 80% of the time.""")


def f3():
    s = json.load(open(T / "supplementary.json"))
    rows = []
    sh = s["S2_power_as_control"]["share"]
    si = s["S2_power_as_control"]["sids"]
    s3 = s["S3_high_power_only"]["share"]
    k = 0.1   # odds ratio per 10 percentage points of import share
    rows.append(("import share, +10 pp", "preregistered (traffic as a straight line)", sh["preregistered_control"], k))
    rows.append(("import share, +10 pp", "post hoc: simulated detection power as the control", sh["power_control"], k))
    rows.append(("import share, +10 pp", f"post hoc: only events with power >= 80% (n = {s['S3_high_power_only']['n']})", s3, k))
    rows.append(("small-island port", "preregistered (traffic as a straight line)", si["preregistered_control"], 1))
    rows.append(("small-island port", "post hoc: simulated detection power as the control", si["power_control"], 1))
    fig, ax = plt.subplots(figsize=(8.6, 3.4))
    fig.subplots_adjust(left=0.40, right=0.80, bottom=0.17, top=0.97)
    style(ax, axis="x")
    ys = [5.6, 4.8, 4.0, 2.0, 1.2]
    yt = ax.get_yaxis_transform()
    for y, (term, spec, c, scale) in zip(ys, rows):
        col = BLUE if term.startswith("import") else ORANGE
        mk = "o" if term.startswith("import") else "D"
        lo, pt, hi = np.exp(scale * c["lo"]), np.exp(scale * c["coef"]), np.exp(scale * c["hi"])
        ax.plot([lo, hi], [y, y], color=col, lw=2, solid_capstyle="round")
        ax.scatter([pt], [y], color=col, marker=mk, s=40, zorder=3)
        ax.text(-0.03, y, spec, fontsize=8, color=INK2, va="center", ha="right", transform=yt)
        ax.text(1.03, y, f"{pt:.2f} ({lo:.2f} to {hi:.2f})", fontsize=8, color=INK2, va="center", transform=yt)
    ax.text(-0.03, 6.4, "import share, per 10 percentage points", fontsize=9, color=INK, va="center", ha="right", transform=yt)
    ax.text(-0.03, 2.8, "small island developing state", fontsize=9, color=INK, va="center", ha="right", transform=yt)
    ax.axvline(1, color=INK2, lw=0.8)
    ax.set_xscale("log")
    ax.set_xlim(0.003, 4)
    ax.set_xticks([0.01, 0.1, 0.5, 1, 2])
    ax.set_xticklabels(["0.01", "0.1", "0.5", "1", "2"])
    ax.set_ylim(0.6, 6.9)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("odds ratio of a detectable disruption (log scale)\n< 1: less often disrupted")
    fig.savefig(F / "F3_odds_ratios.png", dpi=200)
    caption("F3_odds_ratios", """F3. Part A of the two-part model: the odds of a detectable disruption, with 95% intervals
    clustered by storm. The preregistered model controls for detectability with log mean daily calls; the post-hoc
    rows (deviations D7) replace that with each event's simulated power to detect a 7-day closure, or keep only
    events where that power is at least 80%. The direction holds throughout, but once detectability is controlled
    properly neither interval excludes 1.""")


if __name__ == "__main__":
    f1(); f2(); f3()
    print("figures written")
