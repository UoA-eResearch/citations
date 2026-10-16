#!/usr/bin/env python
"""Reviewer check (items 2, 3): independent recomputation of the Bell et al. reproduction and of the
D2 SEAPODYM file anomalies. Independent code path: mask built in -180..180 space against the original
polygons (not by shifting polygons to 0..360), cells straddling the antimeridian split in two."""
import json
from pathlib import Path
import numpy as np, pandas as pd, xarray as xr, geopandas as gpd
from shapely.geometry import box
from shapely.ops import unary_union
from shapely.prepared import prep

RUN = Path('/mnt/citations/research-lab/runs/blue-pacific-tuna-redistribution-detectability')
SEA = RUN / 'data/raw/seapodym'
OUT = RUN / 'review/reviewer_checks'
R = 6371.0088
ESMS = ['GFDL', 'IPSL', 'MIROC', 'MPI']
SP = ['skj', 'yft', 'bet']
res = {}


def load(fn):
    ds = xr.open_dataset(SEA / fn, decode_times=False)
    v = list(ds.data_vars)[0]
    u = ds.time.attrs['units']
    if u.startswith('months'):
        t = pd.DatetimeIndex([pd.Timestamp('1980-01-15') + pd.DateOffset(months=int(x)) for x in ds.time.values])
    else:
        t = pd.Timestamp('2011-01-15') + pd.to_timedelta(ds.time.values, unit='D')
    return ds[v].assign_coords(time=t), v, ds.attrs.get('history', '')


def stats(a, b, name):
    a = np.asarray(a.values, float).ravel(); b = np.asarray(b.values, float).ravel()
    ok = np.isfinite(a) & np.isfinite(b) & ((a > 0) | (b > 0))
    a, b = a[ok], b[ok]
    corr = np.corrcoef(a, b)[0, 1]
    ratio = a.sum() / b.sum()
    big = b > np.percentile(b[b > 0], 50)
    cell = a[big] / b[big]
    d = dict(corr=float(corr), sum_ratio=float(ratio), cell_p1=float(np.percentile(cell, 1)),
             cell_p50=float(np.percentile(cell, 50)), cell_p99=float(np.percentile(cell, 99)),
             max_abs_diff_over_max=float(np.max(np.abs(a - b)) / b.max()))
    print(f'{name}: corr {corr:.6f} sum-ratio {ratio:.4f} cellwise ratio p1/p50/p99 {d["cell_p1"]:.3f}/{d["cell_p50"]:.3f}/{d["cell_p99"]:.3f} max|a-b|/max(b) {d["max_abs_diff_over_max"]:.2e}')
    return d


print('================ D2: file anomalies ================')
bt, vbt, hbt = load('bet_Btot_GFDL_F0.nc'); ba, _, _ = load('bet_Badult_GFDL_F0.nc'); by, _, _ = load('bet_Byoung_GFDL_F0.nc')
print('bet_Btot_GFDL variable name:', vbt, '| history:', hbt)
res['bet_GFDL_Btot_vs_adult_plus_young'] = stats(bt, ba + by, 'bet GFDL Btot vs adult+young')
res['bet_GFDL_Btot_vs_young'] = stats(bt, by, 'bet GFDL Btot vs young-file')
for esm in ['IPSL', 'MIROC', 'MPI']:
    b, v, h = load(f'bet_Btot_{esm}_F0.nc')
    r1 = float(b.sel(time=slice('2011', '2020')).sum(('lat', 'lon')).mean() / bt.sel(time=slice('2011', '2020')).sum(('lat', 'lon')).mean())
    r2 = float(b.sel(time=slice('2011', '2020')).sum(('lat', 'lon')).mean() / by.sel(time=slice('2011', '2020')).sum(('lat', 'lon')).mean())
    print(f'bet_Btot_{esm}: var {v} | history: {h} | 2011-20 global total / GFDL Btot = {r1:.3f}; / GFDL young = {r2:.3f}')
    res[f'bet_{esm}_total_ratio_to_GFDL_Btot'] = r1; res[f'bet_{esm}_total_ratio_to_GFDL_young'] = r2
