"""Cleaning (plan section 1), rules applied in order; each dropped record is counted under the first rule it fails.

  r1 GBIF issue ZERO_COORDINATE, COORDINATE_INVALID, COORDINATE_OUT_OF_RANGE or COUNTRY_COORDINATE_MISMATCH
  r2 coordinate uncertainty > 10 km (missing kept)
  r3 latitude = longitude, or within 0.5 degrees of (0, 0)
  r4 establishment means introduced / naturalised / invasive / managed, or occurrence status ABSENT
  r5 coordinate pair (rounded to 1e-4 degrees) carrying > 1,000 distinct species among records passing r1-r4
  r6 5-arcmin cell not intersecting Natural Earth 10 m land or minor islands
  r7 no species key

-> data/clean.parquet (specieskey, lat, lon, year, period, cy, cx, datasetkey, institutioncode, family, countrycode)
   data/clean_no_r5.parquet (sensitivity: rule 5 not applied), results/tables/clean_summary.json, coverage.json
"""
import json
import sys
import zipfile
from pathlib import Path

import duckdb
import numpy as np
import shapefile
from shapely import STRtree, box
from shapely.geometry import shape

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
sys.path.insert(0, str(RUN.parents[1] / "tools"))
from coverage import Coverage  # noqa: E402

ISSUES = ["ZERO_COORDINATE", "COORDINATE_INVALID", "COORDINATE_OUT_OF_RANGE", "COUNTRY_COORDINATE_MISMATCH"]


def land_tree():
    geoms = []
    for z in ("ne_10m_land.zip", "ne_10m_minor_islands.zip"):
        with zipfile.ZipFile(D / "ref" / z) as f:
            stem = z[:-4]
            r = shapefile.Reader(shp=f.open(stem + ".shp"), shx=f.open(stem + ".shx"), dbf=f.open(stem + ".dbf"))
            geoms += [shape(s.__geo_interface__) for s in r.shapes()]
    return STRtree(geoms)


def main():
    """Every record is classified once, by a single SELECT over joins (no in-place UPDATEs: D2), and the classes must
    sum to the input."""
    con = duckdb.connect()
    con.execute("SET threads TO 16; SET memory_limit = '48GB'")
    con.execute(f"""
        CREATE TABLE a AS SELECT CAST(specieskey AS BIGINT) AS specieskey, decimallatitude AS lat, decimallongitude AS lon,
               year, datasetkey, institutioncode, family, countrycode,
               CAST(floor(12 * decimallatitude) AS INTEGER) AS cy, CAST(floor(12 * decimallongitude) AS INTEGER) AS cx,
               lower(establishmentmeans) AS em,
               CASE WHEN list_has_any(list_transform(issue, x -> x.array_element), {ISSUES}) THEN 'r1 GBIF coordinate issue'
                    WHEN coordinateuncertaintyinmeters > 10000 THEN 'r2 uncertainty > 10 km'
                    WHEN decimallatitude = decimallongitude OR (abs(decimallatitude) < 0.5 AND abs(decimallongitude) < 0.5)
                        THEN 'r3 equal or near-zero coordinates'
                    WHEN lower(establishmentmeans) IN ('introduced', 'naturalised', 'naturalized', 'invasive', 'managed')
                         OR occurrencestatus = 'ABSENT' THEN 'r4 introduced, managed or absent'
                    ELSE NULL END AS w14
        FROM read_parquet('{D / "gbif_s3"}/*.parquet')""")
    n_in = con.execute("SELECT count(*) FROM a").fetchone()[0]
    em_values = dict(con.execute("SELECT em, count(*) FROM a GROUP BY em ORDER BY 2 DESC").fetchall())
    con.execute("""CREATE TABLE dense AS SELECT round(lat, 4) AS rl, round(lon, 4) AS ro, count(DISTINCT specieskey) AS nsp
                   FROM a WHERE w14 IS NULL GROUP BY 1, 2 HAVING count(DISTINCT specieskey) > 1000""")
    n_dense = con.execute("SELECT count(*) FROM dense").fetchone()[0]
    cells = con.execute("SELECT DISTINCT cy, cx FROM a WHERE w14 IS NULL").df()
    hit = land_tree().query(box(cells.cx / 12, cells.cy / 12, (cells.cx + 1) / 12, (cells.cy + 1) / 12),
                            predicate="intersects")[0]
    cells["land"] = False
    cells.loc[np.unique(hit), "land"] = True
    con.register("cells", cells)
    con.execute("""
        CREATE TABLE c AS SELECT a.*, (d.rl IS NOT NULL) AS isdense, coalesce(cl.land, FALSE) AS land,
               CASE WHEN a.w14 IS NOT NULL THEN a.w14 WHEN d.rl IS NOT NULL THEN 'r5 high-density point'
                    WHEN NOT coalesce(cl.land, FALSE) THEN 'r6 sea cell' WHEN a.specieskey IS NULL THEN 'r7 no species key'
                    ELSE NULL END AS why,
               CASE WHEN a.w14 IS NOT NULL THEN a.w14 WHEN NOT coalesce(cl.land, FALSE) THEN 'r6 sea cell'
                    WHEN a.specieskey IS NULL THEN 'r7 no species key' ELSE NULL END AS why_no_r5
        FROM a LEFT JOIN dense d ON round(a.lat, 4) = d.rl AND round(a.lon, 4) = d.ro
               LEFT JOIN cells cl ON a.cy = cl.cy AND a.cx = cl.cx""")
    assert con.execute("SELECT count(*) FROM c").fetchone()[0] == n_in, "join changed the row count"
    keep = """SELECT specieskey, lat, lon, year, CASE WHEN year <= 2000 THEN 1 ELSE 2 END AS period, cy, cx,
                     datasetkey, institutioncode, family, countrycode FROM c"""
    con.execute(f"COPY ({keep} WHERE why IS NULL) TO '{D / 'clean.parquet'}' (FORMAT parquet, COMPRESSION zstd)")
    con.execute(f"COPY ({keep} WHERE why_no_r5 IS NULL) TO '{D / 'clean_no_r5.parquet'}' (FORMAT parquet, COMPRESSION zstd)")
    drops = dict(con.execute("SELECT why, count(*) FROM c WHERE why IS NOT NULL GROUP BY 1 ORDER BY 1").fetchall())
    n_ok = con.execute("SELECT count(*) FROM read_parquet(?)", [str(D / "clean.parquet")]).fetchone()[0]
    n_ok_no_r5 = con.execute("SELECT count(*) FROM read_parquet(?)", [str(D / "clean_no_r5.parquet")]).fetchone()[0]
    assert n_ok + sum(drops.values()) == n_in, (n_ok, sum(drops.values()), n_in)
    cov = Coverage("records_clean", T / "coverage.json")
    cov.add_counts(ok=n_ok, drops=drops)
    cov.save()
    out = {"records_in": n_in, "records_kept": n_ok, "records_kept_without_r5": n_ok_no_r5, "drops": drops,
           "dense_points": int(n_dense), "land_cells": int(cells.land.sum()), "sea_cells": int((~cells.land).sum()),
           "establishmentmeans_values": {str(k): v for k, v in em_values.items()}}
    (T / "clean_summary.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
