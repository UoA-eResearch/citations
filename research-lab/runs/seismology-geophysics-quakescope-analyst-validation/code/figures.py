"""Figures and key-result tiles for the report (after the outcome). Reads results/tables/; recomputes the H2 out-of-fold
predictions deterministically (same model, seed and folds as analysis.h2) to plot them and to confirm the R^2."""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402

FIG = A.RUN / "results" / "figures"
INK, MUTED, ACCENT, WARN, ALT = "#1d2733", "#6b7785", "#1f6f8b", "#c0562b", "#7b5ea7"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
                     "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 160, "savefig.bbox": "tight"})


def caption(name, text):
    (FIG / f"{name}.txt").write_text(text)


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    prim = json.load(open(A.TAB / "primary.json"))
    rel = pd.read_csv(A.TAB / "station_reliability.csv").set_index("netsta")
    r30 = rel[rel.n_ref >= A.MIN_H2]
    b = prim["H1"]["beta"]
    eta = b["Intercept"] + b["M"] * A.REF_M + b["logd"] * np.log10(A.REF_D)
    typical = 1 / (1 + np.exp(-eta))

    # 1. distribution of adjusted station recall
    fig, ax = plt.subplots(figsize=(6.4, 3.0))
    bins = np.linspace(0.1, 1.0, 46)  # 0.02 wide; the lowest station is at 0.13
    ax.hist(r30.recall_ref, bins=bins, color=ACCENT, edgecolor="white", linewidth=0.5)
    ax.axvline(typical, color=INK, lw=1)
    ax.text(typical - 0.01, ax.get_ylim()[1] * 0.92, f"typical station {typical:.1%}", ha="right", color=INK)
    lo10 = r30.recall_ref.quantile(0.10)
    ax.axvline(lo10, color=WARN, lw=1, ls="--")
    ax.text(lo10 - 0.01, ax.get_ylim()[1] * 0.75, f"1 station in 10\nbelow {lo10:.0%}", ha="right", color=WARN)
    alt = A.RUN / "results" / "tables" / "review" / "effects_excl_zero_days.csv"
    if alt.exists():  # D5: review-requested sensitivity, zero-pick station-days excluded
        e = pd.read_csv(alt).set_index("netsta")
        e = e[e.index.isin(r30.index)]
        ax.hist(e.recall_ref, bins=bins, histtype="step", color=ALT, linewidth=1.3, label="excluding zero-pick days (review)")
        ax.legend(loc="upper left", frameon=False)
    ax.set_xlabel("Adjusted P recall at the reference event (M 2.0 at 30 km), 0.5 s tolerance")
    ax.set_ylabel("Stations")
    fig.savefig(FIG / "station_recall.png")
    plt.close(fig)
    caption("station_recall", f"Adjusted P-pick recall for the {len(r30)} stations with at least 30 analyst-reviewed P picks "
            "(posterior-mean station effect from the mixed model, evaluated at an M 2.0 event 30 km away). The solid line is "
            "a station with a zero effect; the dashed line is the 10th percentile. The purple outline is the review-requested "
            "sensitivity analysis that drops station-days on which QuakeScope produced no picks (deviations.md D5).")

    # 2. map of station effects
    fig, ax = plt.subplots(figsize=(5.2, 5.6))
    o = r30.sort_values("recall_ref", ascending=False)
    sc = ax.scatter(o.longitude, o.latitude, c=o.recall_ref, cmap="RdYlBu", vmin=0.6, vmax=1.0, s=14, edgecolor=INK, linewidth=0.2)
    ax.set_aspect(1 / np.cos(np.deg2rad(37)))
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    cb = fig.colorbar(sc, ax=ax, shrink=0.7, extend="min")
    cb.set_label("Adjusted P recall (M 2.0, 30 km)")
    fig.savefig(FIG / "station_map.png")
    plt.close(fig)
    caption("station_map", "Where the low-recall stations are: adjusted P recall by station location (CI, NC and BK "
            "stations with at least 30 reference P picks; colour scale clipped at 60%). Low-recall stations are drawn on top.")

    # 3. H2: observed vs out-of-fold predicted station effects
    d = A.prepare(pd.read_parquet(A.RUN / "data" / "matched.parquet"))
    cov = pd.read_parquet(A.RUN / "data" / "covariates.parquet").set_index("netsta")
    cov.loc[~np.isfinite(cov.log_noise) & cov.log_noise.notna(), "log_noise"] = np.nan
    eff = rel.loc[r30.index, ["u", "u_sd"]]
    X, y, g, cat, x = A.design(eff, cov, d, A.PRIMARY_X)
    res, pred = A.cv_r2(X, y, g, cat)
    assert abs(res["R2"] - prim["H2"]["R2"]) < 1e-9, (res["R2"], prim["H2"]["R2"])
    fig, ax = plt.subplots(figsize=(4.6, 4.2))
    ax.scatter(pred, y, s=7, color=ACCENT, alpha=0.55, linewidth=0)
    lim = [min(y.min(), pred.min()) - 0.2, max(y.max(), pred.max()) + 0.2]
    ax.plot(lim, lim, color=MUTED, lw=0.8)
    ax.set_xlim(lim)
    ax.set_ylim(lim)
    ax.set_xlabel("Predicted from band, instrument, sampling rate, noise (out of fold)")
    ax.set_ylabel("Station effect (logit scale)")
    ax.text(0.03, 0.96, f"cross-validated R² = {res['R2']:.2f}\n(95% CI {res['lower95']:.2f} to {res['upper95']:.2f})",
            transform=ax.transAxes, va="top", color=INK)
    fig.savefig(FIG / "h2_predicted.png")
    plt.close(fig)
    caption("h2_predicted", f"Station attributes predict little of the station effect (H2): out-of-fold predictions from "
            f"gradient boosting with spatially grouped 5-fold cross-validation, {len(y)} stations. The line is perfect prediction.")

    # tiles
    h1, h2 = prim["H1"], prim["H2"]
    sd_note = f"95% CI {h1['lower95']:.3f}-{h1['upper95']:.3f}; H1 {h1['verdict']}"
    zj = A.RUN / "results" / "tables" / "review" / "h1_excl_zero_days.json"
    if zj.exists():  # D5: the review-requested denominator
        z = json.load(open(zj))["H1"]
        sd_note += f" ({z['SD_p']:.3f}, {z['verdict']}, without zero-output days)"
    tiles = [["Reference P picks", f"{h1['n_picks']:,}", f"{h1['n_stations']:,} CI/NC/BK stations, 30 months 2010-2024"],
             ["Pooled P recall", f"{d.y.mean():.1%}", "within 0.5 s of an analyst-reviewed pick"],
             ["Between-station SD", f"{h1['SD_p']:.3f}", sd_note],
             ["Explained by attributes", f"R² {h2['R2']:.2f}", f"95% CI {h2['lower95']:.2f}-{h2['upper95']:.2f}; H2 {h2['verdict']}"]]
    json.dump(tiles, open(A.TAB / "tiles.json", "w"), indent=1, ensure_ascii=False)
    print(tiles)


if __name__ == "__main__":
    main()
