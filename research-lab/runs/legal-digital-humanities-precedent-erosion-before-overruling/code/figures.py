"""Figures for the report (each PNG has a .txt caption). Written after event.py and secondary.py.

  F1  relative decline D(e) = 1 - rate ratio, treated vs matched controls, by event year: preregistered sample,
      excluding co-citing opinions, and (post hoc, D1) windows before the 2019 coverage break
  F2  lower-court citations to Supreme Court clusters per year in CourtListener, federal and state (the coverage break)
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
INK, INK2, GRID, SURF, BLUE, ORANGE, GREY = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb", "#2a78d6", "#e8a317", "#9a9893"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def f1():
    ep = pd.read_csv(T / "event_path.csv")
    p = json.load(open(T / "primary.json"))["primary"]
    q = json.load(open(T / "posthoc_pre2019.json"))
    specs = [("primary", "preregistered\n(71 overrulings)", INK),
             ("excl_cocite", "excluding opinions that also\ncite the overruling decision", BLUE),
             ("pre2019", "post hoc: windows before\nthe 2019 break (57)", ORANGE)]
    fig, axes = plt.subplots(1, 3, figsize=(7.8, 3.6), sharey=True)
    fig.subplots_adjust(left=0.12, right=0.98, bottom=0.15, top=0.76, wspace=0.08)
    for ax, (v, lab, col) in zip(axes, specs):
        g = ep[ep.variant == v].sort_values("event")
        ax.fill_between(g.event, g.lo, g.hi, color=col, alpha=0.15, lw=0)
        ax.plot(g.event, g.D, color=col, marker="o", ms=3, lw=1.5)
        ax.axhline(0, color=INK2, lw=0.8); ax.axvline(-0.5, color=GREY, lw=0.8, ls=":")
        ax.set_title(lab, fontsize=7.8, color=INK, loc="left", wrap=True)
        ax.set_xticks([-10, -5, 0, 5, 10]); ax.set_ylim(-1.3, 1.0); ax.grid(axis="y", color=GRID, lw=0.5)
        ax.set_xlabel("years from overruling")
    axes[0].set_ylabel("relative decline in citations\n(1 − rate ratio vs controls)")
    fig.suptitle("Overruled precedents were not fading beforehand: before the 2019 coverage break they were cited more",
                 x=0.02, ha="left", fontsize=10, color=INK)
    fig.savefig(F / "F1_event_paths.png", dpi=170); plt.close(fig)
    caption("F1_event_paths", f"""Stacked PPML, each overruled precedent against 10 matched never-overruled Supreme Court
    decisions (decided within 2 years, same SCDB issue area where known, nearest on log citations in event years -20 to -11);
    case x stack and calendar-year x stack fixed effects; reference = event years -20 to -11. Positive values: fewer
    citations than controls. Shaded: pointwise 95% stack-bootstrap intervals (B = 1,000). Preregistered pre-share
    D(-1)/D(+5) = {p['pre_share']:.2f}, not testable because D(+5) = {p['D']['5']:.2f} has an interval including 0
    ({p['D5_ci'][0]:.2f} to {p['D5_ci'][1]:.2f}). Right panel (post hoc, D1): D(-1) = {q['D']['-1']:.2f}
    ({q['Dm1_ci'][0]:.2f} to {q['Dm1_ci'][1]:.2f}).""")


def f2():
    t = pd.read_csv(T / "scotus_cites_by_year.csv", index_col=0)
    t = t.loc[1980:2025]
    fig, ax = plt.subplots(figsize=(7.4, 3.2))
    fig.subplots_adjust(left=0.1, right=0.97, bottom=0.14, top=0.86)
    ax.plot(t.index, t.federal / 1000, color=BLUE, lw=2, label="federal courts")
    ax.plot(t.index, t.state / 1000, color=ORANGE, lw=2, label="state courts")
    ax.axvline(2018.5, color=GREY, lw=0.8, ls=":")
    ax.set_ylabel("citations to Supreme Court decisions (thousands)"); ax.grid(axis="y", color=GRID, lw=0.5)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    fig.suptitle("CourtListener's federal coverage triples after 2018", x=0.02, ha="left", fontsize=10.5, color=INK)
    fig.savefig(F / "F2_coverage.png", dpi=170); plt.close(fig)
    caption("F2_coverage", f"""Lower-court citing opinions (clusters) citing any Supreme Court cluster, by year filed, in the
    CourtListener citation map of 2026-09-30. Federal: {int(t.federal[2018]):,} in 2018, {int(t.federal[2020]):,} in 2020;
    state: {int(t.state[2018]):,} and {int(t.state[2020]):,}. The jump is a coverage change (scraped federal opinions),
    not a change in citing behaviour (D1).""")


if __name__ == "__main__":
    f1(); f2()
    print("figures written")
