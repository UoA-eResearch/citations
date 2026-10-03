"""Approximate each wastewater site's catchment from open boundaries, using no outcome data.

Rule (fixed before any outcome analysis; to be frozen in plan.md):
- Each SA1 2023 is placed in the Urban Rural 2023 area containing its representative point.
- A site whose DisplayName equals an Urban Rural 2023 area name (accents and case ignored) gets that area's SA1s as its
  catchment. Sites without an exact name match (metro multi-plant sites and a few others) have no catchment here.
- Validation: the summed 2023 usually-resident population of the catchment must be within +/-25% of the site's
  population in ESR's sites.csv; otherwise the site is excluded from the primary analysis.
- Covariates: population-weighted NZDep2023 score (SA1s with a score), share aged 65+ (Census 2023 via Eagle
  Technology's SA1 layer, which matches the Otago file's population and NZDep scores for 99.7% of SA1s), log ESR
  population, sampler type (Autosampler / Grab; 'Auto/grab' counts as Autosampler), region.
Output: data/catchments.csv
"""
import unicodedata
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"


def n(x):
    return unicodedata.normalize("NFKD", str(x)).encode("ascii", "ignore").decode().lower().strip()


def main():
    s = pd.read_csv(RAW / "covid_in_wastewater" / "data_historic" / "sites.csv")
    sa1 = gpd.read_parquet(RAW / "sa1_2023.parquet")
    sa1 = sa1[sa1.geometry.notna()].copy()
    sa1["code"] = pd.to_numeric(sa1.SA12023_V1_00)
    ur = gpd.read_parquet(RAW / "ur_2023.parquet")[["UR2023_V1_00_NAME", "geometry"]]
    pts = gpd.GeoDataFrame(sa1[["code"]], geometry=sa1.representative_point(), crs=2193)
    j = gpd.sjoin(pts, ur, how="left", predicate="within").drop_duplicates("code")
    dep = pd.read_excel(RAW / "NZDep2023_SA1_withHigherGeo.xlsx")
    age = pd.read_parquet(RAW / "eagle_census_sa1_age.parquet")
    age["code"] = pd.to_numeric(age.SA12023_code)
    a = j[["code", "UR2023_V1_00_NAME"]].merge(dep[["SA12023_code", "NZDep2023_Score", "URPopnSA1_2023"]],
                                                left_on="code", right_on="SA12023_code", how="left")
    a = a.merge(age[["code", "C23_Age65Plus", "C23_AgeLifeTot"]], on="code", how="left")
    a["urn"] = a.UR2023_V1_00_NAME.map(n)
    rows = []
    for r in s.itertuples():
        c = a[a.urn == n(r.DisplayName)]
        pop = c.URPopnSA1_2023.sum()
        w = c[c.NZDep2023_Score.notna() & c.URPopnSA1_2023.notna()]
        dep_w = np.average(w.NZDep2023_Score, weights=w.URPopnSA1_2023) if len(w) and w.URPopnSA1_2023.sum() > 0 else np.nan
        p65 = c.C23_Age65Plus.sum() / c.C23_AgeLifeTot.sum() if c.C23_AgeLifeTot.sum() > 0 else np.nan
        st = str(r.SampleType).strip()
        rows.append(dict(SampleLocation=r.SampleLocation, DisplayName=r.DisplayName, Region=r.Region,
                         esr_pop=r.Population, sampler="Autosampler" if st in ("Autosampler", "Auto/grab") else st,
                         name_match=len(c) > 0, n_sa1=len(c), sa1_pop=pop,
                         pop_ratio=pop / r.Population if len(c) else np.nan, nzdep_w=dep_w, p65=p65))
    out = pd.DataFrame(rows)
    out["accepted"] = out.name_match & (out.pop_ratio >= 0.75) & (out.pop_ratio <= 1.25)
    out.to_csv(RUN / "data" / "catchments.csv", index=False)
    out.to_csv(RUN / "results" / "tables" / "catchments.csv", index=False)
    print(out.name_match.sum(), "name-matched;", out.accepted.sum(), "accepted (+/-25% population)")
    print(out[out.name_match & ~out.accepted][["DisplayName", "esr_pop", "sa1_pop", "pop_ratio"]].round(2).to_string())


if __name__ == "__main__":
    main()
