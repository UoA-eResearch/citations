"""Parse every quarterly coverage file into one tidy table (data/coverage.parquet):
quarter_end (period end date), milestone (months: 6, 8, 12, 18, 24, 54, 60), district, group, eligible, immunised.

Two layout families:
- archive (Ministry of Health / Te Whatu Ora, Apr 2009 - Mar 2023): one sheet per milestone; the first table on each
  sheet is "coverage by prioritised ethnicity" with a "DHB" header row, group names (Total, NZE, Maori, Pacific, Asian,
  Other) over triples of (No. Eligible, Fully Immunised, %).
- current (Health NZ, Jul 2023 on): sheet "Ethnicity", one long table with columns Milestone Age, District of
  residence, Region and groups (Total, Maori, Pacific, Asian, European or Other) over triples.

Groups are harmonised to Total, Maori, Pacific, Asian and European or Other (archive NZE + Other summed; a sum is
missing if either part is suppressed). Suppressed cells ('n/s', '*', blanks) stay missing and are never
back-calculated. District names are harmonised to the 20 Health NZ districts (old DHB boundaries)."""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
MONTHS = {m.lower(): i for i, m in enumerate(["January", "February", "March", "April", "May", "June", "July", "August",
                                                  "September", "October", "November", "December"], 1)}
DISTRICTS = {
    "auckland": "Auckland", "bay of plenty": "Bay of Plenty", "canterbury": "Canterbury", "capital & coast": "Capital and Coast",
    "capital and coast": "Capital and Coast", "counties manukau": "Counties Manukau", "hawkes bay": "Hawke's Bay",
    "hawke's bay": "Hawke's Bay", "hutt": "Hutt Valley", "hutt valley": "Hutt Valley", "lakes": "Lakes", "midcentral": "MidCentral",
    "mid central": "MidCentral", "nelson marlborough": "Nelson Marlborough", "northland": "Northland",
    "south canterbury": "South Canterbury", "southern": "Southern", "otago": "Otago", "southland": "Southland",
    "tairawhiti": "Tairāwhiti", "tairāwhiti": "Tairāwhiti", "taranaki": "Taranaki", "waikato": "Waikato", "wairarapa": "Wairarapa",
    "waitemata": "Waitematā", "waitematā": "Waitematā", "west coast": "West Coast", "whanganui": "Whanganui",
    "national total": "National total", "national": "National total", "total": "National total", "new zealand": "National total",
}
GROUPS = {"total": "Total", "nze": "NZE", "nz european": "NZE", "european": "NZE", "maori": "Maori", "māori": "Maori",
          "pacific": "Pacific", "asian": "Asian", "other": "Other", "european or other": "European or Other"}


def num(x):
    if isinstance(x, (int, float, np.integer, np.floating)) and not pd.isna(x):
        return float(x)
    s = str(x).strip().replace(",", "")
    return float(s) if re.fullmatch(r"\d+(\.\d+)?", s) else np.nan


def quarter_end_from_name(name):
    """Period end from an archive file name like '1-April-2013-to-30-June-2013' or '1-October-2009-to-1-January-2010'."""
    m = re.findall(r"(\d{1,2})-([A-Za-z]+)-(\d{4})", name)
    (d1, m1, y1), (d2, m2, y2) = m[0], m[1]
    start = pd.Timestamp(int(y1), MONTHS[m1.lower()], 1)
    return (start + pd.offsets.QuarterEnd(0)).normalize()


def milestone_of(text):
    t = str(text).lower()
    if "year" in t:
        n = int(re.search(r"\d+", t).group())
        return 12 * n
    m = re.search(r"(\d+)\s*month", t)
    return int(m.group(1)) if m else None


def clean_district(x):
    s = re.sub(r"\s+", " ", str(x)).strip().lower().replace(" dhb", "").replace(" district", "")
    return DISTRICTS.get(s)


def parse_archive(f):
    q = quarter_end_from_name(f.name)
    out = []
    xl = pd.ExcelFile(f)
    for sh in xl.sheet_names:
        ms = milestone_of(sh)
        if ms is None:
            continue
        d = pd.read_excel(f, sheet_name=sh, header=None)
        hdr = None
        for r in range(min(len(d), 40)):
            row = [str(v).strip().lower() for v in d.iloc[r].tolist()]
            if any(re.fullmatch(r"(dhb( area| of residence)?|district( of residence)?)", v) for v in row) and any(v in GROUPS for v in row):
                hdr = r
                break
        if hdr is None:
            continue
        cols = {}
        row = [str(v).strip().lower() for v in d.iloc[hdr].tolist()]
        for c, v in enumerate(row):
            if v in GROUPS:
                cols[GROUPS[v]] = c
        dcol = next(c for c, v in enumerate(row) if re.fullmatch(r"(dhb( area| of residence)?|district( of residence)?)", v))
        for r in range(hdr + 2, len(d)):
            name = d.iat[r, dcol]
            if pd.isna(name) or str(name).strip() == "":
                if out and r > hdr + 25:
                    break
                continue
            dist = clean_district(name)
            if dist is None:
                if re.search(r"deprivation|quintile|ethnicity", str(name), re.I):
                    break
                continue
            for g, c in cols.items():
                out.append(dict(quarter_end=q, milestone=ms, district=dist, group=g, eligible=num(d.iat[r, c]), immunised=num(d.iat[r, c + 1]), file=f.name))
            if dist == "National total":
                break
    return out


