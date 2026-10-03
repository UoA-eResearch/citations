"""Pre-opening calibration for H1 (plan.md section 4). Uses only days up to 10 Sep 2026.

1. Baseline: R_pre = mean of the window means R(W_2024), R(W_2025), R(W_2026), W_y = 16 Feb - 25 Mar of year y;
   the same for train and bus boardings (mean per eligible day).
2. Placebo error: for every 38-day window starting 1 Feb 2025 - 1 Aug 2026, that window's mean over the mean of the
   same calendar window in every earlier year with data, minus 1. q05 / q95 of these placebo uplifts.
3. The decision thresholds this implies for the 2027 window, written down now.
Output: results/tables/baseline_windows.csv, placebo_uplifts.csv, h1_thresholds.csv; results/figures/pre_ratio.png
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import daily as D  # noqa: E402

TAB = D.RUN / "results" / "tables"
FIG = D.RUN / "results" / "figures"
SERIES = ["ratio", "train", "bus"]
FIRST = pd.Timestamp("2023-07-01")
MIN_DAYS = 9  # D2 (after review): minimum eligible days in a window and in each comparison-year window; also W_2027


def window_mean(d, start, end):
    w = d[(d.date >= start) & (d.date <= end) & d.eligible]
    return {s: w[s].mean() for s in SERIES} | {"n": len(w)}


def baseline(d):
    rows = []
    for y in (2024, 2025, 2026):
        s, e = pd.Timestamp(f"{y}-02-16"), pd.Timestamp(f"{y}-03-25")
        rows.append(dict(year=y, start=s.date(), end=e.date()) | window_mean(d, s, e))
    return pd.DataFrame(rows)


def placebo(d):
    rows = []
    for s in pd.date_range("2025-02-01", "2026-08-01"):
        e = s + pd.Timedelta(days=37)
        now = window_mean(d, s, e)
        past = []
        for k in (1, 2, 3):
            ps, pe = s - pd.DateOffset(years=k), e - pd.DateOffset(years=k)
            if ps >= FIRST:
                m = window_mean(d, ps, pe)
                if m["n"] >= MIN_DAYS:
                    past.append(m)
        if now["n"] < MIN_DAYS or not past:
            continue
        r = dict(start=s.date(), n_days=now["n"], n_years=len(past), min_past_days=min(p["n"] for p in past))
        for v in SERIES:
            r[f"u_{v}"] = now[v] / np.mean([p[v] for p in past]) - 1
        rows.append(r)
    return pd.DataFrame(rows)


def main():
    d = D.load(D.OPEN_CUTOFF)
    assert d.date.max() <= D.OPEN_CUTOFF
    b = baseline(d)
    b.to_csv(TAB / "baseline_windows.csv", index=False)
    p = placebo(d)
    p.to_csv(TAB / "placebo_uplifts.csv", index=False)
    rows = []
    for v in SERIES:
        q05, q50, q95 = np.quantile(p[f"u_{v}"], [0.05, 0.5, 0.95])
        pre = b[v].mean()
        r = dict(series=v, pre_mean=pre, q05=q05, q50=q50, q95=q95, n_windows=len(p))
        if v == "ratio":  # the decision rule applies to the ratio only; train and bus are descriptive (plan.md 5)
            sup = max(0.20, 0.10 + q95)  # Supported needs U >= 0.20 and U - q95 > 0.10
            con = 0.20 + q05  # Contradicted if U - q05 < 0.20
            r |= dict(supported_if_U_above=sup, contradicted_if_U_below=con,
                      supported_if_post_above=pre * (1 + sup), contradicted_if_post_below=pre * (1 + con))
        rows.append(r)
    t = pd.DataFrame(rows)
    t.to_csv(TAB / "h1_thresholds.csv", index=False)
    # disclosure (review finding 3): quantiles by number of comparison years, and the approximate number of
    # independent 38-day blocks behind the placebo distribution
    strat = p.groupby("n_years").u_ratio.describe(percentiles=[0.05, 0.5, 0.95])
    strat["independent_blocks_approx"] = p.groupby("n_years").size() / 38
    strat.to_csv(TAB / "placebo_by_years.csv")
    print(strat.round(4).to_string())
    print(b.round(4).to_string(index=False))
    print(t.round(4).to_string(index=False))
    print(p.groupby("n_years").size().to_dict(), "min eligible days in a window", p.n_days.min())

    e = d[d.eligible]
    fig, ax = plt.subplots(figsize=(10, 3.6))
    ax.plot(e.date, e.ratio, ".", ms=3, color="#33658a")
    for y in (2024, 2025, 2026, 2027):
        ax.axvspan(pd.Timestamp(f"{y}-02-16"), pd.Timestamp(f"{y}-03-25"), color="#f6ae2d", alpha=0.25, lw=0)
    ax.axhline(t.set_index("series").supported_if_post_above["ratio"], color="#2f8f5b", lw=1, ls="--")
    ax.axhline(t.set_index("series").contradicted_if_post_below["ratio"], color="#b5443b", lw=1, ls="--")
    ax.axvline(pd.Timestamp("2026-09-13"), color="k", lw=0.8)
    ax.set_xlim(pd.Timestamp("2023-07-01"), pd.Timestamp("2027-04-15"))
    ax.set_ylabel("train / bus boardings")
    ax.set_title("Eligible Tue-Thu days to 10 Sep 2026; shaded = 16 Feb-25 Mar windows; dashed = 2027 decision lines",
                 fontsize=9)
    fig.tight_layout()
    fig.savefig(FIG / "pre_ratio.png", dpi=150)


if __name__ == "__main__":
    main()
