#!/usr/bin/env python
"""Reviewer check (item 4): recompute O1 (and O2 for a few years) straight from the raw WCPFC file with an
independent EEZ mask built in -180..180 space. Also the means around 2010 and the largest year-to-year swings."""
import json
from pathlib import Path
import numpy as np, pandas as pd, xarray as xr, geopandas as gpd
from shapely.geometry import box
from shapely.ops import unary_union
from shapely.prepared import prep

RUN = Path('/mnt/citations/research-lab/runs/blue-pacific-tuna-redistribution-detectability')
OUT = RUN / 'review/reviewer_checks'
R = 6371.0088
SCH = ['una', 'log', 'dfad', 'afad', 'oth']
res = {}

ds = xr.open_dataset(RUN / 'data/raw/WCPFC_S_PUBLIC_BY_1x1_MM.nc')
print('full file: lat', float(ds.latitude.min()), float(ds.latitude.max()), 'lon', float(ds.longitude.min()), float(ds.longitude.max()), 'time', str(ds.time.values[0])[:10], str(ds.time.values[-1])[:10])
# Domain under the SW-corner convention: integer lat -20..19 (cells span -20..20), lon 120..227 (cells span 120..228)
sub = ds.sel(time=slice('1980-01-01', '2021-12-31'), latitude=slice(-20, 19), longitude=slice(120, 227))
print('subset months:', sub.sizes['time'], 'lat cells', sub.sizes['latitude'], 'lon cells', sub.sizes['longitude'])
skj_m = sum(sub[f'skj_c_{s}'] for s in SCH)                     # NaN where all five are NaN
nan_pattern_same = bool(((sub['skj_c_una'].isnull() == sub['days'].isnull()).all()))
print('missing pattern identical between skj_c_una and days:', nan_pattern_same)
skj = skj_m.fillna(0).groupby('time.year').sum('time').load()
days = sub['days'].fillna(0).groupby('time.year').sum('time').load()
sets_una = sub['sets_una'].fillna(0).groupby('time.year').sum('time').load()
skj_una = sub['skj_c_una'].fillna(0).groupby('time.year').sum('time').load()
years = skj.year.values
lat_c = sub.latitude.values + 0.5; lon_c = sub.longitude.values + 0.5

g = gpd.read_file(RUN / 'data/raw/eez/sids10_eez.geojson')
g12 = g[g.pol_type == '200NM']; assert len(g12) == 12
shape = unary_union(list(g12.geometry)); ps = prep(shape)


def boxes180(lo_c, la_c, r):
    x0, x1, y0, y1 = lo_c - r / 2, lo_c + r / 2, la_c - r / 2, la_c + r / 2
    if x1 <= 180: return [box(x0, y0, x1, y1)]
    if x0 >= 180: return [box(x0 - 360, y0, x1 - 360, y1)]
    return [box(x0, y0, 180, y1), box(-180, y0, x1 - 360, y1)]


frac = np.zeros((lat_c.size, lon_c.size))
for i, la in enumerate(lat_c):
    for j, lo in enumerate(lon_c):
        parts = boxes180(lo, la, 1.0)
        frac[i, j] = sum(shape.intersection(p).area for p in parts if ps.intersects(p)) / sum(p.area for p in parts)
area = (R ** 2 * np.radians(1.0) * (np.sin(np.radians(lat_c + 0.5)) - np.sin(np.radians(lat_c - 0.5))))[:, None] * np.ones((1, lon_c.size))
print('1-deg mask: EEZ area inside domain %.0f km2; cells with 0<frac<1: %d; frac==1: %d' % ((frac * area).sum(), ((frac > 0) & (frac < 1)).sum(), (frac == 1).sum()))

C = skj.values; D = days.values
o1 = (C * frac[None]).sum((1, 2)) / C.sum((1, 2))
cpue = np.where(D >= 5, C / np.where(D > 0, D, 1), 0.0)
o2 = (area[None] * frac[None] * cpue).sum((1, 2)) / (area[None] * cpue).sum((1, 2))
S = sets_una.values; CU = skj_una.values
cpue_u = np.where(S >= 5, CU / np.where(S > 0, S, 1), 0.0)
o2u = (area[None] * frac[None] * cpue_u).sum((1, 2)) / (area[None] * cpue_u).sum((1, 2))
dshare = (D * frac[None]).sum((1, 2)) / D.sum((1, 2))
obs = pd.read_csv(RUN / 'results/tables/observed_annual.csv', index_col=0)
obs = obs[obs.convention == 'sw'].loc[1980:2021]
mine = pd.DataFrame({'o1': o1, 'o2': o2, 'o2u': o2u, 'days_share': dshare, 'dom_catch_t': C.sum((1, 2)), 'eez_catch_t': (C * frac[None]).sum((1, 2))}, index=years)
cmp = pd.DataFrame({'O1_mine': mine.o1, 'O1_study': obs.skj_catch_share, 'O2_mine': mine.o2, 'O2_study': obs.skj_density_share,
                    'O2u_mine': mine.o2u, 'O2u_study': obs.skj_density_share_una, 'days_mine': mine.days_share, 'days_study': obs.days_eez_share,
                    'domcatch_mine': mine.dom_catch_t, 'domcatch_study': obs.skj_catch_dom_t})
