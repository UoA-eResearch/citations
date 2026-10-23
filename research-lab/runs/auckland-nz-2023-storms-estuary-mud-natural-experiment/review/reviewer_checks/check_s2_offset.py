"""Reviewer check 4: does the s2.py offset rule ('0.5th percentile of red DN < 900 => offset already removed') decide
correctly on the Earth Search COGs used? Reads STAC metadata and a small window of one pre- and one post-window scene.

Network-bound, light CPU. stdout -> check_s2_offset.out.
"""
import json
import sys
import urllib.request
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin

RUN = Path("/mnt/citations/research-lab/runs/auckland-nz-2023-storms-estuary-mud-natural-experiment")
sys.path.insert(0, str(RUN / "code"))
import s2  # noqa: E402

# a 10 km x 10 km window over the upper Waitemata / Riverhead (forest, pasture, harbour water), NZTM
X0, Y1 = 1740000.0, 5930000.0
N = 1000                       # 10 m pixels
tf10 = from_origin(X0, Y1, 10.0, 10.0)

for window in ("pre", "post"):
    feats = s2.search(window, max_cloud=40)
    # scenes whose footprint contains the window centre (west Auckland is tile 60HTD, not 60HUD); clearest first
    import pyproj
    lo_c, la_c = pyproj.Transformer.from_crs(2193, 4326, always_xy=True).transform(X0 + 5000, Y1 - 5000)
    cand = sorted([f for f in feats if f["bbox"][0] <= lo_c <= f["bbox"][2] and f["bbox"][1] <= la_c <= f["bbox"][3]],
                  key=lambda f: f["properties"]["eo:cloud_cover"])
    print(f"\n{window}: {len(cand)} scenes cover the window centre ({lo_c:.3f}, {la_c:.3f}); tiles {sorted({f['tile'] for f in cand})}")
    if not cand:
        continue
    for f in cand[:2]:
        p = f["properties"]
        rb_red = (f["assets"]["red"].get("raster:bands") or [{}])[0]
        print(f"\n{window}: {f['id']}  cloud {p.get('eo:cloud_cover')}  baseline {p.get('s2:processing_baseline')}  "
              f"red raster:bands scale/offset {rb_red.get('scale')}/{rb_red.get('offset')}  href {f['assets']['red']['href'][:80]}")
        r = s2.reflectance(f, ["red", "nir"], "EPSG:2193", tf10, (N, N))
        if r is None:
            print("  no data in window"); continue
        ref, scl, valid, strip = r
        dn_red = s2.read_warped(f["assets"]["red"]["href"], "EPSG:2193", tf10, (N, N), Resampling.average)
        dn_nir = s2.read_warped(f["assets"]["nir"]["href"], "EPSG:2193", tf10, (N, N), Resampling.average)
        print(f"  s2.py decision in this window: offset_already_removed = {strip}  (0.5th pct red DN = {np.percentile(dn_red[valid], 0.5):.0f})")
        for cls, name in ((6, "water"), (4, "vegetation"), (5, "not vegetated")):
            m = valid & (scl == cls)
            if m.sum() < 100:
                continue
            q = np.percentile(dn_red[m], [0.5, 5, 50, 95])
            qn = np.percentile(dn_nir[m], [5, 50, 95])
            print(f"  SCL {cls} {name:<14} n={m.sum():>7}  red DN p0.5/5/50/95 = {q.round(0)}  nir DN p5/50/95 = {qn.round(0)}")
        # NDVI of dense vegetation under both conventions
        m = valid & (scl == 4)
        red_a, nir_a = dn_red[m] * 1e-4, dn_nir[m] * 1e-4                     # offset NOT subtracted (what s2.py did if strip)
        red_b, nir_b = red_a - 0.1, nir_a - 0.1                               # offset subtracted
        nd_a = (nir_a - red_a) / (nir_a + red_a)
        nd_b = (nir_b - red_b) / np.maximum(nir_b + red_b, 1e-6)
        print(f"  vegetation NDVI, offset kept   : p10/50/90 = {np.percentile(nd_a, [10, 50, 90]).round(2)}  share >= 0.5: {(nd_a >= 0.5).mean():.2f}  share <= 0.3: {(nd_a <= 0.3).mean():.2f}")
        print(f"  vegetation NDVI, offset removed: p10/50/90 = {np.percentile(nd_b, [10, 50, 90]).round(2)}  share >= 0.5: {(nd_b >= 0.5).mean():.2f}  share <= 0.3: {(nd_b <= 0.3).mean():.2f}")
        m5 = valid & (scl == 5)
        if m5.sum() > 100:
            ra, na = dn_red[m5] * 1e-4, dn_nir[m5] * 1e-4
            print(f"  not-vegetated NDVI, offset kept   : p10/50/90 = {np.percentile((na - ra) / (na + ra), [10, 50, 90]).round(2)}; "
                  f"offset removed: {np.percentile((na - ra) / np.maximum(na + ra - 0.2, 1e-6), [10, 50, 90]).round(2)}")
        # what reflectance did s2.py actually hand on?
        print(f"  s2.reflectance red for vegetation: median {np.nanmedian(ref['red'][m]):.3f} (physically ~0.02-0.06 for dense vegetation)")
        break
