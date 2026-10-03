"""Split OpenStreetMap drivable roads (NZ extract 2026-10-02) into segments of at most 100 m (NZTM).

Each OSM way of a public-road highway class is cut into ceil(length / 100 m) equal pieces. Output columns:
seg (int id), way, highway, cls (grouped class), name, ref, length_m, geometry (LineString), mx, my (midpoint).
Output: data/segments.parquet
"""
from pathlib import Path

import geopandas as gpd
import numpy as np
import osmium
import pandas as pd
from pyproj import Transformer
from shapely.geometry import LineString
from shapely.ops import substring

RUN = Path(__file__).resolve().parents[1]
PBF = RUN / "data" / "raw" / "new-zealand-261002.osm.pbf"
CLASSES = {
    "motorway": "motorway", "motorway_link": "motorway",
    "trunk": "trunk", "trunk_link": "trunk",
    "primary": "primary", "primary_link": "primary",
    "secondary": "secondary", "secondary_link": "secondary",
    "tertiary": "tertiary", "tertiary_link": "tertiary",
    "unclassified": "local", "residential": "local", "living_street": "local", "road": "local",
}
MAXLEN = 100.0
TO_NZTM = Transformer.from_crs(4326, 2193, always_xy=True)


def ways():
    fp = osmium.FileProcessor(str(PBF)).with_locations().with_filter(osmium.filter.KeyFilter("highway"))
    for o in fp:
        if not o.is_way():
            continue
        hw = o.tags.get("highway")
        if hw not in CLASSES:
            continue
        if o.tags.get("access") in ("private", "no") or o.tags.get("area") == "yes":
            continue
        try:
            coords = [(n.lon, n.lat) for n in o.nodes]
        except osmium.InvalidLocationError:
            continue
        if len(coords) < 2:
            continue
        yield o.id, hw, o.tags.get("name", ""), o.tags.get("ref", ""), coords


def main():
    rows = []
    for wid, hw, name, ref, coords in ways():
        x, y = TO_NZTM.transform(*zip(*coords))
        line = LineString(zip(x, y))
        L = line.length
        if L == 0:
            continue
        k = max(1, int(np.ceil(L / MAXLEN)))
        for i in range(k):
            piece = line if k == 1 else substring(line, L * i / k, L * (i + 1) / k)
            m = piece.interpolate(0.5, normalized=True)
            rows.append((wid, hw, CLASSES[hw], name, ref, piece.length, piece, m.x, m.y))
    df = pd.DataFrame(rows, columns=["way", "highway", "cls", "name", "ref", "length_m", "geometry", "mx", "my"])
    g = gpd.GeoDataFrame(df, geometry="geometry", crs=2193)
    g.insert(0, "seg", np.arange(len(g)))
    g.to_parquet(RUN / "data" / "segments.parquet")
    print(len(g), "segments;", f"{g.length_m.sum() / 1000:,.0f} km;", g.cls.value_counts().to_dict())


if __name__ == "__main__":
    main()
