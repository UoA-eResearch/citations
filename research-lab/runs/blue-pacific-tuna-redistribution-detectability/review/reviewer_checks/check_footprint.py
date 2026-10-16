#!/usr/bin/env python
"""Reviewer check (item 9): the fixed-footprint centroid. (a) Re-run across footprint thresholds and coverage
rules; (b) footprints defined on post-development windows; (c) the structural question: would SEAPODYM's own
projected eastward shift show up as a centroid trend inside each footprint at all?"""
import json
from pathlib import Path
import numpy as np, pandas as pd, xarray as xr, geopandas as gpd, statsmodels.api as sm
from shapely.geometry import box
from shapely.ops import unary_union
from shapely.prepared import prep

RUN = Path('/mnt/citations/research-lab/runs/blue-pacific-tuna-redistribution-detectability')
OUT = RUN / 'review/reviewer_checks'; SEA = RUN / 'data/raw/seapodym'
R = 6371.0088; SCH = ['una', 'log', 'dfad', 'afad', 'oth']; MIN_DAYS = 5
idx = pd.read_csv(RUN / 'results/tables/indices.csv', index_col=0)
res = {}

ds = xr.open_dataset(RUN / 'data/raw/WCPFC_S_PUBLIC_BY_1x1_MM.nc').sel(time=slice('1980-01-01', '2021-12-31'), latitude=slice(-20, 19), longitude=slice(120, 227))
skj = sum(ds[f'skj_c_{s}'].fillna(0) for s in SCH).groupby('time.year').sum('time').load()
days = ds['days'].fillna(0).groupby('time.year').sum('time').load()
years = skj.year.values; C = skj.values; D = days.values
lat_c = ds.latitude.values + 0.5; lon_c = ds.longitude.values + 0.5
area = (R ** 2 * np.radians(1.0) * (np.sin(np.radians(lat_c + 0.5)) - np.sin(np.radians(lat_c - 0.5))))[:, None] * np.ones((1, lon_c.size))
LON = np.broadcast_to(lon_c[None, :], area.shape)
g = gpd.read_file(RUN / 'data/raw/eez/sids10_eez.geojson'); g12 = g[g.pol_type == '200NM']
shape = unary_union(list(g12.geometry)); ps = prep(shape)
def boxes180(lo, la, r):
    x0, x1, y0, y1 = lo - r / 2, lo + r / 2, la - r / 2, la + r / 2
    if x1 <= 180: return [box(x0, y0, x1, y1)]
    if x0 >= 180: return [box(x0 - 360, y0, x1 - 360, y1)]
    return [box(x0, y0, 180, y1), box(-180, y0, x1 - 360, y1)]
frac = np.zeros(area.shape)
for i, la in enumerate(lat_c):
    for j, lo in enumerate(lon_c):
        parts = boxes180(lo, la, 1.0); frac[i, j] = sum(shape.intersection(p).area for p in parts if ps.intersects(p)) / sum(p.area for p in parts)

cpue = np.where(D >= MIN_DAYS, C / np.where(D > 0, D, 1), np.nan)      # nan = too little effort that year
fished = D >= MIN_DAYS


def enso_trend(yv, yy, nboot=3000, seed=5):
    X = np.column_stack([np.ones(len(yy)), yy - 2000, idx.loc[yy, 'nino34'], idx.loc[yy, 'nino34_lag'], idx.loc[yy, 'wpe']])
    f = sm.OLS(yv, X).fit(); h = sm.OLS(yv, X).fit(cov_type='HAC', cov_kwds={'maxlags': 3}); ci = h.conf_int()[1]
    n = len(yv); P = np.linalg.pinv(X); rng = np.random.default_rng(seed)
    starts = rng.integers(0, n, (nboot, int(np.ceil(n / 4)))); ii = ((starts[:, :, None] + np.arange(4)) % n).reshape(nboot, -1)[:, :n]
    B = (f.fittedvalues[None, :] + f.resid[ii]) @ P.T; lo, hi = np.percentile(B[:, 1], [2.5, 97.5])
    return dict(point=float(f.params[1]), boot=[float(lo), float(hi)], hac=[float(ci[0]), float(ci[1])], n=int(n))


def fmt(t): return f"{t['point']:+.3f} boot({t['boot'][0]:+.3f},{t['boot'][1]:+.3f}) hac({t['hac'][0]:+.3f},{t['hac'][1]:+.3f}) n={t['n']}"


