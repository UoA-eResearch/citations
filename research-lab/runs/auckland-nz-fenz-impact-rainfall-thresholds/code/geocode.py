"""FENZ Suburb (+TLA) -> NZ Gazetteer point (plan section 1).

Names are normalised (macrons and punctuation removed, case folded). A name with one gazetteer place is taken; a name
with several takes the one nearest the centroid of the uniquely matched suburbs in the same TLA. Feature types:
Suburb, Locality, Town, City, Village and other populated-place types.

  geocode.py -> data/suburbs.parquet (suburb, tla, region, lat, lon, match), results/tables/geocode.json
"""
import json
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
PLACES = {"Suburb", "Locality", "Town", "City", "Village", "Settlement", "Township", "Hamlet", "Urban Area"}


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def main():
    g = pd.read_csv(D / "raw_gaz" / "gaz.csv", encoding="utf-8-sig", usecols=["name", "feat_type", "crd_latitude", "crd_longitude"],
                    low_memory=False)
    g = g[g.feat_type.isin(PLACES) & g.crd_latitude.notna()].assign(key=lambda x: x.name.map(norm))
    g = g.drop_duplicates(["key", "crd_latitude", "crd_longitude"])
    f = pd.read_parquet(D / "fenz_daily.parquet")
    s = f.groupby(["suburb", "tla", "region"]).agg(exposures=("nonflood", "size")).reset_index()
    s["key"] = s.suburb.map(norm)
    cand = g.groupby("key")[["crd_latitude", "crd_longitude"]].apply(lambda x: x.to_numpy()).to_dict()
    s["n_cand"] = s.key.map(lambda k: len(cand.get(k, [])))
    uni = s[s.n_cand == 1].copy()
    uni[["lat", "lon"]] = np.vstack([cand[k][0] for k in uni.key]) if len(uni) else np.empty((0, 2))
    cen = uni.groupby("tla")[["lat", "lon"]].median()
    rows = []
    for r in s.itertuples():
        c = cand.get(r.key)
        if c is None:
            rows.append((np.nan, np.nan, "unmatched")); continue
        if len(c) == 1:
            rows.append((c[0][0], c[0][1], "unique")); continue
        if r.tla in cen.index:
            la, lo = cen.loc[r.tla]
            j = np.argmin(np.hypot((c[:, 1] - lo) * np.cos(np.radians(la)), c[:, 0] - la))
            rows.append((c[j][0], c[j][1], "tla_centroid")); continue
        rows.append((np.nan, np.nan, "ambiguous"))
    s[["lat", "lon", "match"]] = pd.DataFrame(rows, index=s.index)
    s.drop(columns="key").to_parquet(D / "suburbs.parquet")
    by = s.groupby("match").agg(suburbs=("suburb", "size"), exposures=("exposures", "sum"))
    out = {"suburbs": len(s), "exposure_days": int(s.exposures.sum()), "by_match": by.to_dict("index"),
           "share_exposure_days_geocoded": round(float(s.exposures[s.match.isin(["unique", "tla_centroid"])].sum() / s.exposures.sum()), 4)}
    (T / "geocode.json").write_text(json.dumps(out, indent=1, default=int) + "\n")
    print(json.dumps(out, indent=1, default=int))


if __name__ == "__main__":
    main()
