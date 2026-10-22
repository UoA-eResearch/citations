"""Secondary (plan section 4): audit Digital Earth Pacific Coastlines (v0.7.0-55) against this study's islet rates.

For each islet, DEP rate-of-change points within 100 m of the islet ring are pooled:
- mean rate_time (m/yr, positive = seaward), the share significant, and an implied areal rate:
  100 x mean rate x perimeter / area (%/yr);
- DEP's own early and late rates, as least-squares slopes of each point's annual distance over 1999-2015 and over
  2016-2023, averaged over the islet's points.

Writes results/tables/dep_audit_islets.csv. Comparison with this study's rates happens in rates.py's output
afterwards.
"""
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyproj
import shapely

sys.path.insert(0, str(Path(__file__).resolve().parent))
from inventory import ATOLLS  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
GPKG = RUN / "data" / "raw" / "dep_ls_coastlines_0-7-0-55.gpkg"
ENV = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}


def geom(blob):
    flags = blob[3]
    return shapely.from_wkb(bytes(blob[8 + ENV[(flags >> 1) & 7]:]))


def utm(lon, lat):
    return f"EPSG:{(32600 if lat >= 0 else 32700) + int((lon + 180) // 6) + 1}"


def main():
    c = sqlite3.connect(GPKG)
    cols = [r[1] for r in c.execute('pragma table_info("rates_of_change")')]
    dcols = [x for x in cols if x.startswith("dist_")]
    years = np.array([int(x[5:]) for x in dcols])
    to3832 = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3832", always_xy=True)
    inv = pd.read_csv(RUN / "data" / "inventory.csv")
    inv = inv[inv.area_ha >= 1]
    rows = []
    for name, (gid, (s, w, n, e)) in ATOLLS.items():
        xs, ys = to3832.transform([w, e, w, e], [s, s, n, n])
        q = (f'select r.{", r.".join(["geom", "rate_time", "sig_time", "se_time", "outl_time"] + dcols)} '
             f'from rates_of_change r join rtree_rates_of_change_geom t on r.fid = t.id '
             f'where t.maxx >= {min(xs)} and t.minx <= {max(xs)} and t.maxy >= {min(ys)} and t.miny <= {max(ys)}')
        pts = c.execute(q).fetchall()
        if not pts:
            print(name, "no DEP points"); continue
        P = pd.DataFrame(pts, columns=["geom", "rate", "sig", "se", "outl"] + dcols)
        g3832 = [geom(b) for b in P.geom]
        isl = inv[inv.atoll == name]
        cx, cy = shapely.centroid(shapely.from_wkt(isl.wkt.iloc[0])).coords[0]
        crs = utm(cx, cy)
        t1 = pyproj.Transformer.from_crs("EPSG:3832", crs, always_xy=True)
        t2 = pyproj.Transformer.from_crs("EPSG:4326", crs, always_xy=True)
        pxy = np.array([t1.transform(p.x, p.y) for p in g3832])
        tree = shapely.STRtree(shapely.points(pxy))
        D = P[dcols].to_numpy(float)
        early = years <= 2015
        late = years >= 2016

        def slope(m):
            yy = years[m].astype(float)
            out = np.full(len(D), np.nan)
            for k in range(len(D)):
                v = D[k, m]
                ok = np.isfinite(v)
                if ok.sum() >= 5:
                    out[k] = np.polyfit(yy[ok], v[ok], 1)[0]
            return out
        se_, sl_ = slope(early), slope(late)
        for _, r in isl.iterrows():
            ring = shapely.transform(shapely.from_wkt(r.wkt), lambda a: np.column_stack(t2.transform(a[:, 0], a[:, 1])))
            idx = tree.query(ring.boundary.buffer(100.0), predicate="intersects")
            if len(idx) == 0:
                rows.append({"islet": r.islet, "atoll": name, "dep_points": 0}); continue
            per, area = ring.length, ring.area
            mr = float(np.nanmean(P.rate.to_numpy(float)[idx]))
            rows.append({"islet": r.islet, "atoll": name, "dep_points": int(len(idx)), "dep_rate_m_yr": mr,
                         "dep_sig_share": float(np.mean(P.sig.to_numpy(float)[idx] < 0.01)),
                         "dep_area_rate_pct": 100 * mr * per / area,
                         "dep_early_m_yr": float(np.nanmean(se_[idx])), "dep_late_m_yr": float(np.nanmean(sl_[idx])),
                         "perimeter_m": per, "area_m2": area})
        print(name, len(P), "DEP points;", sum(1 for x in rows if x["atoll"] == name and x.get("dep_points")), "islets matched",
              flush=True)
    pd.DataFrame(rows).to_csv(RUN / "results" / "tables" / "dep_audit_islets.csv", index=False)


if __name__ == "__main__":
    main()
