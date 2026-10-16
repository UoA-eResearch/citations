#!/usr/bin/env python
"""Confirmation pass: (b) outside-EEZ skipjack catch by longitude band, per year, to test the author's
reconciliation of the 180-200E rise; (c) the 1-degree vs 5-degree (FIRMS GTA) comparison by longitude band and
by flag, to see whether the shortfall is suppression or domestic fleets reported only at 5 degrees."""
import json
from pathlib import Path
import numpy as np, pandas as pd, xarray as xr, geopandas as gpd
from shapely.geometry import box
from shapely.ops import unary_union
from shapely.prepared import prep

RUN = Path('/mnt/citations/research-lab/runs/blue-pacific-tuna-redistribution-detectability')
OUT = RUN / 'review/reviewer_checks'
SCH = ['una', 'log', 'dfad', 'afad', 'oth']
res = {}
ds = xr.open_dataset(RUN / 'data/raw/WCPFC_S_PUBLIC_BY_1x1_MM.nc').sel(time=slice('1980-01-01', '2021-12-31'), latitude=slice(-20, 19), longitude=slice(120, 227))
skj = sum(ds[f'skj_c_{s}'].fillna(0) for s in SCH).groupby('time.year').sum('time').load()
years = skj.year.values; C = skj.values
lat_c = ds.latitude.values + 0.5; lon_c = ds.longitude.values + 0.5
g = gpd.read_file(RUN / 'data/raw/eez/sids10_eez.geojson'); g12 = g[g.pol_type == '200NM']
shape = unary_union(list(g12.geometry)); ps = prep(shape)
def boxes180(lo, la, r):
    x0, x1, y0, y1 = lo - r / 2, lo + r / 2, la - r / 2, la + r / 2
    if x1 <= 180: return [box(x0, y0, x1, y1)]
    if x0 >= 180: return [box(x0 - 360, y0, x1 - 360, y1)]
    return [box(x0, y0, 180, y1), box(-180, y0, x1 - 360, y1)]
frac = np.zeros((lat_c.size, lon_c.size))
for i, la in enumerate(lat_c):
    for j, lo in enumerate(lon_c):
        parts = boxes180(lo, la, 1.0); frac[i, j] = sum(shape.intersection(p).area for p in parts if ps.intersects(p)) / sum(p.area for p in parts)

print('================ (b) outside-EEZ skipjack catch by longitude band, kt/yr ================')
bands = [(120, 140), (140, 160), (160, 180), (180, 200), (200, 228)]
out = (C * (1 - frac)[None])
tab = pd.DataFrame({f'{a}-{b}E': out[:, :, (lon_c >= a) & (lon_c < b)].sum((1, 2)) / 1e3 for a, b in bands}, index=years)
tab['inside EEZs'] = (C * frac[None]).sum((1, 2)) / 1e3
print(tab.loc[2000:2021].round(1).to_string())
for a, b in [(2000, 2009), (2010, 2019), (2005, 2009), (2010, 2014), (2015, 2019), (2010, 2013), (2017, 2021)]:
    print(f'mean {a}-{b}: ' + '  '.join(f'{c} {tab.loc[a:b, c].mean():.1f}' for c in tab.columns))
res['bands_by_year'] = tab.loc[2000:2021].round(2).to_dict()
# ENSO years in the 180-200E band
idx = pd.read_csv(RUN / 'results/tables/indices.csv', index_col=0)
print('\n180-200E outside-EEZ catch vs Nino3.4, 2010-2021:')
for y in range(2010, 2022): print(f'  {y}: {tab.loc[y, "180-200E"]:6.1f} kt   nino34 {idx.loc[y, "nino34"]:+.2f}   wpe {idx.loc[y, "wpe"]:.0f}E')
r = np.corrcoef(tab.loc[1990:2021, '180-200E'], idx.loc[1990:2021, 'nino34'])[0, 1]
print(f'corr(180-200E outside-EEZ catch, nino34) 1990-2021: {r:+.2f}')

print('\n================ (c) 1-degree vs 5-degree (GTA) by longitude band ================')
gta = pd.read_parquet(RUN / 'data/raw/gta/gta_public.parquet')
sk = gta[(gta.source_authority == 'WCPFC') & (gta.species == 'SKJ') & (gta.gear_type == '01.1') & (gta.measurement == 'catch') & (gta.measurement_unit == 't') & (gta.year.between(1980, 2021))].copy()
def cwp5(code):
    s = str(code)
    if len(s) != 7 or s[0] != '6': return (np.nan, np.nan)
    q, la, lo = int(s[1]), int(s[2:4]), int(s[4:7])
    lat = la + 2.5 if q in (1, 4) else -(la + 2.5)
    lon = lo + 2.5 if q in (1, 2) else -(lo + 2.5)
    return (lat, lon % 360)
