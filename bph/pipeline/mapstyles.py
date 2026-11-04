"""Step 7b: data for the workshop map styles on the Map tab (public data only).

- Ocean depth (for the bathymetric Spilhaus style): Natural Earth 10m bathymetry polygons (public domain),
  one layer per depth from 200 m to 10,000 m, simplified for a world map.
- Exclusive economic zones (for the Large Ocean States style): Flanders Marine Institute (2023), Maritime
  Boundaries Geodatabase: Maritime Boundaries and Exclusive Economic Zones (200NM), version 12, via the
  Marine Regions web feature service (CC BY 4.0, https://www.marineregions.org). Pacific Island countries
  and territories, Aotearoa New Zealand and Australia; zones that cross 180 degrees are merged.

Writes data/bathy.json and data/eez.json. Downloads are cached in <WORK>/mapdata.
"""

import io
import json
import os
import time
import zipfile
from pathlib import Path

import requests
import shapefile  # pyshp
from shapely.geometry import MultiPolygon, mapping, shape
from shapely.ops import unary_union
from shapely.affinity import translate

ROOT = Path(__file__).resolve().parents[1]
WORK = Path(os.environ.get("BPH_WORK", "/mnt/data/ubuntu/bph-work"))
CACHE = WORK / "mapdata"
NE = "https://naciscdn.org/naturalearth/10m/physical/ne_10m_bathymetry_{}.zip"
BANDS = ["K_200", "J_1000", "I_2000", "H_3000", "G_4000", "F_5000", "E_6000", "D_7000", "C_8000", "B_9000", "A_10000"]
WFS = ("https://geo.vliz.be/geoserver/MarineRegions/wfs?service=WFS&version=1.0.0&request=GetFeature"
       "&typeName=MarineRegions:eez&outputFormat=application/json&CQL_FILTER=iso_ter1 IN ({})")
PI = "ASM COK FJI FSM GUM KIR MHL MNP NCL NIU NRU PCN PLW PNG PYF SLB TKL TON TUV VUT WLF WSM".split()
CONTEXT = ["NZL", "AUS"]
UA = {"User-Agent": "bph-pacific-landscape"}


def get(url, name):
    f = CACHE / name
    if not f.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        for attempt in range(5):
            try:
                r = requests.get(url, headers=UA, timeout=300)
                r.raise_for_status()
                f.write_bytes(r.content)
                break
            except requests.RequestException:
                if attempt == 4:
                    raise
                time.sleep(5 * (attempt + 1))
    return f.read_bytes()


def rnd(geom, nd):
    def r(c):
        return [round(c[0], nd), round(c[1], nd)]
    g = mapping(geom)
    if g["type"] == "Polygon":
        g["coordinates"] = [[r(c) for c in ring] for ring in g["coordinates"]]
    elif g["type"] == "MultiPolygon":
        g["coordinates"] = [[[r(c) for c in ring] for ring in poly] for poly in g["coordinates"]]
    return g


def bathymetry():
    feats = []
    for band in BANDS:
        z = zipfile.ZipFile(io.BytesIO(get(NE.format(band), f"ne_10m_bathymetry_{band}.zip")))
        shp = next(n for n in z.namelist() if n.endswith(".shp"))
        base = shp[:-4]
        sf = shapefile.Reader(shp=io.BytesIO(z.read(shp)), shx=io.BytesIO(z.read(base + ".shx")), dbf=io.BytesIO(z.read(base + ".dbf")))
        depth = int(band.split("_")[1])
        # Each band's polygons do not overlap, so they are simplified one by one (no union: it is slow and
        # not needed for filled bands); specks under ~0.25 square degrees are dropped.
        parts = []
        for sh in sf.shapes():
            # deep bands are narrow trenches (Kermadec, Tonga): finer simplification and a smaller speck size
            g = shape(sh.__geo_interface__).simplify(0.18 if depth < 6000 else 0.04, preserve_topology=True)
            if not g.is_valid:
                g = g.buffer(0)
            parts += [p for p in getattr(g, "geoms", [g]) if p.geom_type == "Polygon" and p.area > (0.25 if depth < 6000 else 0.004)]
        if parts:
            feats.append(dict(type="Feature", properties=dict(depth=depth), geometry=rnd(MultiPolygon(parts), 2)))
        print(f"  bathymetry {depth} m: {len(parts)} polygons")
    return dict(type="FeatureCollection", features=feats)


def eez():
    codes = ",".join(f"'{c}'" for c in PI + CONTEXT)
    data = json.loads(get(WFS.format(codes).replace(" ", "%20"), "eez_pacific.json"))
    by = {}
    for f in data["features"]:
        p = f["properties"]
        if p.get("pol_type") != "200NM":
            continue
        key = p["iso_ter1"]
        g = shape(f["geometry"]).buffer(0)
        # zones crossing 180 degrees come in two halves: move the western half east and merge
        if g.bounds[0] <= -179.9 or g.bounds[2] >= 179.9:
            parts = list(getattr(g, "geoms", [g]))
            g = unary_union([translate(x, 360, 0) if x.bounds[2] <= 0 else x for x in parts])
        rec = by.setdefault(key, dict(geoms=[], name=p.get("territory1") or p.get("geoname"), sov=p.get("iso_sov1")))
        rec["geoms"].append(g)
    feats = []
    for key, rec in by.items():
        g = unary_union(rec["geoms"]).simplify(0.06, preserve_topology=True)
        feats.append(dict(type="Feature", properties=dict(iso=key, name=rec["name"], sov=rec["sov"],
                                                          group="pi" if key in PI else "context"),
                          geometry=rnd(g, 2)))
    print(f"  EEZ: {len(feats)} zones ({sum(1 for f in feats if f['properties']['group'] == 'pi')} Pacific Island)")
    return dict(type="FeatureCollection", features=feats)


def main():
    for name, data in (("bathy", dict(bathymetry(), source="Natural Earth 10m bathymetry (public domain), naturalearthdata.com")),
                       ("eez", dict(eez(), source="Flanders Marine Institute (2023). Maritime Boundaries Geodatabase: Maritime Boundaries "
                                                  "and Exclusive Economic Zones (200NM), version 12. marineregions.org, CC BY 4.0. "
                                                  "https://doi.org/10.14284/632"))):
        f = ROOT / "data" / f"{name}.json"
        f.write_text(json.dumps(data, separators=(",", ":")))
        print(f"wrote {f} ({f.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
