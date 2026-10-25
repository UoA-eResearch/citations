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
    con = duckdb.connect()
    con.execute("SET threads TO 16; SET memory_limit = '48GB'")
    con.execute(f"""
        CREATE TABLE r AS SELECT CAST(specieskey AS BIGINT) AS specieskey, decimallatitude AS lat, decimallongitude AS lon,
               year, datasetkey, institutioncode, family, countrycode, coordinateuncertaintyinmeters AS unc,
               lower(establishmentmeans) AS em, occurrencestatus AS os,
               list_transform(issue, x -> x.array_element) AS iss
        FROM read_parquet('{D / "gbif_s3"}/*.parquet')""")
    n_in = con.execute("SELECT count(*) FROM r").fetchone()[0]
    em_values = dict(con.execute("SELECT em, count(*) FROM r GROUP BY em ORDER BY 2 DESC").fetchall())
    con.execute(f"""
        ALTER TABLE r ADD COLUMN why VARCHAR;
        UPDATE r SET why = CASE
            WHEN list_has_any(iss, {ISSUES}) THEN 'r1 GBIF coordinate issue'
            WHEN unc > 10000 THEN 'r2 uncertainty > 10 km'
            WHEN lat = lon OR (abs(lat) < 0.5 AND abs(lon) < 0.5) THEN 'r3 equal or near-zero coordinates'
            WHEN em IN ('introduced', 'naturalised', 'naturalized', 'invasive', 'managed') OR os = 'ABSENT'
                THEN 'r4 introduced, managed or absent'
            ELSE NULL END""")
    dense = con.execute("""
        CREATE TABLE dense AS SELECT round(lat, 4) AS rl, round(lon, 4) AS ro, count(DISTINCT specieskey) AS nsp
        FROM r WHERE why IS NULL GROUP BY 1, 2 HAVING count(DISTINCT specieskey) > 1000;
        SELECT count(*), coalesce(sum(nsp), 0) FROM dense""").fetchone()
    con.execute("ALTER TABLE r ADD COLUMN why_no_r5 VARCHAR; UPDATE r SET why_no_r5 = why")
    con.execute("""UPDATE r SET why = 'r5 high-density point' FROM dense
                   WHERE r.why IS NULL AND round(r.lat, 4) = dense.rl AND round(r.lon, 4) = dense.ro""")
    con.execute("ALTER TABLE r ADD COLUMN cy INTEGER; ALTER TABLE r ADD COLUMN cx INTEGER;"
                "UPDATE r SET cy = CAST(floor(12 * lat) AS INTEGER), cx = CAST(floor(12 * lon) AS INTEGER)")
    cells = con.execute("SELECT DISTINCT cy, cx FROM r WHERE why_no_r5 IS NULL").fetchnumpy()
    cy, cx = cells["cy"].astype(np.int64), cells["cx"].astype(np.int64)
    tree = land_tree()
    hit = tree.query(box(cx / 12, cy / 12, (cx + 1) / 12, (cy + 1) / 12), predicate="intersects")[0]
    land = np.zeros(len(cy), bool)
    land[np.unique(hit)] = True
    con.register("sea", {"cy": cy[~land].astype(np.int32), "cx": cx[~land].astype(np.int32)})
    for col in ("why", "why_no_r5"):
        con.execute(f"""UPDATE r SET {col} = 'r6 sea cell' FROM sea
                        WHERE r.{col} IS NULL AND r.cy = sea.cy AND r.cx = sea.cx""")
        con.execute(f"UPDATE r SET {col} = 'r7 no species key' WHERE {col} IS NULL AND specieskey IS NULL")
    keep = """SELECT specieskey, lat, lon, year, CASE WHEN year <= 2000 THEN 1 ELSE 2 END AS period, cy, cx,
                     datasetkey, institutioncode, family, countrycode FROM r"""
    con.execute(f"COPY ({keep} WHERE why IS NULL) TO '{D / 'clean.parquet'}' (FORMAT parquet, COMPRESSION zstd)")
    con.execute(f"COPY ({keep} WHERE why_no_r5 IS NULL) TO '{D / 'clean_no_r5.parquet'}' (FORMAT parquet, COMPRESSION zstd)")
    drops = dict(con.execute("SELECT why, count(*) FROM r WHERE why IS NOT NULL GROUP BY 1 ORDER BY 1").fetchall())
    n_ok = con.execute("SELECT count(*) FROM r WHERE why IS NULL").fetchone()[0]
    n_ok_no_r5 = con.execute("SELECT count(*) FROM r WHERE why_no_r5 IS NULL").fetchone()[0]
    cov = Coverage("records_clean", T / "coverage.json")
    cov.add_counts(ok=n_ok, drops=drops)
    cov.save()
    out = {"records_in": n_in, "records_kept": n_ok, "records_kept_without_r5": n_ok_no_r5, "drops": drops,
           "dense_points": int(dense[0]), "land_cells": int(land.sum()), "sea_cells": int((~land).sum()),
           "establishmentmeans_values": {str(k): v for k, v in em_values.items()}}
    (T / "clean_summary.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
