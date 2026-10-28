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
HL = RUN.parent / "auckland-nz-hirds-out-of-sample-exceedance-audit"
COUNCIL = {"Northland": "Northland Region", "HawkesBay": "Hawke's Bay Region", "Wellington": "Wellington Region",
           "Marlborough": "Marlborough Region", "Tasman": "Tasman Region", "Taranaki": "Taranaki Region",
           "WestCoast": "West Coast Region", "Auckland": "Auckland Region"}
_NB = {"Tasman Region": {"Nelson Region", "West Coast Region", "Marlborough Region", "Canterbury Region"},
       "Auckland Region": {"Waikato Region", "Northland Region"}, "Wellington Region": {"Manawatu-Wanganui Region"},
       "Hawke's Bay Region": {"Gisborne Region", "Manawatu-Wanganui Region", "Bay of Plenty Region", "Waikato Region"},
       "Taranaki Region": {"Manawatu-Wanganui Region", "Waikato Region"}, "Marlborough Region": {"Canterbury Region", "Nelson Region"},
       "West Coast Region": {"Canterbury Region", "Otago Region", "Southland Region"}}
NEIGHBOURS = {}
for k, vs in _NB.items():
    for v in vs:
        NEIGHBOURS.setdefault(k, set()).add(v); NEIGHBOURS.setdefault(v, set()).add(k)
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
    # D2: a candidate is consistent with the record's regional council unless its nearest gauge within 10 km belongs
    # to a council that is neither that council nor a neighbour of it (gauge locations only; no outcomes)
    H = pd.read_parquet(HL / "data" / "hirds_depths.parquet").groupby("file")[["lat", "lon"]].first()
    glat, glon = H.lat.to_numpy(), H.lon.to_numpy()
    gcouncil = H.index.str.split("__").str[0].map(COUNCIL).to_numpy()

    def consistent(c, region):
        dist = np.hypot((glon[None, :] - c[:, 1:2]) * 111.32 * np.cos(np.radians(c[:, 0:1])), (glat[None, :] - c[:, 0:1]) * 110.57)
        j = dist.argmin(1)
        near = dist[np.arange(len(c)), j] <= 10
        ok_council = np.array([gcouncil[k] == region or gcouncil[k] in NEIGHBOURS.get(region, set()) for k in j])
        return ~near | ok_council
    s["cands"] = [cand[k][consistent(cand[k], r)] if k in cand else None for k, r in zip(s.key, s.region)]
    s["n_cand"] = s.cands.map(lambda c: -1 if c is None else len(c))
    uni = s[s.n_cand == 1].copy()
    uni[["lat", "lon"]] = np.vstack([c[0] for c in uni.cands]) if len(uni) else np.empty((0, 2))
    cen = uni.groupby("tla")[["lat", "lon"]].median()
    rows = []
    for r in s.itertuples():
        c = r.cands
        if c is None:
            rows.append((np.nan, np.nan, "unmatched")); continue
        if len(c) == 0:
            rows.append((np.nan, np.nan, "council_mismatch")); continue
        if len(c) == 1:
            rows.append((c[0][0], c[0][1], "unique")); continue
        if r.tla in cen.index:
            la, lo = cen.loc[r.tla]
            j = np.argmin(np.hypot((c[:, 1] - lo) * np.cos(np.radians(la)), c[:, 0] - la))
            rows.append((c[j][0], c[j][1], "tla_centroid")); continue
        rows.append((np.nan, np.nan, "ambiguous"))
    s[["lat", "lon", "match"]] = pd.DataFrame(rows, index=s.index)
    s.drop(columns=["key", "cands"]).to_parquet(D / "suburbs.parquet")
    by = s.groupby("match").agg(suburbs=("suburb", "size"), exposures=("exposures", "sum"))
    out = {"suburbs": len(s), "exposure_days": int(s.exposures.sum()), "by_match": by.to_dict("index"),
           "share_exposure_days_geocoded": round(float(s.exposures[s.match.isin(["unique", "tla_centroid"])].sum() / s.exposures.sum()), 4)}
    (T / "geocode.json").write_text(json.dumps(out, indent=1, default=int) + "\n")
    print(json.dumps(out, indent=1, default=int))


if __name__ == "__main__":
    main()