bth, vh, hh = load('bet_Btot_hist_F0.nc'); bah, _, _ = load('bet_Badult_hist_F0.nc'); byh, _, _ = load('bet_Byoung_hist_F0.nc')
print('bet_Btot_hist variable', vh, '| history:', hh)
res['bet_hist_Btot_vs_adult_plus_young'] = stats(bth, bah + byh, 'bet hist Btot vs adult+young')
res['bet_hist_Btot_vs_adult'] = stats(bth, bah, 'bet hist Btot vs adult only')
a = bah.values.ravel(); y = byh.values.ravel(); t = bth.values.ravel()
ok = np.isfinite(a) & np.isfinite(y) & np.isfinite(t) & ((a + y) > 0)
X = np.column_stack([a[ok], y[ok]]); coef, *_ = np.linalg.lstsq(X, t[ok], rcond=None)
r2 = 1 - np.sum((t[ok] - X @ coef) ** 2) / np.sum((t[ok] - t[ok].mean()) ** 2)
print(f'bet hist: Btot ~ {coef[0]:.4f}*adult + {coef[1]:.4f}*young (no intercept), R2 {r2:.5f}')
res['bet_hist_fit'] = dict(adult=float(coef[0]), young=float(coef[1]), r2=float(r2))
rt = (bth.sum(('lat', 'lon')) / (bah + byh).sum(('lat', 'lon'))).groupby('time.year').mean()
print('bet hist Btot/(adult+young) by year:', np.round(rt.values, 3))
res['bet_hist_ratio_by_year'] = {int(k): float(v) for k, v in zip(rt.year.values, rt.values)}
for sp in ['skj', 'yft']:
    for run in ['hist', 'GFDL']:
        b, _, _ = load(f'{sp}_Btot_{run}_F0.nc'); a_, _, _ = load(f'{sp}_Badult_{run}_F0.nc'); y_, _, _ = load(f'{sp}_Byoung_{run}_F0.nc')
        res[f'{sp}_{run}_Btot_vs_adult_plus_young'] = stats(b, a_ + y_, f'{sp} {run} Btot vs adult+young')

print('\n================ EEZ mask, independent route ================')
g = gpd.read_file(RUN / 'data/raw/eez/sids10_eez.geojson')
g12 = g[g.pol_type == '200NM']
assert len(g12) == 12, len(g12)
print('rows used:', sorted(g12.geoname.tolist()))
print('dropped:', g[g.pol_type != '200NM'].geoname.tolist())
shape180 = unary_union(list(g12.geometry))
pshape = prep(shape180)
ref, _, _ = load('skj_Btot_hist_F0.nc')
lat, lon = ref.lat.values, ref.lon.values


def boxes180(lo_c, la_c, r):
    x0, x1, y0, y1 = lo_c - r / 2, lo_c + r / 2, la_c - r / 2, la_c + r / 2
    if x1 <= 180: return [box(x0, y0, x1, y1)]
    if x0 >= 180: return [box(x0 - 360, y0, x1 - 360, y1)]
    return [box(x0, y0, 180, y1), box(-180, y0, x1 - 360, y1)]


def frac_mask(lat, lon, r):
    f = np.zeros((lat.size, lon.size))
    miny, maxy = shape180.bounds[1], shape180.bounds[3]
    for i, la in enumerate(lat):
        if la + r / 2 < miny or la - r / 2 > maxy: continue
        for j, lo in enumerate(lon):
            parts = boxes180(lo, la, r)
            tot = sum(p.area for p in parts)
            f[i, j] = sum(shape180.intersection(p).area for p in parts if pshape.intersects(p)) / tot
    return f


frac = frac_mask(lat, lon, 2.0)
m = xr.open_dataset(RUN / 'data/processed/eez_mask_2deg.nc')
study = m.eez_frac.values
print(f'mask vs study mask: max|diff| {np.max(np.abs(frac - study)):.2e}, sum mine {frac.sum():.4f} study {study.sum():.4f}')
area = (R ** 2 * np.radians(2.0) * (np.sin(np.radians(lat + 1)) - np.sin(np.radians(lat - 1))))[:, None] * np.ones((1, lon.size))
mask_area = float((frac * area).sum()); mr = float(g12.area_km2.sum())
print(f'mask EEZ area {mask_area:,.0f} km2 vs Marine Regions {mr:,.0f} (ratio {mask_area/mr:.4f})')
res['mask'] = dict(max_abs_diff_vs_study=float(np.max(np.abs(frac - study))), area_km2=mask_area, mr_area_km2=mr)

print('\n================ Bell reproduction ================')
W = xr.DataArray(frac * area, dims=('lat', 'lon'))


