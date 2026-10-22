"""Freeze the site list (plan section 1) from sampling dates and counts only; no indicator value is read into the output.

Auckland Council sites with Mud_content in at least 5 distinct years 2010-2022 and a 2023 row.
Writes results/tables/sites.csv.
"""
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw" / "lawa_estuary_2025v2.xlsx"


def main():
    d = pd.read_excel(RAW, sheet_name="Data", usecols=["Council/Agency", "Region", "LAWA Site ID", "Site name",
                                                        "Estuary name", "Latitude", "Longitude",
                                                        "Date sampled (YYYY/MM/DD)", "Indicator"])
    d = d[(d["Council/Agency"] == "Auckland Council") & (d.Indicator == "Mud_content")].copy()
    d["year"] = pd.to_datetime(d["Date sampled (YYYY/MM/DD)"]).dt.year
    g = d.groupby("LAWA Site ID")
    s = pd.DataFrame({"site_name": g["Site name"].first(), "estuary": g["Estuary name"].first(),
                      "lat": g.Latitude.first(), "lon": g.Longitude.first(),
                      "pre_years": g.year.apply(lambda y: y[(y >= 2010) & (y <= 2022)].nunique()),
                      "has_2023": g.year.apply(lambda y: bool((y == 2023).any())),
                      "has_2024": g.year.apply(lambda y: bool((y == 2024).any()))})
    s = s[(s.pre_years >= 5) & s.has_2023].sort_index()
    s.index.name = "site_id"
    s.to_csv(RUN / "results" / "tables" / "sites.csv")
    print(len(s), "sites;", s.estuary.nunique(), "harbours;", int(s.has_2024.sum()), "with 2024")


if __name__ == "__main__":
    main()
