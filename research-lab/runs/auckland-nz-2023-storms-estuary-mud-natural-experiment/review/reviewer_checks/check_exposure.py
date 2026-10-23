"""Reviewer check 3: sea mask, contributing land, newly bare patches, and exposure structure. Read-only on the study.

Memory: dem20 band 1 (float32, ~240 MB) + sea + bare. Single pass, then freed. stdout -> check_exposure.out.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyproj
import rasterio
from scipy import ndimage

RUN = Path("/mnt/citations/research-lab/runs/auckland-nz-2023-storms-estuary-mud-natural-experiment")
T = RUN / "results" / "tables"
D = RUN / "data"

sites = pd.read_csv(T / "sites.csv")
ex = pd.read_csv(T / "exposure.csv")
to_ll = pyproj.Transformer.from_crs(2193, 4326, always_xy=True)
to_xy = pyproj.Transformer.from_crs(4326, 2193, always_xy=True)

with rasterio.open(D / "sea20.tif") as ds:
    sea = ds.read(1).astype(bool); tf = ds.transform; shape = ds.shape
with rasterio.open(D / "dem20.tif") as ds:
    dem = ds.read(1)
h, w = shape
print("grid", shape, "res", tf.a, "origin", (tf.c, tf.f))


def cell_ll(flat):
    r, c = np.divmod(flat, w)
    x, y = tf.c + (c + 0.5) * tf.a, tf.f + (r + 0.5) * tf.e
    lo, la = to_ll.transform(x, y)
    return lo, la


def comp_report(mask, label, k=8, min_cells=500):
    lab, n = ndimage.label(mask, structure=np.ones((3, 3), bool))
    sz = np.bincount(lab.ravel())[1:]
    order = np.argsort(-sz)[:k]
    print(f"{label}: {n} components; {int((sz >= min_cells).sum())} with >= {min_cells} cells; total {sz.sum()} cells ({sz.sum() * 4e-4:.0f} km2)")
    for i in order:
        if sz[i] < min_cells:
            break
        rr, cc = np.nonzero(lab == i + 1)
        flat = rr.mean() * w + cc.mean()
        lo, la = cell_ll(int(round(rr.mean())) * w + int(round(cc.mean())))
        elev = dem[rr, cc]
        print(f"   {sz[i]:>8} cells {sz[i] * 4e-4:7.1f} km2  centroid lon {lo:.3f} lat {la:.3f}  elev median {np.nanmedian(elev):.2f} m  (rows {rr.min()}-{rr.max()}, cols {cc.min()}-{cc.max()})")
    return lab, sz


print("\n== 1. sea mask: what the '<= 0 m' and 'Sentinel-2 water' rules added beyond DEM no-data ==")
nod = np.isnan(dem)
low_only = sea & ~nod & (dem <= 0)
water_only = sea & ~nod & (dem > 0)
print("sea cells:", int(sea.sum()), "; no-data:", int((sea & nod).sum()), "; <=0 m (not no-data):", int(low_only.sum()),
      "; S2 water with DEM > 0 m:", int(water_only.sum()))
comp_report(low_only, "components of '<= 0 m' sea (outside no-data)")
comp_report(water_only, "components of S2-water sea above 0 m (rivers, wet flats)", min_cells=200)
print("elevation of S2-water sea cells above 0 m: quantiles", np.round(np.nanpercentile(dem[water_only], [50, 90, 99, 100]), 2))

print("\n== 2. is each site's own cell sea or land, and how high is it? ==")
sx, sy = to_xy.transform(sites.lon.to_numpy(), sites.lat.to_numpy())
sc, sr = (~tf) * (sx, sy)
sr, sc = np.floor(sr).astype(int), np.floor(sc).astype(int)
site_sea = sea[sr, sc]
print("sites whose own cell is sea:", int(site_sea.sum()), "of", len(sites), "; site-cell DEM (m) quantiles:",
      np.round(np.nanpercentile(dem[sr, sc], [0, 25, 50, 75, 100]), 2), "; no-data at site:", int(np.isnan(dem[sr, sc]).sum()))

print("\n== 3. contributing land C(R): nesting, extent and overlap ==")
z = np.load(D / "contrib.npz")
rows = []
for i, s in enumerate(sites.site_id):
    c2, c5, c10 = (z[f"{s}|route|{R}"] for R in (2, 5, 10))
    r5 = z[f"{s}|radius|5"]
    rr, cc = np.divmod(c5, w)
    x, y = tf.c + (cc + 0.5) * tf.a, tf.f + (rr + 0.5) * tf.e
    dist = np.hypot(x - sx[i], y - sy[i]) / 1000
    rows.append({"site": sites.site_name[i], "estuary": sites.estuary[i], "tercile": ex.tercile[i],
                 "C2<C5": bool(np.isin(c2, c5).all()), "C5<C10": bool(np.isin(c5, c10).all()),
                 "any_sea_in_C5": bool(sea.ravel()[c5].any()), "any_nodata_C5": bool(np.isnan(dem.ravel()[c5]).any()),
                 "C5_km2": len(c5) * 4e-4, "p50_dist_km": np.median(dist), "p95_dist_km": np.percentile(dist, 95), "max_dist_km": dist.max(),
                 "share_C5_within_5km": float((dist <= 5).mean()), "share_C5_in_radius5": float(np.isin(c5, r5).mean())})
cr = pd.DataFrame(rows)
pd.set_option("display.width", 250, "display.max_rows", 100)
print(cr.round(2).to_string(index=False))
print("nesting violations:", int((~cr["C2<C5"]).sum()), int((~cr["C5<C10"]).sum()), "; sea/nodata cells in C5:", int(cr.any_sea_in_C5.sum()), int(cr.any_nodata_C5.sum()))

print("\n== 4. within-harbour overlap of C(5) (Jaccard) -> how many distinct exposures the terciles really contain ==")
sets = {s: set(z[f"{s}|route|5"].tolist()) for s in sites.site_id}
for hname, g in sites.groupby("estuary"):
    ids = g.site_id.tolist()
    if len(ids) < 2:
        continue
    jac = []
    for a in range(len(ids)):
        for b in range(a + 1, len(ids)):
            A_, B_ = sets[ids[a]], sets[ids[b]]
            jac.append(len(A_ & B_) / len(A_ | B_))
    print(f"   {hname:<30} n={len(ids):>2}  Jaccard C5 min {min(jac):.2f} median {np.median(jac):.2f}  E range {100 * ex.set_index('site_id').E_route_5[ids].min():.3f}-{100 * ex.set_index('site_id').E_route_5[ids].max():.3f}%")
# overlap across the Whitford embayment harbours
whit = sites[sites.estuary.isin(["Mangemangeroa", "Tūranga", "Waikōpua"])].site_id.tolist()
inter = set.intersection(*[sets[s] for s in whit]); union = set.union(*[sets[s] for s in whit])
print(f"Whitford embayment (Mangemangeroa+Turanga+Waikopua, {len(whit)} sites): shared/union C5 = {len(inter) / len(union):.2f}")

print("\n== 5. newly bare: patches, where the big ones are, and the slip-sized share ==")
with rasterio.open(D / "bare20.tif") as ds:
    bare, valid = ds.read(1), ds.read(2)
lab, n = ndimage.label(bare > 0, structure=np.ones((3, 3), bool))
px = ndimage.sum(bare, lab, index=np.arange(1, n + 1))        # 10 m pixels per patch
cells = np.bincount(lab.ravel())[1:]
tot = bare.sum()
print(f"patches {n}; newly bare 10 m px {int(tot)} ({tot * 1e-2:.0f} ha); cells<=25 share {px[cells <= 25].sum() / tot:.3f}; cells>125 share {px[cells > 125].sum() / tot:.3f}")
for thr in (1, 2, 5, 10, 25):
    print(f"   patches of <= {thr} cells: {int((cells <= thr).sum())} ({px[cells <= thr].sum() / tot:.1%} of area)")
order = np.argsort(-px)[:12]
print("largest 12 patches:")
objs = ndimage.find_objects(lab)
for i in order:
    sl = objs[i]
    rr, cc = np.nonzero(lab[sl] == i + 1)
    r0, c0 = sl[0].start + rr.mean(), sl[1].start + cc.mean()
    lo, la = to_ll.transform(tf.c + (c0 + 0.5) * tf.a, tf.f + (r0 + 0.5) * tf.e)
    print(f"   {px[i]:>7.0f} px {px[i] * 1e-2:7.1f} ha  lon {lo:.3f} lat {la:.3f}  cells {cells[i]}")
# density of newly bare in known slip country vs market gardens (descriptive): 5 km circles
spots = {"Muriwai (slips)": (174.45, -36.83), "Piha/Karekare (slips)": (174.47, -36.95), "Titirangi (slips)": (174.65, -36.94),
         "North Shore Birkenhead (slips)": (174.73, -36.80), "Pukekohe market gardens": (174.90, -37.20), "Woodhill forest": (174.45, -36.72),
         "Riverhead/Kumeu": (174.57, -36.75), "Clevedon": (175.03, -36.99)}
rr_, cc_ = np.indices(shape, sparse=True)
for name, (lo, la) in spots.items():
    x, y = to_xy.transform(lo, la)
    c0, r0 = (~tf) * (x, y)
    m = (rr_ - r0) ** 2 + (cc_ - c0) ** 2 <= (5000 / 20) ** 2
    v = valid[m].sum(); b = bare[m].sum(); land = (~sea)[m].sum()
    print(f"   {name:<32} land {land * 4e-4:6.0f} km2  valid share {v / max(1, 4 * land):.2f}  newly bare {100 * b / max(1, v):.3f}% of valid")

print("\n== 6. exposure vs data quality ==")
m = ex.merge(sites, on="site_id")
print("Spearman E_route_5 vs valid_share_route_5:", round(m.E_route_5.corr(m.valid_share_route_5, method="spearman"), 3))
print("valid share by tercile:", m.groupby("tercile").valid_share_route_5.median().round(2).to_dict())
print("contour-filled share (any site > 0?):", float(m[[c for c in m.columns if c.startswith("contour_filled")]].max().max()))
sl = pd.read_csv(T / "exposure_slips.csv").merge(ex[["site_id", "tercile"]], on="site_id")
print("tercile agreement primary vs slip exposure:")
print(pd.crosstab(sl.tercile, sl.tercile_slip))