cc = pd.DataFrame({'code': sk.geographic_identifier.unique()})
cc[['lat5', 'lon5']] = cc.code.apply(lambda c: pd.Series(cwp5(c)))
sk = sk.merge(cc, left_on='geographic_identifier', right_on='code')
sk = sk[(sk.lat5 >= -20) & (sk.lat5 <= 20) & (sk.lon5 >= 120) & (sk.lon5 <= 228)]
print('5-degree cells in domain:', sk[['lat5', 'lon5']].drop_duplicates().shape[0], '; lon5 range', sk.lon5.min(), sk.lon5.max(), '; lat5 values', sorted(sk.lat5.unique()))
# catch-weighted centroid sanity check of the parsing
print('GTA catch-weighted mean lon %.1fE, lat %.1f' % (np.average(sk.lon5, weights=sk.measurement_value), np.average(sk.lat5, weights=sk.measurement_value)))
# aggregate the 1-degree file to 5-degree cells
lat5_1 = (np.floor(lat_c / 5) * 5 + 2.5); lon5_1 = (np.floor(lon_c / 5) * 5 + 2.5)
one = pd.DataFrame({'year': np.repeat(years, lat_c.size * lon_c.size),
                    'lat5': np.tile(np.repeat(lat5_1, lon_c.size), years.size), 'lon5': np.tile(np.tile(lon5_1, lat_c.size), years.size),
                    'kt': C.ravel() / 1e3}).groupby(['year', 'lat5', 'lon5']).kt.sum().reset_index()
five = sk.groupby(['year', 'lat5', 'lon5']).measurement_value.sum().div(1e3).rename('kt5').reset_index()
m = one.merge(five, how='outer', on=['year', 'lat5', 'lon5']).fillna(0)
m['decade'] = (m.year // 10) * 10
def band(lo): return '120-130E' if lo < 130 else ('130-160E' if lo < 160 else ('160-200E' if lo < 200 else '200-230E'))
m['band'] = m.lon5.apply(band)
piv = m.groupby(['decade', 'band'])[['kt', 'kt5']].sum()
piv['ratio_1deg_over_5deg'] = piv.kt / piv.kt5
print('\n1-degree vs 5-degree totals by decade and band (kt over the decade):'); print(piv.round(2).to_string())
tot = m.groupby('decade')[['kt', 'kt5']].sum(); tot['ratio'] = tot.kt / tot.kt5
tot2 = m[m.band != '120-130E'].groupby('decade')[['kt', 'kt5']].sum(); tot2['ratio'] = tot2.kt / tot2.kt5
print('\nwhole domain ratio by decade:', tot.ratio.round(3).to_dict()); print('excluding 120-130E:', tot2.ratio.round(3).to_dict())
res['ratio_by_decade_all'] = tot.ratio.to_dict(); res['ratio_by_decade_excl_120_130'] = tot2.ratio.to_dict()
# share of the shortfall sitting in 120-130E
short = (m.kt5 - m.kt).groupby([m.decade, m.band]).sum().unstack()
print('\nshortfall (5deg - 1deg, kt per decade) by band:'); print(short.round(0).to_string())
# which flags fish 120-130E in the GTA?
fl = [c for c in sk.columns if 'fleet' in c or 'flag' in c]
if fl:
    f = fl[0]
    west = sk[sk.lon5 < 130].groupby(f).measurement_value.sum().sort_values(ascending=False) / 1e3
    print(f'\nGTA SKJ PS catch at 120-130E by {f} (kt, 1980-2021):'); print(west.head(8).round(0).to_string())
    east = sk[sk.lon5 >= 130].groupby(f).measurement_value.sum().sort_values(ascending=False) / 1e3
    print(f'\nGTA SKJ PS catch at 130-228E by {f} (kt, 1980-2021):'); print(east.head(10).round(0).to_string())
# does the GTA also carry WCPFC 1-degree records? compare them with the raw 1-degree file
codes = gta[(gta.source_authority == 'WCPFC') & (gta.species == 'SKJ') & (gta.gear_type == '01.1') & (gta.measurement == 'catch')].geographic_identifier.astype(str)
print('\nWCPFC SKJ PS code first digits in GTA:', codes.str[0].value_counts().to_dict())
json.dump(res, open(OUT / 'check_confirm.json', 'w'), indent=1, default=float)