print('\nmax |mine - study|: O1 %.2e  O2 %.2e  O2u %.2e  days %.2e  domain catch (t) %.3f' % (
    (cmp.O1_mine - cmp.O1_study).abs().max(), (cmp.O2_mine - cmp.O2_study).abs().max(), (cmp.O2u_mine - cmp.O2u_study).abs().max(),
    (cmp.days_mine - cmp.days_study).abs().max(), (cmp.domcatch_mine - cmp.domcatch_study).abs().max()))
print('\nHand recomputation of O1 for five years (sw convention):')
for y in [1985, 1995, 2005, 2010, 2015, 2021]:
    r = mine.loc[y]
    print(f'  {y}: EEZ skj catch {r.eez_catch_t:,.1f} t / domain skj catch {r.dom_catch_t:,.1f} t = {r.o1:.4f}   (study {obs.loc[y, "skj_catch_share"]:.4f})')
res['max_abs_diff'] = dict(O1=float((cmp.O1_mine - cmp.O1_study).abs().max()), O2=float((cmp.O2_mine - cmp.O2_study).abs().max()),
                           O2u=float((cmp.O2u_mine - cmp.O2u_study).abs().max()), days=float((cmp.days_mine - cmp.days_study).abs().max()))
res['hand_O1'] = {int(y): dict(eez_t=float(mine.loc[y].eez_catch_t), dom_t=float(mine.loc[y].dom_catch_t), O1=float(mine.loc[y].o1)) for y in [1985, 1995, 2005, 2010, 2015, 2021]}

# cross-check the catch total against a different accounting: total of the 5 set types vs 'una' alone
print('\nshare of domain skj catch by set type, 1980-89 / 2010-21:')
for s in SCH:
    v = sub[f'skj_c_{s}'].fillna(0).groupby('time.year').sum('time').sum(('latitude', 'longitude')).to_series()
    print(f'  {s:5s} {v.loc[1980:1989].sum()/mine.dom_catch_t.loc[1980:1989].sum():.3f}  {v.loc[2010:2021].sum()/mine.dom_catch_t.loc[2010:2021].sum():.3f}')

# means around 2010 and swings
for col, lab in [('skj_catch_share', 'catch share'), ('skj_density_share', 'density share'), ('days_eez_share', 'days share'), ('skj_density_share_una', 'free-school density share')]:
    a, b = 100 * obs.loc[1980:2009, col].mean(), 100 * obs.loc[2010:2021, col].mean()
    print(f'{lab:28s} mean 1980-2009 {a:.1f}%  2010-2021 {b:.1f}%  (2000-2009 {100*obs.loc[2000:2009, col].mean():.1f}%)')
    res[f'mean_{col}'] = dict(pre=a, post=b)
d = (100 * obs.skj_catch_share).diff().abs()
print('largest year-to-year changes in catch share (pp):', d.sort_values(ascending=False).head(5).round(1).to_dict())
print('fished cells per year (>=5 days):', {int(y): int(v) for y, v in zip(years, (D >= 5).sum((1, 2)))})
res['max_swing_pp'] = float(d.max())
# how much of the pre-2010 vs post-2010 catch-share jump is "pocket" cells (outside EEZ) losing catch
out_eez = (C * (1 - frac)[None]).sum((1, 2))
print('\nskj catch outside the EEZs but inside the domain (kt): 2005-09 mean %.0f, 2010-14 mean %.0f; inside EEZs: %.0f -> %.0f' % (
    out_eez[(years >= 2005) & (years <= 2009)].mean() / 1e3, out_eez[(years >= 2010) & (years <= 2014)].mean() / 1e3,
    mine.eez_catch_t.loc[2005:2009].mean() / 1e3, mine.eez_catch_t.loc[2010:2014].mean() / 1e3))
# where did the outside-EEZ catch sit? split by longitude band
for lo0, lo1 in [(120, 140), (140, 160), (160, 180), (180, 200), (200, 228)]:
    sel = (lon_c >= lo0) & (lon_c < lo1)
    pre = (C[(years >= 2005) & (years <= 2009)][:, :, sel] * (1 - frac)[None, :, sel]).sum() / 5 / 1e3
    post = (C[(years >= 2010) & (years <= 2014)][:, :, sel] * (1 - frac)[None, :, sel]).sum() / 5 / 1e3
    print(f'  outside-EEZ skj catch {lo0}-{lo1}E: 2005-09 {pre:.0f} kt/yr -> 2010-14 {post:.0f} kt/yr')
json.dump(res, open(OUT / 'check_observed.json', 'w'), indent=1, default=float)
