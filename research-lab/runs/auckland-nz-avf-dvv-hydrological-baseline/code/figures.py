"""Figures for the report (each PNG has a .txt caption). Written after model.py and secondary.py.

  F1  held-out R^2 by scored pair (sorted), against the H1 threshold
  F2  the most coherent pair: observed 30-day dv/v against the model's training fit and held-out prediction, with rain
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dvv as D  # noqa: E402
import model as M  # noqa: E402

T, F = M.T, M.RUN / "results" / "figures"
F.mkdir(parents=True, exist_ok=True)
INK, INK2, GRID, SURF, BLUE, ORANGE, GREY = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb", "#2a78d6", "#e8a317", "#9a9893"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def f1(p):
    f = pd.read_csv(T / "fit.csv")
    sc = f[(f.train_coherence >= 0.5) & (f.heldout_days >= 180) & f.heldout_r2.notna()].sort_values("heldout_r2")
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    fig.subplots_adjust(left=0.2, right=0.97, bottom=0.11, top=0.88)
    y = np.arange(len(sc))
    v = sc.heldout_r2.clip(lower=-3)
    ax.barh(y, v, color=[BLUE if x >= 0 else GREY for x in sc.heldout_r2], height=0.7)
    for yi, x in zip(y, sc.heldout_r2):
        if x < -3:
            ax.text(-2.95, yi, f"{x:.1f}", va="center", fontsize=6.5, color=SURF)
    ax.axvline(0.5, color=ORANGE, lw=1.2, ls="--", label="H1 threshold (median 0.5)")
    ax.axvline(p["median_heldout_r2"], color=INK, lw=1.2, label=f"median {p['median_heldout_r2']:.2f}")
    ax.set_yticks(y); ax.set_yticklabels(sc.pair, fontsize=6.5); ax.set_xlim(-3.05, 1)
    ax.set_xlabel("held-out R² (2021 to each pair's first sensor change), clipped at -3")
    ax.grid(axis="x", color=GRID, lw=0.5); ax.legend(frameon=False, fontsize=8, loc="lower right")
    fig.suptitle("A rainfall-and-season model does not predict held-out velocity changes under Auckland", x=0.02, ha="left",
                 fontsize=10.5, color=INK)
    fig.savefig(F / "F1_heldout_r2.png", dpi=170); plt.close(fig)
    caption("F1_heldout_r2", f"""Held-out R² of the rainfall-diffusion + annual + drift model for the {p['pairs_scored']}
    station pairs with mean training coherence of at least 0.5 and at least 180 held-out days. Model trained on 2013-2020
    and applied unchanged from 2021. Median {p['median_heldout_r2']:.2f} (95% pair bootstrap {p['ci'][0]:.2f} to {p['ci'][1]:.2f});
    no pair reaches 0.5. Values below -3 are printed on the bar.""")


def f2():
    f = pd.read_csv(T / "fit.csv")
    sc = f[(f.train_coherence >= 0.5) & (f.heldout_days >= 180) & f.heldout_r2.notna()]
    pair = sc.sort_values("train_coherence", ascending=False).pair.iloc[0]
    dv = pd.read_parquet(T / "dvv_daily.parquet")
    era = pd.read_csv(M.RUN / "data" / "raw" / "era5_daily.csv", parse_dates=["date"]).set_index("date")
    days = pd.date_range(era.index.min(), M.REC_END, freq="D")
    feats = M.rain_features(days, era.precip_mm.reindex(days).fillna(0).to_numpy())
    g = dv[dv.pair == pair]
    sm, seg, ty, ph, ok, tr = M.fit_pair(g, feats, days)
    a, b = pair.split("-")
    ho_end = M.held_out_end(M.load_segments("plan"), a, b)
    ho = ok & (days >= M.HO_START) & (days <= ho_end)
    lv = np.unique(seg[tr])
    row = sc.set_index("pair").loc[pair]
    tau = int(row.tau_days)
    beta, *_ = np.linalg.lstsq(M.design(seg, ty, ph, feats[tau], tr, lv), sm[tr], rcond=None)
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(7.4, 4.6), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
    fig.subplots_adjust(left=0.1, right=0.97, bottom=0.1, top=0.88, hspace=0.08)
    ax.plot(days[ok], sm[ok], color=INK, lw=1, label="observed dv/v (30-day mean)")
    ax.plot(days[tr], M.design(seg, ty, ph, feats[tau], tr, lv) @ beta, color=BLUE, lw=1.2, label="model, training fit")
    ax.plot(days[ho], M.design(seg, ty, ph, feats[tau], ho, lv) @ beta, color=ORANGE, lw=1.2, label="model, held-out prediction")
    ax.axvline(M.HO_START, color=GREY, lw=0.8, ls=":")
    ax.set_ylabel("dv/v (%)"); ax.grid(axis="y", color=GRID, lw=0.5); ax.legend(frameon=False, fontsize=7.5, loc="lower left")
    mon = era.precip_mm.resample("MS").sum()
    ax2.bar(mon.index, mon.to_numpy(), width=25, color=GREY)
    ax2.set_ylabel("rain (mm/mo)"); ax2.grid(axis="y", color=GRID, lw=0.5)
    fig.suptitle(f"{pair}, the most coherent pair: held-out R² {row.heldout_r2:.1f}", x=0.02, ha="left", fontsize=10.5, color=INK)
    fig.savefig(F / "F2_example_pair.png", dpi=170); plt.close(fig)
    caption("F2_example_pair", f"""{pair} (mean training coherence {row.train_coherence:.2f}; tau = {tau} days). Black: observed
    dv/v, stretching at 0.5-2 Hz, 30-day running mean. Blue: the model fitted on 2013-2020. Orange: its prediction from
    2021, with nothing refitted. Lower panel: ERA5 monthly rainfall at the field's centre.""")


if __name__ == "__main__":
    p = json.load(open(T / "primary.json"))
    f1(p); f2()
    print("figures written")