def centroid_on(foot):
    w = area[None] * cpue * foot[None]                                  # nan where unfished that year
    cen = np.nansum(w * LON[None], axis=(1, 2)) / np.nansum(w, axis=(1, 2))
    dens = np.nansum(w * frac[None], axis=(1, 2)) / np.nansum(w, axis=(1, 2))
    cover = np.mean(np.isfinite(cpue[:, foot]), axis=1)
    return cen, dens, cover


print('================ (a) thresholds x coverage rules, footprint defined on all 42 years ================')
freq = fished.mean(0)
res['grid'] = {}
for fmin in (0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
    foot = freq >= fmin
    cen, dens, cover = centroid_on(foot)
    lon_f = lon_c[foot.any(0)]
    eez_share = float((area * frac * foot).sum() / (area * foot).sum())
    print(f'\nfootprint >= {fmin:.1f} of years: {foot.sum()} cells, lon {lon_f.min():.1f}-{lon_f.max():.1f}E, {100*eez_share:.1f}% EEZ, mean coverage {cover.mean():.2f}')
    row = dict(n_cells=int(foot.sum()), lon=[float(lon_f.min()), float(lon_f.max())], eez_share=eez_share)
    for cmin in (0.0, 0.6, 0.7, 0.8, 0.9):
        sel = cover >= cmin
        if sel.sum() < 12: print(f'   coverage>={cmin}: only {sel.sum()} years'); continue
        t = enso_trend(cen[sel], years[sel]); d = enso_trend(100 * dens[sel], years[sel])
        print(f'   coverage>={cmin:.1f}: years {years[sel].min()}-{years[sel].max()} ({sel.sum()}): centroid {fmt(t)} deg/yr | EEZ density share {d["point"]:+.3f} pp/yr ({d["boot"][0]:+.3f},{d["boot"][1]:+.3f})')
        row[f'cov{cmin}'] = dict(centroid=t, density_share_pp=d, years=[int(years[sel].min()), int(years[sel].max())])
    res['grid'][str(fmin)] = row

print('\n================ (b) footprints defined on later windows ================')
res['windows'] = {}
for y0 in (1988, 1990, 1995, 2000):
    sel_w = years >= y0
    for fmin in (0.8, 0.9):
        foot = fished[sel_w].mean(0) >= fmin
        cen, dens, cover = centroid_on(foot)
        lon_f = lon_c[foot.any(0)]
        for cmin in (0.0, 0.8):
            sel = sel_w & (cover >= cmin)
            t = enso_trend(cen[sel], years[sel]); d = enso_trend(100 * dens[sel], years[sel])
            print(f'window {y0}-2021, footprint >= {fmin:.1f}: {foot.sum()} cells {lon_f.min():.1f}-{lon_f.max():.1f}E ({100*(area*frac*foot).sum()/(area*foot).sum():.0f}% EEZ); coverage>={cmin:.1f} ({sel.sum()} yrs): centroid {fmt(t)} | density share {d["point"]:+.3f} ({d["boot"][0]:+.3f},{d["boot"][1]:+.3f})')
            res['windows'][f'{y0}_f{fmin}_c{cmin}'] = dict(n_cells=int(foot.sum()), lon=[float(lon_f.min()), float(lon_f.max())], centroid=t, density_share_pp=d)

print('\n================ (c) the all-fished-cells series restricted to post-development years ================')
cen_all, dens_all, _ = centroid_on(np.ones_like(freq, bool))
for y0, y1 in ((1980, 2021), (1990, 2021), (1980, 2010), (1990, 2010)):
    sel = (years >= y0) & (years <= y1)
    print(f'{y0}-{y1}: density centroid {fmt(enso_trend(cen_all[sel], years[sel]))} | density share {enso_trend(100*dens_all[sel], years[sel])["point"]:+.3f} pp/yr {enso_trend(100*dens_all[sel], years[sel])["boot"]}')
    res[f'allcells_{y0}_{y1}'] = dict(centroid=enso_trend(cen_all[sel], years[sel]), density_share_pp=enso_trend(100 * dens_all[sel], years[sel]))

print('\n================ (d) would SEAPODYM\'s projected shift be visible inside each footprint? ================')
def load(fn):
    d_ = xr.open_dataset(SEA / fn, decode_times=False); v = list(d_.data_vars)[0]; u = d_.time.attrs['units']
    t = pd.DatetimeIndex([pd.Timestamp('1980-01-15') + pd.DateOffset(months=int(x)) for x in d_.time.values]) if u.startswith('months') else pd.Timestamp('2011-01-15') + pd.to_timedelta(d_.time.values, unit='D')
    return d_[v].assign_coords(time=t)
runs = {e: load(f'skj_Btot_{e}_F0.nc') for e in ('GFDL', 'IPSL', 'MIROC', 'MPI')}; runs['hist'] = load('skj_Btot_hist_F0.nc')
lat2, lon2 = runs['hist'].lat.values, runs['hist'].lon.values
area2 = (R ** 2 * np.radians(2.0) * (np.sin(np.radians(lat2 + 1)) - np.sin(np.radians(lat2 - 1))))[:, None] * np.ones((1, lon2.size))
dom2 = (((lat2 >= -20) & (lat2 <= 20))[:, None] & ((lon2 >= 120) & (lon2 <= 228))[None, :]).astype(float)
LON2 = np.broadcast_to(lon2[None, :], area2.shape)


def to2deg(foot1):
    """fraction of each 2-degree cell covered by footprint 1-degree cells"""
    W = np.zeros(area2.shape)
    for i, la in enumerate(lat_c):
        for j, lo in enumerate(lon_c):
            if foot1[i, j]:
                i2 = int(np.argmin(np.abs(lat2 - la))); j2 = int(np.argmin(np.abs(lon2 - lo)))
                W[i2, j2] += 0.25
    return W


def model_centroid(da, W):
    b = da.fillna(0).values * (area2 * W)[None]
    c = (b * LON2[None]).sum((1, 2)) / b.sum((1, 2))
    return pd.Series(c, index=da.time.values).groupby(pd.Series(c, index=da.time.values).index.year).mean()


slope = lambda s, a, b: float(np.polyfit(s.loc[a:b].index.values, s.loc[a:b].values, 1)[0])
res['model_in_footprint'] = {}
foots = {'domain': dom2.astype(bool)}
for fmin in (0.8, 0.5):
    foots[f'footprint_{fmin}'] = freq >= fmin
for name, fp in foots.items():
    W = dom2 if name == 'domain' else to2deg(fp)
    out = {}
    cen_m = {e: model_centroid(runs[e], W) for e in runs}
    mean_proj = pd.concat([cen_m[e] for e in ('GFDL', 'IPSL', 'MIROC', 'MPI')], axis=1).mean(axis=1)
    out['proj_2011_2050_mean_of_esm_slopes'] = float(np.mean([slope(cen_m[e], 2011, 2050) for e in ('GFDL', 'IPSL', 'MIROC', 'MPI')]))
    out['proj_2011_2050_slope_of_mean_path'] = slope(mean_proj, 2011, 2050)
    out['proj_per_esm'] = {e: slope(cen_m[e], 2011, 2050) for e in ('GFDL', 'IPSL', 'MIROC', 'MPI')}
    out['hist_1980_2010_raw'] = slope(cen_m['hist'], 1980, 2010)
    out['hist_1980_2010_enso'] = enso_trend(cen_m['hist'].loc[1980:2010].values, np.arange(1980, 2011))
    out['proj_2011_2099_slope_of_mean_path'] = slope(mean_proj, 2011, 2099)
    out['mean_lon_2011_2020'] = float(mean_proj.loc[2011:2020].mean())
    out['delta_lon_2044_53_minus_2011_20'] = float(mean_proj.loc[2044:2053].mean() - mean_proj.loc[2011:2020].mean())
    print(f"{name:14s}: model centroid 2011-20 {out['mean_lon_2011_2020']:.2f}E; projected 2011-2050 trend {out['proj_2011_2050_slope_of_mean_path']:+.4f} deg/yr (per ESM {dict((k, round(v,4)) for k,v in out['proj_per_esm'].items())}); 2044-53 minus 2011-20 = {out['delta_lon_2044_53_minus_2011_20']:+.2f} deg; 2011-2099 {out['proj_2011_2099_slope_of_mean_path']:+.4f}; hist 1980-2010 raw {out['hist_1980_2010_raw']:+.4f}, ENSO-adj {fmt(out['hist_1980_2010_enso'])}")
    res['model_in_footprint'][name] = out
# the observed footprint centroid over 1980-2010 and 1988-2010, to set against the model's hist in-footprint trend
foot8 = freq >= 0.8; cen8, _, cov8 = centroid_on(foot8)
for a, b in ((1980, 2010), (1988, 2010), (1988, 2021)):
    sel = (years >= a) & (years <= b) & (cov8 >= 0.8)
    print(f'observed density centroid on the 0.8 footprint, {a}-{b}, coverage>=0.8 ({sel.sum()} yrs): {fmt(enso_trend(cen8[sel], years[sel]))}')
    res[f'obs_foot08_{a}_{b}'] = enso_trend(cen8[sel], years[sel])
json.dump(res, open(OUT / 'check_footprint.json', 'w'), indent=1, default=float)
