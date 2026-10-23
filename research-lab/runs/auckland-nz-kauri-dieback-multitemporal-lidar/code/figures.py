"""Figures for the report (each PNG has a .txt caption). Written after model.py.

  F1  AUC (95% block bootstrap) of the change, static and static + change models: primary and secondary analyses
  F2  mean change in P95 canopy height within 15 m, 2016-18 -> 2024, by survey and field status, with stable points
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T, F = RUN / "results" / "tables", RUN / "results" / "figures"
F.mkdir(parents=True, exist_ok=True)
INK, INK2, GRID, SURF, BLUE, ORANGE, GREY = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb", "#2a78d6", "#e8a317", "#9a9893"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def f1(p):
    rows = [("2014-15 labels (primary)", p["primary"]), ("2014-15, severe only", p["secondary"]["severe_only_2014"]),
            ("2014-15, 10 m circle", p["secondary"]["radius_10"]), ("2014-15, 20 m circle", p["secondary"]["radius_20"]),
            ("2014-15, no slip mask", p["secondary"]["no_slip_mask"]), ("2021 labels (time-aligned)", p["secondary"]["s2021"])]
    fig, ax = plt.subplots(figsize=(7.4, 3.8))
    fig.subplots_adjust(left=0.3, right=0.97, bottom=0.14, top=0.86)
    ax.axvspan(0.70, 1.0, color=BLUE, alpha=0.06, lw=0)
    ax.axvline(0.5, color=INK2, lw=0.8, ls="--"); ax.axvline(0.70, color=BLUE, lw=0.8, ls=":")
    for i, (lab, r) in enumerate(rows):
        for k, (key, col, off) in enumerate((("auc_change", BLUE, -0.22), ("auc_static", GREY, 0.0),
                                             ("auc_static_plus_change", ORANGE, 0.22))):
            lo, hi = r[f"{key}_ci"]
            ax.plot([lo, hi], [i + off] * 2, color=col, lw=1.6)
            ax.plot(r[key], i + off, "o", color=col, ms=5, label=["LiDAR change", "static", "static + change"][k] if i == 0 else None)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([f"{l} ({r['positives']}/{r['n']})" for l, r in rows], fontsize=8)
    ax.invert_yaxis(); ax.set_xlim(0.3, 0.85); ax.set_xlabel("AUC within test folds, spatially blocked CV (95% block bootstrap)")
    ax.grid(axis="x", color=GRID, lw=0.5); ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.text(0.705, -0.6, "H1 bar", fontsize=7.5, color=BLUE)
    fig.suptitle("Crown change from repeat LiDAR does not pick out kauri graded symptomatic", x=0.02, ha="left",
                 fontsize=10.5, color=INK)
    fig.savefig(F / "F1_auc.png", dpi=170); plt.close(fig)
    pr = p["primary"]
    caption("F1_auc", f"""AUC computed within each test fold and averaged (D1; logistic regression, 500 m blocks, 5-fold, 5 repeats) for trees graded
    possible or severe kauri dieback (status 3-4) against non-symptomatic (status 1). Change features: P95, P50 and
    cover above 15 m of the canopy height model within 15 m of each tree, 2024 minus 2016-18. Static: elevation, slope,
    2016-18 P95 and distance to the nearest track. Labels in brackets: symptomatic / all trees. Primary: change AUC
    {pr['auc_change']:.2f} ({pr['auc_change_ci'][0]:.2f}-{pr['auc_change_ci'][1]:.2f}); the dotted line is the H1
    threshold of 0.70. A within-block label shuffle gives
    {pr['within_block_shuffle_null_change']['mean']:.2f} on average (95th percentile
    {pr['within_block_shuffle_null_change']['p95']:.2f}), the relevant "chance" level.""")


def f2(p):
    g = p["group_means"]
    order = [("s2014_status1", "2014-15 non-symptomatic"), ("s2014_status3", "2014-15 possible"),
             ("s2014_status4", "2014-15 severe"), ("s2021_status1", "2021 non-symptomatic"),
             ("s2021_status3", "2021 possible"), ("s2021_status4", "2021 severe"), ("stable_status0", "random forest points")]
    fig, ax = plt.subplots(figsize=(7.4, 3.4))
    fig.subplots_adjust(left=0.3, right=0.97, bottom=0.16, top=0.86)
    for i, (k, lab) in enumerate(order):
        v = g[k]["dp95_m_r15"]
        col = GREY if k.startswith("stable") else (BLUE if k.endswith("status1") else ORANGE)
        ax.plot(v["ci"], [i, i], color=col, lw=1.8); ax.plot(v["mean"], i, "o", color=col, ms=6)
    ax.set_yticks(range(len(order))); ax.set_yticklabels([f"{lab} ({g[k]['n']:,})" for k, lab in order], fontsize=8)
    ax.invert_yaxis(); ax.axvline(0, color=INK2, lw=0.8, ls="--")
    ax.set_xlabel("mean change in P95 canopy height within 15 m, 2016-18 to 2024 (m)"); ax.grid(axis="x", color=GRID, lw=0.5)
    fig.suptitle("Canopy rose almost everywhere; trees graded symptomatic do not stand out", x=0.02, ha="left", fontsize=10.5, color=INK)
    fig.savefig(F / "F2_change_by_status.png", dpi=170); plt.close(fig)
    caption("F2_change_by_status", f"""Mean change (95% block bootstrap) in the 95th percentile of canopy height within
    15 m of each surveyed tree, after masking cells whose ground height changed by more than 1 m. Random forest points:
    {g['stable_status0']['n']:,} points with 2016-18 canopy above 15 m, at least 50 m from any survey record; their
    mean rise of {g['stable_status0']['dp95_m_r15']['mean']:.2f} m includes any systematic difference between the two
    LiDAR surveys. The 2014-15 trees stand by tracks (median 5 m away); the 2021 trees stand deeper in the forest.""")


if __name__ == "__main__":
    p = json.load(open(T / "primary.json"))
    f1(p); f2(p)
    print("figures written")
