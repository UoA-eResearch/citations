#!/usr/bin/env python
"""Bell et al. (2021) Methods eq. (1): dB(2050) = (1/N) sum_{t=2011..2020, monthly} B(t+33y)/B(t) - 1, i.e. the
mean of monthly ratios with a 2011-2020 baseline, not the ratio of decadal means with a 2009-2018 baseline (which is
what Fig. 3's caption says). Recompute the headline both ways to see which the study's -14.2% / -15.3% miss."""
import numpy as np, pandas as pd, xarray as xr
from pathlib import Path
RUN = Path('/mnt/citations/research-lab/runs/blue-pacific-tuna-redistribution-detectability'); SEA = RUN / 'data/raw/seapodym'
m = xr.open_dataset(RUN / 'data/processed/eez_mask_2deg.nc'); W = m.eez_frac * m.cell_area_km2
def load(fn):
    d = xr.open_dataset(SEA / fn, decode_times=False); v = list(d.data_vars)[0]; u = d.time.attrs['units']
    t = pd.DatetimeIndex([pd.Timestamp('1980-01-15') + pd.DateOffset(months=int(x)) for x in d.time.values]) if u.startswith('months') else pd.Timestamp('2011-01-15') + pd.to_timedelta(d.time.values, unit='D')
    return d[v].assign_coords(time=t).fillna(0)
def eez_monthly(sp, run):
    da = load('bet_Badult_hist_F0.nc') + load('bet_Byoung_hist_F0.nc') if (sp == 'bet' and run == 'hist') else load(f'{sp}_Btot_{run}_F0.nc')
    return (da * W).sum(('lat', 'lon')).to_series()
rows = []
for esm in ['GFDL', 'IPSL', 'MIROC', 'MPI']:
    tot = sum(eez_monthly(sp, esm) for sp in ['skj', 'yft', 'bet'])
    tot.index = pd.to_datetime(tot.index)
    base = tot['2011-01':'2020-12']; fut = tot['2044-01':'2053-12']
    # eq (1): month-by-month ratio, 33-year offset
    ratios = fut.values / base.values
    r = dict(esm=esm, eq1_mean_of_monthly_ratios=ratios.mean() - 1, ratio_of_means_2011_2020=fut.mean() / base.mean() - 1,
             ratio_of_means_2011_2018=fut.mean() / tot['2011-01':'2018-12'].mean() - 1)
    # per species under eq (1)
    for sp in ['skj', 'yft', 'bet']:
        s = eez_monthly(sp, esm); s.index = pd.to_datetime(s.index)
        r[f'{sp}_eq1'] = (s['2044-01':'2053-12'].values / s['2011-01':'2020-12'].values).mean() - 1
    rows.append(r)
df = pd.DataFrame(rows).set_index('esm')
print(df.round(4).to_string())
print('\nmeans: eq1 %.4f | ratio of means 2011-2020 %.4f | ratio of means 2011-2018 %.4f' % (df.eq1_mean_of_monthly_ratios.mean(), df.ratio_of_means_2011_2020.mean(), df.ratio_of_means_2011_2018.mean()))
print('range eq1: %.4f to %.4f' % (df.eq1_mean_of_monthly_ratios.min(), df.eq1_mean_of_monthly_ratios.max()))
print('published: -0.13 (range -0.20 to -0.05)')
