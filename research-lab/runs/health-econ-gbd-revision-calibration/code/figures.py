"""Figures and key-result tiles for the report, from results/tables (and z from the panel). Rounds once, here.
Writes results/figures/*.png with *.txt captions, and results/tables/tiles.json."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.stats import norm  # noqa: E402

import analysis as A  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
FIG = RUN / "results" / "figures"
GROUP_ORDER = ["high", "medium", "low"]
GROUP_LABEL = {"high": "High-quality VR\n(59 countries)", "medium": "Medium\n(28)", "low": "Low, very low or none\n(117)"}
C1C, C2C = "#2a78d6", "#d95926"


def pct(x, d=1):
    return f"{100 * x:.{d}f}%"


def save(fig, name, caption):
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / f"{name}.png", dpi=170, bbox_inches="tight")
    (FIG / f"{name}.txt").write_text(caption)
    plt.close(fig)


def coverage_by_group(pr, sec):
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    xs = np.arange(len(GROUP_ORDER) + 1)
    labels = ["All 204\ncountries"] + [GROUP_LABEL[g] for g in GROUP_ORDER]
    for off, key, col, name in ((-0.12, "H2", C1C, "C1: GBD 2023 estimate inside the GBD 2021 95% interval"),
                                (0.12, "H4", C2C, "C2: revision within both releases' stated uncertainty")):
        overall = pr["H1" if key == "H2" else "H3"]
        vals = [overall] + [pr[key]["by_group"][g] for g in GROUP_ORDER]
        est = np.array([v["estimate"] for v in vals])
        lo = est - np.array([v["lower95"] for v in vals])
        hi = np.array([v["upper95"] for v in vals]) - est
        ax.errorbar(xs + off, est, yerr=[lo, hi], fmt="o", color=col, capsize=4, ms=7, label=name)
    e1 = sec[(sec.analysis.str.startswith("E1")) & (sec.group == "all")].estimate.iloc[0]
    ax.axhline(0.95, color="#85847e", ls="--", lw=1)
    ax.text(len(xs) - 0.5, 0.955, "95%: the C2 floor if intervals are calibrated", ha="right", va="bottom", fontsize=8, color="#4f4e4a")
    ax.axhline(e1, color=C1C, ls=":", lw=1)
    ax.text(len(xs) - 0.5, e1 - 0.006, f"{pct(e1)}: C1 expected if calibrated and independent", ha="right", va="top", fontsize=8, color=C1C)
    ax.set_xticks(xs, labels, fontsize=8.5)
    ax.set_ylim(0.55, 1.0)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    ax.set_ylabel("Share of country-cause-year cells")
    ax.legend(loc="lower left", fontsize=8, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "coverage_by_group", "Coverage of GBD 2023 estimates by GBD 2021 95% uncertainty intervals, 137 level-3 causes × 2019 "
         "and 2021, by WHO vital-registration quality group. Bars are 95% two-way (country × cause) bootstrap intervals. Both "
         "measures sit far below what calibrated intervals would give, and hardly differ by data quality.")


def calibration_levels(p):
    e = p[p.elig2]
    nominal = np.array([0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99])
    obs = np.array([(np.abs(e.z) <= norm.ppf(0.5 + n / 2)).mean() for n in nominal])
    fig, ax = plt.subplots(figsize=(4.8, 4.4))
    ax.plot([0.45, 1], [0.45, 1], color="#85847e", lw=1, ls="--")
    ax.plot(nominal, obs, "o-", color=C2C)
    for n, o in zip(nominal, obs):
        if n in (0.5, 0.8, 0.95, 0.99):
            ax.annotate(f"{pct(o, 0)}", (n, o), textcoords="offset points", xytext=(6, -12) if n > 0.5 else (-4, 8), fontsize=8, color=C2C,
                        ha="left" if n > 0.5 else "right")
    ax.set_xlabel("Nominal level of the combined interval")
    ax.set_ylabel("Share of revisions inside it")
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.set_xlim(0.45, 1.0)
    ax.set_ylim(0.45, 1.0)
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "calibration_levels", "Exploratory (X4). Share of the 52,219 eligible cells whose revision |z| falls within the "
         "combined interval at each nominal level. Calibrated, independent releases would lie on or above the dashed line. The gap "
         "is small at 50% and grows towards 99%: most revisions are of the size the intervals imply, but large revisions are far "
         "more common than the intervals allow.")


def by_cause(p):
    k = pd.read_csv(TAB / "by_cause.csv").sort_values("C2").reset_index(drop=True)
    cols = {"Non-communicable diseases": "#2a78d6", "Communicable, maternal, neonatal, and nutritional diseases": "#d95926", "Injuries": "#3a9a5b"}
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    for l1, c in cols.items():
        m = k.l1_name == l1
        ax.scatter(k.index[m], k.C2[m], s=14, color=c, label=l1.replace(", and nutritional", " and nutritional"))
    ax.axhline(0.95, color="#85847e", ls="--", lw=1)
    for name in ("Other neoplasms", "COVID-19", "Other intestinal infectious diseases"):
        r = k[k.cause_name == name]
        if len(r):
            ax.annotate(name, (r.index[0], r.C2.iloc[0]), textcoords="offset points", xytext=(8, -2), fontsize=7.5)
    ax.set_xlabel("137 level-3 causes, sorted by C2")
    ax.set_ylabel("C2 across countries and years")
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.set_xticks([])
    ax.legend(fontsize=7.5, frameon=False, loc="lower right")
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "c2_by_cause", "C2 for each of the 137 level-3 causes (both years, all countries). Only 7 causes reach the 95% "
         "line. The lowest, Other neoplasms, reflects an error in earlier rounds that GBD 2023 fixed (appendix p. 361).")


def by_country():
    c = pd.read_csv(TAB / "by_country.csv")
    order = ["high", "medium", "low", "very low", "none"]
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    rng = np.random.default_rng(1)
    for i, w in enumerate(order):
        v = c[c.who_quality == w].C2.values
        ax.scatter(i + rng.uniform(-0.18, 0.18, len(v)), v, s=12, color="#4f4e4a", alpha=0.7)
        ax.plot([i - 0.25, i + 0.25], [np.median(v)] * 2, color=C2C, lw=2)
    ax.axhline(0.95, color="#85847e", ls="--", lw=1)
    n = c.who_quality.value_counts()
    ax.set_xticks(range(len(order)), [f"{w}\n({n.get(w, 0)})" for w in order])
    ax.set_xlabel("WHO vital-registration quality class (countries)")
    ax.set_ylabel("C2 per country")
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "c2_by_country", "C2 for each of the 204 countries (137 causes × 2 years each), by WHO vital-registration class; "
         "orange bars are medians. The spread within every class dwarfs the differences between classes.")


def tiles(pr, sec):
    e1 = sec[(sec.analysis.str.startswith("E1")) & (sec.group == "all")].estimate.iloc[0]
    d = pr["H4"]["high_minus_low"]
    sign = lambda x: f"{'+' if x >= 0 else '−'}{abs(100 * x):.1f}"  # noqa: E731
    t = [
        ["Inside the GBD 2021 interval", pct(pr["H1"]["estimate"]), f"of GBD 2023 estimates; about {pct(e1, 0)} expected if calibrated"],
        ["Within combined uncertainty", pct(pr["H3"]["estimate"]), "of revisions (C2); at least 95% if calibrated"],
        ["High − low data quality", f"{sign(d['estimate'])} pts", f"C2 gap, 95% CI {sign(d['lower95'])} to {sign(d['upper95'])}"],
        ["Verdict", "Inconclusive", "too narrow everywhere (H3); no clear quality gradient (H4)"],
    ]
    json.dump(t, open(TAB / "tiles.json", "w"), ensure_ascii=False, indent=1)
    return t


def main():
    pr = json.load(open(TAB / "primary.json"))
    sec = pd.read_csv(TAB / "secondary.csv")
    p = A.metrics(pd.read_parquet(RUN / "data" / "panel.parquet"))
    coverage_by_group(pr, sec)
    calibration_levels(p)
    by_cause(p)
    by_country()
    print(tiles(pr, sec))


if __name__ == "__main__":
    main()
