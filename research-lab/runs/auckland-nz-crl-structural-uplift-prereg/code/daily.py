"""Load AT daily boardings by mode and apply the preregistered day filters (plan.md section 3).

load(cutoff) returns one row per day up to and including `cutoff`, with columns
date, bus, train, ferry, ratio (train / bus), dow, holiday, disrupted, eligible.

Disruption rule (plan.md 3): a day is disrupted if train or bus boardings fall below 60% of the median of that mode on
the same weekday over the preceding 8 weeks. Details fixed here:
- D5 (after review): the reference is the median of the last 8 preceding same-weekday days that were neither public
  holidays nor themselves flagged disrupted, so the summer rail shutdown and Christmas weeks cannot drag the reference
  down. Days are processed in date order within each weekday. The series has no missing dates (checked in load), so
  "8 same-weekday days" and "8 weeks" coincide for clean stretches.
- D1: until 8 such clean days exist (the start of the series), the reference is the median of the first 8 non-holiday
  same-weekday values.
The daily files are listed in DAILY. When AT re-releases a year, the new file replaces the old entry (it must not be
added alongside it, because drop_duplicates keeps the first file's value for a date).
"""
from pathlib import Path

import holidays
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
DAILY = [
    "bus-train-and-ferry-boardings-by-day-report-2023-2024.xlsx",
    "auckland-transport-bus-train-and-ferry-boardings-by-day-july-2024-to-june-2025.xlsx",
    "auckland-transport-bus-train-ferry-boardings-by-day-2025-to-2026.xlsx",
    "bus-train-ferry-boardings-by-day-2026-to-2027-2.xlsx",
]
OPEN_CUTOFF = pd.Timestamp("2026-09-10")  # last pre-opening day used for calibration (plan.md 4)


def _read(name):
    d = pd.read_excel(RAW / name, header=7)
    d = d[pd.to_datetime(d["Date"], errors="coerce").notna()].copy()
    d["date"] = pd.to_datetime(d["Date"])
    return d.rename(columns={"Bus": "bus", "Train": "train", "Ferry": "ferry"})[["date", "bus", "train", "ferry"]]


def raw(cutoff):
    d = pd.concat([_read(n) for n in DAILY]).drop_duplicates("date").sort_values("date")
    d = d[d.date <= pd.Timestamp(cutoff)].reset_index(drop=True)
    assert (d.date.diff().dropna() == pd.Timedelta(days=1)).all(), "missing or duplicate dates in the daily series"
    for c in ["bus", "train", "ferry"]:
        d[c] = pd.to_numeric(d[c])
    return d


def _disrupted(d):
    """Sequential disruption flags (D1, D5): reference = median of the last 8 clean same-weekday days."""
    flag = pd.Series(False, index=d.index)
    modes = ["bus", "train"]
    for k in range(7):
        g = d[d.dow == k]
        seed = g.loc[~g.holiday, modes].iloc[:8].median()
        clean = []  # rows (bus, train) of preceding non-holiday, non-disrupted days
        for i, r in g.iterrows():
            ref = pd.DataFrame(clean[-8:], columns=modes).median() if len(clean) >= 8 else seed
            dis = any(r[m] < 0.6 * ref[m] for m in modes)
            flag.loc[i] = dis
            if not dis and not r.holiday:
                clean.append((r.bus, r.train))
    return flag


def load(cutoff=OPEN_CUTOFF):
    d = raw(cutoff)
    d["dow"] = d.date.dt.dayofweek  # Mon=0
    nz = holidays.country_holidays("NZ", subdiv="AUK", years=range(2023, 2029))
    d["holiday"] = d.date.dt.date.map(lambda x: x in nz)
    d["disrupted"] = _disrupted(d)
    d["ratio"] = d.train / d.bus
    d["eligible"] = d.dow.isin([1, 2, 3]) & ~d.holiday & ~d.disrupted
    return d
