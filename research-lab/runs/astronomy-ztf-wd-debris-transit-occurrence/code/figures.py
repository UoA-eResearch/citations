"""Figures (PNG + .txt caption). Written after detect.py occurrence.

  F1  faint-outlier excess for every eligible star, known debris-transit systems marked (secondary analysis 3)
  F2  injection recovery by signal class and G magnitude
  F3  candidates and recovered known systems on the Gaia colour-magnitude diagram (secondary analysis 4)
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T, F, D = RUN / "results" / "tables", RUN / "results" / "figures", RUN / "data"
F.mkdir(parents=True, exist_ok=True)
INK, INK2, GRID, SURF, BLUE, ORANGE, GREY = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb", "#2a78d6", "#d6532a", "#9a9893"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.facecolor": SURF, "figure.facecolor": SURF, "axes.spines.top": False, "axes.spines.right": False})
d = pd.read_parquet(T / "detect.parquet")
s = pd.read_parquet(D / "sample.parquet")[["source_id", "phot_g_mean_mag", "parallax", "bp_rp"]]
e = d[d.n_epochs >= 100].merge(s, on="source_id")
k = pd.read_csv(T / "known_systems.csv")
k = k[k.in_sample]
kid = set(k.gaia_dr3_source_id_in_sample.astype(int))
p = json.load(open(T / "primary.json"))


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


# F1
fig, ax = plt.subplots(figsize=(6.8, 3.6))
fig.subplots_adjust(left=0.1, right=0.97, bottom=0.15, top=0.85)
x = e.excess.clip(-20, 80)
ax.hist(x, bins=np.arange(-20, 81, 1), color=GREY, log=True)
kn = e[e.source_id.isin(kid)]
for v, fl in zip(kn.excess.clip(-20, 80), kn.short.fillna(False) | kn.long.fillna(False)):
    ax.axvline(v, color=BLUE if fl else ORANGE, lw=1.2, alpha=0.9)
ax.axvline(5, color=INK2, lw=0.8, ls=":")
ax.set_xlabel("faint-outlier excess (epochs > 3σ fainter minus > 3σ brighter; clipped at −20 and 80)")
ax.set_ylabel("stars (log)")
ax.plot([], [], color=BLUE, label="known system, recovered"); ax.plot([], [], color=ORANGE, label="known system, missed")
ax.plot([], [], color=INK2, ls=":", label="short-rule excess bar (5)")
ax.legend(frameon=False, fontsize=8, loc="upper right")
fig.suptitle(f"Faint outliers in {len(e):,} white-dwarf light curves; {p['known_recovered']} of {p['known_eligible']} known debris-transit systems flagged",
             x=0.02, ha="left", fontsize=9.5, color=INK)
fig.savefig(F / "F1_excess.png", dpi=170); plt.close(fig)
caption("F1_excess", f"""Per-star faint-outlier excess pooled over ZTF g and r (good epochs only), for {len(e):,} sample white dwarfs
with at least 100 good epochs. Vertical lines mark the {len(kn)} known debris-transit white dwarfs in the sample (blue: flagged by
either preregistered rule; orange: missed). The short-dip rule also needs a binomial p < 1e-6 and faint epochs on at least 3 nights;
the long-dip rule uses 30-day bins and is not shown here.""")

# F2
inj = pd.read_parquet(T / "inject.parquet").merge(e[["source_id", "phot_g_mean_mag"]], on="source_id")
inj["gb"] = pd.cut(inj.phot_g_mean_mag, [0, 17, 18, 19, 19.5, 21], labels=["<17", "17–18", "18–19", "19–19.5", "19.5–20"])
fig, ax = plt.subplots(figsize=(6.2, 3.4))
fig.subplots_adjust(left=0.11, right=0.97, bottom=0.16, top=0.85)
for cls, col, lab in (("wd1145", BLUE, "WD 1145-like (hours)"), ("j0139", ORANGE, "J0139-like (days)"), ("oneoff", INK2, "one-off (30–400 d)")):
    r = inj[inj.cls == cls].groupby("gb", observed=True).rec.mean()
    ax.plot(range(len(r)), r.values, marker="o", ms=4, lw=2, color=col, label=lab)
ax.set_xticks(range(5)); ax.set_xticklabels(["<17", "17–18", "18–19", "19–19.5", "19.5–20"])
ax.set_ylim(0, 1); ax.set_xlabel("Gaia G"); ax.set_ylabel("share of injections recovered"); ax.grid(axis="y", color=GRID, lw=0.5)
ax.legend(frameon=False, fontsize=8, loc="lower left")
fig.suptitle("Injection recovery falls for faint white dwarfs, most for long dips", x=0.02, ha="left", fontsize=9.5, color=INK)
fig.savefig(F / "F2_completeness.png", dpi=170); plt.close(fig)
caption("F2_completeness", """Share of injected signals recovered by either preregistered rule, by class and Gaia G, from 5,000 random
eligible, unflagged white dwarfs x 3 classes x 10 injections. Signal parameters are drawn as in plan section 0.""")

# F3
c = pd.read_csv(T / "candidates.csv")
fig, ax = plt.subplots(figsize=(5.2, 4.4))
fig.subplots_adjust(left=0.13, right=0.97, bottom=0.12, top=0.88)
MG = lambda g, plx: g + 5 * np.log10(plx / 100)  # noqa: E731
ax.scatter(e.bp_rp, MG(e.phot_g_mean_mag, e.parallax), s=1, color=GRID, rasterized=True, label="sample")
ax.scatter(c.bp_rp, MG(c.phot_g_mean_mag, c.parallax), s=6, color=ORANGE, label=f"candidates ({len(c)})")
kk = e[e.source_id.isin(kid)]
ax.scatter(kk.bp_rp, MG(kk.phot_g_mean_mag, kk.parallax), s=26, color=BLUE, edgecolor=SURF, lw=0.8, label="known systems")
ax.invert_yaxis(); ax.set_xlim(-0.7, 1.6); ax.set_xlabel("BP − RP"); ax.set_ylabel("absolute G")
ax.legend(frameon=False, fontsize=8, loc="lower left", markerscale=1.5)
fig.suptitle("Candidates spread across the white-dwarf sequence", x=0.02, ha="left", fontsize=9.5, color=INK)
fig.savefig(F / "F3_cmd.png", dpi=170); plt.close(fig)
caption("F3_cmd", f"""Gaia colour-magnitude diagram of the {len(e):,} eligible white dwarfs, the {len(c)} unexplained candidates
(flagged, not known, not a Gaia DR3 CV/ECL/RS/SOLAR_LIKE) and the known debris-transit systems in the sample.""")
print("figures written")
