"""G3 hand trace: three species (seed 20261026, from the primary population) recomputed from the raw snapshot extract
with an independent, plain implementation (pandas filters, explicit thinning, spherical mean, haversine), and compared
with results/tables/observed_primary.parquet. Rule 5 (dense points) and rule 6 (sea cells) are taken from the cleaned
file's absence, so the trace checks rules 1-4 and 7, thinning, centroids and velocity independently.
-> results/tables/handtrace.json
"""
import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
BAD = {"ZERO_COORDINATE", "COORDINATE_INVALID", "COORDINATE_OUT_OF_RANGE", "COUNTRY_COORDINATE_MISMATCH"}


def centroid(lat, lon):
    la, lo = np.radians(lat), np.radians(lon)
    v = np.c_[np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)].sum(0)
    v /= np.linalg.norm(v)
    return np.degrees(np.arcsin(v[2])), np.degrees(np.arctan2(v[1], v[0]))


def haversine(a, b):
    p1, p2, dl = np.radians(a[0]), np.radians(b[0]), np.radians(b[1] - a[1])
    h = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * 6371.0088 * np.arcsin(np.sqrt(h))


def main():
    obs = pd.read_parquet(T / "nulls_primary.parquet")
    pick = obs.sample(3, random_state=20261026)
    con = duckdb.connect()
    out = []
    for r in pick.itertuples():
        raw = con.execute(f"""SELECT decimallatitude lat, decimallongitude lon, year, coordinateuncertaintyinmeters unc,
                              lower(establishmentmeans) em, occurrencestatus os,
                              list_transform(issue, x -> x.array_element) iss
                              FROM read_parquet('{D / "gbif_s3"}/*.parquet') WHERE specieskey = '{r.specieskey}'""").df()
        n_raw = len(raw)
        keep = raw[~raw.iss.map(lambda x: isinstance(x, (list, np.ndarray)) and bool(set(list(x)) & BAD))]
        keep = keep[~(keep.unc > 10000)]
        keep = keep[~((keep.lat == keep.lon) | ((keep.lat.abs() < 0.5) & (keep.lon.abs() < 0.5)))]
        keep = keep[~(keep.em.isin(["introduced", "naturalised", "naturalized", "invasive", "managed"]) | (keep.os == "ABSENT"))]
        clean = con.execute(f"SELECT lat, lon, period FROM read_parquet('{D / 'clean.parquet'}') WHERE specieskey = {r.specieskey}").df()
        cents = {}
        for p, yrs in ((1, (1970, 2000)), (2, (2001, 2024))):
            c = clean[clean.period == p]
            cells = pd.DataFrame({"cy": np.floor(12 * c.lat).astype(int), "cx": np.floor(12 * c.lon).astype(int)}).drop_duplicates()
            cents[p] = (centroid((cells.cy + 0.5) / 12, (cells.cx + 0.5) / 12), len(cells))
        v = haversine(cents[1][0], cents[2][0]) / 28
        out.append({"specieskey": int(r.specieskey), "raw_records": n_raw, "after_rules_1_4": int(len(keep)),
                    "clean_records": int(len(clean)), "cells_p1": cents[1][1], "cells_p2": cents[2][1],
                    "centroid_p1": [round(x, 4) for x in cents[1][0]], "centroid_p2": [round(x, 4) for x in cents[2][0]],
                    "trace_v_km_yr": round(float(v), 4), "table_v_km_yr": round(float(r.v_sph), 4),
                    "table_k1_k2": [int(r.k1), int(r.k2)], "effort_null_median": round(float(r.effort_med), 4),
                    "effort_null_p95": round(float(r.effort_p95), 4)})
        print(out[-1], flush=True)
    (T / "handtrace.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
