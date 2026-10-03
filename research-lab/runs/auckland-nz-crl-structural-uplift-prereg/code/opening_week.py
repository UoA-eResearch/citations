"""Opening-week uplift U_open (plan.md section 5, persistence denominator). Reads days up to 17 Sep 2026.

U_open = mean eligible R over Tue-Thu 15-17 Sep 2026 / mean of the same quantity over the Tue-Thu of ISO week 38 in
2023, 2024 and 2025 - 1. ('Corresponding week' = same ISO week; deviations.md D4.)
Every post-opening day this script reads is listed in viewing_log.md.
Output: results/tables/opening_week.csv
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import daily as D  # noqa: E402

CUTOFF = pd.Timestamp("2026-09-17")


def main():
    d = D.load(CUTOFF)
    iso = d.date.dt.isocalendar()
    d["year"], d["week"] = iso.year.values, iso.week.values
    w = d[(d.week == 38) & d.dow.isin([1, 2, 3])]
    out = w[["date", "year", "bus", "train", "ratio", "holiday", "disrupted", "eligible"]]
    out.to_csv(D.RUN / "results" / "tables" / "opening_week.csv", index=False)
    m = out[out.eligible].groupby("year")[["ratio", "train", "bus"]].mean()
    base = m.loc[[2023, 2024, 2025]].mean()
    u = m.loc[2026] / base - 1
    print(out.round(4).to_string(index=False))
    print("U_open:", u.round(4).to_dict())


if __name__ == "__main__":
    main()