def annual_eez(da): return (da.fillna(0) * W).sum(('lat', 'lon')).groupby('time.year').mean().to_series()


def total(sp, run):
    if sp == 'bet' and run == 'hist':
        return load('bet_Badult_hist_F0.nc')[0] + load('bet_Byoung_hist_F0.nc')[0]
    return load(f'{sp}_Btot_{run}_F0.nc')[0]


hist_sp = {sp: annual_eez(total(sp, 'hist')) for sp in SP}
hist = sum(hist_sp.values())
hist_asserved = sum(annual_eez(load(f'{sp}_Btot_hist_F0.nc')[0]) for sp in SP)
rows = []
for esm in ESMS:
    proj_sp = {sp: annual_eez(total(sp, esm)) for sp in SP}
    proj = sum(proj_sp.values())
    fut = proj.loc[2044:2053].mean()
    base_spl = pd.concat([hist.loc[2009:2010], proj.loc[2011:2018]]).mean()
    base_proj = proj.loc[2011:2018].mean()
    base_spl_srv = pd.concat([hist_asserved.loc[2009:2010], proj.loc[2011:2018]]).mean()
    r = dict(esm=esm, chg_spliced=fut / base_spl - 1, chg_proj_only=fut / base_proj - 1,
             chg_spliced_bet_as_served=fut / base_spl_srv - 1,
             hist2010_over_proj2011=float(hist.loc[2010] / proj.loc[2011]))
    for sp in SP:
        r[f'{sp}_chg_proj_only'] = proj_sp[sp].loc[2044:2053].mean() / proj_sp[sp].loc[2011:2018].mean() - 1
        r[f'{sp}_share_of_eez_biomass_2011_18'] = proj_sp[sp].loc[2011:2018].mean() / base_proj
    rows.append(r)
df = pd.DataFrame(rows).set_index('esm')
print(df.round(4).to_string())
print('mean spliced %.4f  mean proj-only %.4f  mean spliced(bet as served) %.4f' % (df.chg_spliced.mean(), df.chg_proj_only.mean(), df.chg_spliced_bet_as_served.mean()))
res['bell'] = df.to_dict(orient='index'); res['bell_mean_spliced'] = float(df.chg_spliced.mean()); res['bell_mean_proj_only'] = float(df.chg_proj_only.mean())

print('\n================ skipjack domain share and tau ================')
dom = ((lat >= -20) & (lat <= 20))[:, None] & ((lon >= 120) & (lon <= 228))[None, :]
Wd = xr.DataArray(dom * area, dims=('lat', 'lon')); We = xr.DataArray(frac * dom * area, dims=('lat', 'lon'))


def share(da):
    b = da.fillna(0)
    return ((b * We).sum(('lat', 'lon')).groupby('time.year').mean() / (b * Wd).sum(('lat', 'lon')).groupby('time.year').mean()).to_series()


hs = share(total('skj', 'hist'))
ps = {e: share(total('skj', e)) for e in ESMS}
pm = pd.concat(ps, axis=1).mean(axis=1)
sl = lambda s, a, b: float(np.polyfit(s.loc[a:b].index.values, s.loc[a:b].values, 1)[0])
tau = {e: 100 * sl(s, 2011, 2050) for e, s in ps.items()}
print('hist mean share 1980-2010 %.4f; raw trend %.4f pp/yr' % (hs.mean(), 100 * sl(hs, 1980, 2010)))
print('tau per ESM (pp/yr):', {k: round(v, 4) for k, v in tau.items()}, ' mean of ESM slopes %.4f; slope of mean path %.4f' % (np.mean(list(tau.values())), 100 * sl(pm, 2011, 2050)))
print('proj share 2011-2020 %.4f, 2044-2053 %.4f; 2011-2030 slope %.4f' % (pm.loc[2011:2020].mean(), pm.loc[2044:2053].mean(), 100 * sl(pm, 2011, 2030)))
mt = json.load(open(RUN / 'results/tables/model_targets.json'))
print('study: tau mean %.5f, hist trend %.5f' % (100 * mt['skipjack_share']['proj_trend_per_year_2011_2050_mean'], 100 * mt['skipjack_share']['hist_trend_per_year_1980_2010']))
res['tau_mean_pp'] = float(np.mean(list(tau.values()))); res['hist_trend_pp'] = 100 * sl(hs, 1980, 2010)
json.dump(res, open(OUT / 'check_bell_d2.json', 'w'), indent=1, default=float)