def quarter_end_current(name):
    """Period end from a Health NZ file name: '...-july-2023-september-2023.xlsx' or '...-q3-25-26.xlsx' (NZ fiscal
    quarters: Q1 Jul-Sep, Q2 Oct-Dec, Q3 Jan-Mar, Q4 Apr-Jun)."""
    m = re.search(r"q([1-4])-(\d{2})-(\d{2})", name)
    if m:
        k, y1 = int(m.group(1)), 2000 + int(m.group(2))
        month, year = {1: (9, y1), 2: (12, y1), 3: (3, y1 + 1), 4: (6, y1 + 1)}[k]
        return (pd.Timestamp(year, month, 1) + pd.offsets.MonthEnd(0)).normalize()
    m = re.findall(r"([a-z]+)-(\d{4})", name.lower())
    mon, yr = m[-1]
    return (pd.Timestamp(int(yr), MONTHS[mon], 1) + pd.offsets.MonthEnd(0)).normalize()


def parse_current(f, end=None):
    out = []
    xl = pd.ExcelFile(f)
    if "Ethnicity" not in xl.sheet_names:
        return out
    d = pd.read_excel(f, sheet_name="Ethnicity", header=None)
    end = end if end is not None else quarter_end_current(f.name)
    hdr = next(r for r in range(len(d)) if any(str(d.iat[r, c]).strip().lower().startswith("milestone age") for c in (0, 1)))
    mcol = 0 if str(d.iat[hdr, 0]).strip().lower().startswith("milestone age") else 1
    dcol = 1 - mcol  # 2020 Q3 files put the district first
    grow = [str(v).strip().lower() for v in d.iloc[hdr - 1].tolist()]
    cols = {}
    for c, v in enumerate(grow):  # first column of each group (some files repeat the name over its three columns)
        if v in GROUPS and GROUPS[v] not in cols:
            cols[GROUPS[v]] = c
    ms, dist = None, None
    for r in range(hdr + 1, len(d)):
        mc, dc = d.iat[r, mcol], d.iat[r, dcol]
        if not (pd.isna(mc) or str(mc).strip() == ""):
            ms = milestone_of(mc)  # some files label only the first row of each block
        if not (pd.isna(dc) or str(dc).strip() == ""):
            dist = clean_district(dc)
        if ms is None or dist is None:
            continue
        for g, c in cols.items():
            out.append(dict(quarter_end=end.normalize(), milestone=ms, district=dist, group=g, eligible=num(d.iat[r, c]), immunised=num(d.iat[r, c + 1]), file=f.name))
    return out


def main():
    rows = []
    for f in sorted((RAW / "archive3m").glob("*.xls*")):
        try:
            if "Ethnicity" in pd.ExcelFile(f).sheet_names:  # late archive files (2020 Q3 on) use the long layout
                rows += parse_current(f, end=quarter_end_from_name(f.name))
            else:
                rows += parse_archive(f)
        except Exception as e:  # noqa: BLE001
            print("ARCHIVE FAIL", f.name, repr(e)[:200])
    for f in sorted((RAW / "current").glob("quarterly-*.xlsx")):
        try:
            rows += parse_current(f)
        except Exception as e:  # noqa: BLE001
            print("CURRENT FAIL", f.name, repr(e)[:200])
    d = pd.DataFrame(rows)
    # harmonise archive NZE + Other into European or Other (missing if either part is suppressed)
    arch = d[d.group.isin(["NZE", "Other"])]
    eo = arch.groupby(["quarter_end", "milestone", "district", "file"]).agg(
        eligible=("eligible", lambda x: x.sum() if x.notna().all() and len(x) == 2 else np.nan),
        immunised=("immunised", lambda x: x.sum() if x.notna().all() and len(x) == 2 else np.nan)).reset_index()
    eo["group"] = "European or Other"
    d = pd.concat([d[~d.group.isin(["NZE", "Other"])], eo], ignore_index=True)
    d = d.drop_duplicates(["quarter_end", "milestone", "district", "group"], keep="last")
    d.to_parquet(RUN / "data" / "coverage.parquet")
    t = d[(d.district == "National total") & (d.group == "Total")].pivot_table(index="quarter_end", columns="milestone", values="eligible")
    print(t.to_string())
    print(d.groupby("group").size().to_dict(), "| quarters:", d.quarter_end.nunique(), "| districts:", sorted(d.district.unique()))


if __name__ == "__main__":
    main()
