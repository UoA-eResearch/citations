"""G2 coverage file and figures (PNG + .txt caption). Written after analyse.py.

  coverage.json  FENZ rows -> suburbs geocoded -> with a gauge within 10 km -> suburb-days with a usable gauge
  F1  Auckland's fitted callout probability against rarity, with 27 January 2023 placed on it
  F2  leave-one-region-out held-out log-loss, depth model against rarity model
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T, F = RUN / "results" / "tables", RUN / "results" / "figures"
F.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(RUN.parents[1] / "tools"))
from coverage import Coverage  # noqa: E402

INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"
BLUE, ORANGE = "#2a78d6", "#d6532a"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def coverage():
    rows = json.loads((T / "fenz_rows.json").read_text())
    geo = json.loads((T / "geocode.json").read_text())
    pan = json.loads((T / "panel_coverage.json").read_text())
    path = T / "coverage.json"
    if path.exists():
        path.unlink()
    raw = sum(v["rows"] for k, v in rows.items() if k.endswith(".csv"))
    c = Coverage("fenz_rows", path)
    c.add_counts(ok=rows["kept_rows"], drops={"time unparsed or in the DST gap, or no suburb": raw - rows["kept_rows"]})
    c.save()
    bm = geo["by_match"]
    c = Coverage("suburbs_geocoded", path)
    c.add_counts(ok=bm["unique"]["suburbs"] + bm["tla_centroid"]["suburbs"],
                 drops={k: v["suburbs"] for k, v in bm.items() if k not in ("unique", "tla_centroid")})
    c.save()
    c = Coverage("suburbs_in_panel", path)
    c.add_counts(ok=pan["panel_suburbs"], drops={"no gauge within 10 km": pan["geocoded_suburbs"] - pan["with_gauge_within_10km"],
                                               "a gauge within 10 km but never usable": pan["with_gauge_within_10km"] - pan["panel_suburbs"]})
    c.save()
    c = Coverage("suburb_days", path)
    c.add_counts(ok=pan["panel_suburb_days"], drops={"no usable gauge within 10 km that day": pan["suburb_days_no_usable_gauge"]})
    c.save()


def f1():
    c = pd.read_csv(T / "auckland_curve.csv"); r = c[c.model == "R"]
    a = json.loads((T / "auckland_2023_01_27.json").read_text())
    fig, ax = plt.subplots(figsize=(6.4, 3.3))
    fig.subplots_adjust(left=0.13, right=0.97, bottom=0.17, top=0.86)
    ax.plot(r.x, r.p * 100, color=BLUE, lw=2)
    ax.axvline(a["median_r6"], color=ORANGE, lw=1.2, ls="--")
    ax.text(a["median_r6"] + 0.05, ax.get_ylim()[1] * 0.85 if ax.get_ylim()[1] else 1,
            f"27 Jan 2023: median rarity {a['median_r6']:.1f}\n{a['with_callout']} of {a['suburbs']} suburbs called out", color=INK2, fontsize=8)
    ax.set_xlabel("rarity: day's maximum 6-h rain / local HIRDS median annual maximum")
    ax.set_ylabel("fitted callout probability (%)")
    ax.grid(color=GRID, lw=0.5)
    fig.suptitle("Auckland: fitted flood-callout probability against rain rarity",
                 x=0.02, ha="left", fontsize=9, color=INK)
    fig.savefig(F / "F1_auckland_curve.png", dpi=170); plt.close(fig)
    caption("F1_auckland_curve", """Fitted probability of at least one FENZ flood callout in an Auckland suburb-day, from the
    rarity model trained on FY2017/18-2023/24, averaged over Auckland's training suburb-days with only the rain term
    changed. Dashed: the median rarity of Auckland panel suburbs on 27 January 2023.""")


def f2():
    lo = json.loads((T / "primary.json").read_text())["loro"]["regions"]
    d = pd.DataFrame(lo).T
    d["gain_pct"] = 100 * (d.LL_D.astype(float) - d.LL_R.astype(float)) / d.LL_D.astype(float)
    d = d.sort_values("gain_pct")
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    fig.subplots_adjust(left=0.27, right=0.97, bottom=0.16, top=0.86)
    cols = [BLUE if g > 0 else ORANGE for g in d.gain_pct]
    ax.barh([f"{i.replace(' Region', '')} ({int(r.test_floods)})" for i, r in d.iterrows()], d.gain_pct, color=cols, height=0.6)
    ax.axvline(0, color=INK2, lw=0.8)
    ax.set_xlabel("held-out log-loss reduction of rarity over depth (%)")
    ax.grid(axis="x", color=GRID, lw=0.5)
    fig.suptitle("Leave-one-region-out: rarity predicts better in 7 of 9 regions", x=0.02, ha="left", fontsize=9.5, color=INK)
    fig.savefig(F / "F2_loro.png", dpi=170); plt.close(fig)
    caption("F2_loro", """Each region is left out of training (FY2017/18-2023/24 in the other regions) and scored on its own
    FY2024/25 suburb-days. Bars: percentage reduction in mean log-loss of the rarity model against the depth model.
    In brackets: the region's held-out flood suburb-days; regions with few are noisy.""")


if __name__ == "__main__":
    coverage(); f1(); f2(); print("coverage and figures written")
