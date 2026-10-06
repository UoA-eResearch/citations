"""Assign each document to a comparison group from Federal Register agency metadata (no text):
DOT (the department and its operating administrations) vs the 14 other cabinet departments (and their sub-agencies);
everything else (independent agencies) is excluded. Flags templated rule classes by title regex (plan section 2).
Writes data/meta/fr_groups.parquet and results/tables/counts_by_group_period.csv."""
import json
import re
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
DEPTS = {"agriculture-department": "USDA", "commerce-department": "Commerce", "defense-department": "Defense",
         "education-department": "Education", "energy-department": "Energy", "health-and-human-services-department": "HHS",
         "homeland-security-department": "DHS", "housing-and-urban-development-department": "HUD", "interior-department": "Interior",
         "justice-department": "Justice", "labor-department": "Labor", "state-department": "State",
         "transportation-department": "DOT", "treasury-department": "Treasury", "veterans-affairs-department": "VA"}
TEMPLATED = re.compile(r"airworthiness directive|class [a-e] airspace|class e2|class e[0-9]? airspace|airspace|ifr altitudes|"
                       r"standard instrument approach|safety zone|security zone|special local regulation|drawbridge operation|"
                       r"regulated navigation area|anchorage|restricted area|danger zone|tolerances? for|pesticide|"
                       r"approval and promulgation of (?:air quality )?implementation plans", re.I)


def dept_of(agencies, by_id):
    """Top-level cabinet department of the first agency in the list that resolves to one."""
    for a in agencies:
        cur, seen = a, 0
        while cur is not None and seen < 5:
            if cur.get("slug") in DEPTS:
                return DEPTS[cur["slug"]]
            cur = by_id.get(cur.get("parent_id"))
            seen += 1
    return None


def main():
    m = pd.read_parquet(RUN / "data" / "meta" / "fr_meta.parquet")
    ags = m.agencies.map(json.loads)
    by_id = {}
    for lst in ags:
        for a in lst:
            if a.get("id"):
                by_id[a["id"]] = a
    m["dept"] = [dept_of(a, by_id) for a in ags]
    # D9 (after review): the API lists the parent department first, so take the first listed agency that is not a
    # cabinet department itself (agencies[0] made every DOT document "Transportation Department")
    m["subagency"] = [next(((x.get("name") or x.get("raw_name")) for x in a if x.get("slug") not in DEPTS), a[0].get("name")) if a else None for a in ags]
    m["ferc"] = [any("Federal Energy Regulatory Commission" in (x.get("name") or "") for x in a) for a in ags]
    m["group"] = m.dept.map(lambda d: "excluded" if pd.isna(d) else ("DOT" if d == "DOT" else "other_cabinet"))  # D1: NaN is truthy
    m["templated"] = m.title.fillna("").str.contains(TEMPLATED)
    d = pd.to_datetime(m.publication_date)
    m["period"] = pd.cut(d, [pd.Timestamp("2018-12-31"), pd.Timestamp("2021-12-31"), pd.Timestamp("2023-12-31"),
                             pd.Timestamp("2025-12-31"), pd.Timestamp("2026-01-31"), pd.Timestamp("2026-09-30")],
                         labels=["2019-21 (human reference)", "2022-23", "2024-25 (pre)", "2026-01 (excluded)", "2026-02..09 (post)"])
    m.drop(columns=["abstract"]).to_parquet(RUN / "data" / "meta" / "fr_groups.parquet")
    c = m[~m.templated].groupby(["period", "group", "type"], observed=True).size().unstack(["type"]).fillna(0).astype(int)
    c.to_csv(RUN / "results" / "tables" / "counts_by_group_period.csv")
    print(c.to_string())
    print("templated share by group:", m.groupby("group").templated.mean().round(3).to_dict())
    print("DOT sub-agencies (non-templated, all periods):", m[(m.group == "DOT") & ~m.templated].subagency.value_counts().head(12).to_dict())


if __name__ == "__main__":
    main()
