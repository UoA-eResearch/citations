"""Confirmation pass, part 2: are the 12 excluded series cumulative counters or incremental series with faults? Post-screen
water-year totals; per-gauge exceedance diff old vs new; which included gauges the window rule touched; report counts."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
RUN = Path("/mnt/citations/research-lab/runs/auckland-nz-hirds-out-of-sample-exceedance-audit")
T = RUN / "results" / "tables"
sys.path.insert(0, str(RUN / "code"))
import analyse as A, maxima as MX
sc = pd.read_csv(T / "screen_counts.csv"); faulty = sorted(sc.file[sc.gauge_fault == 1])
rows = []
for f in faulty:
    t, v, q = MX.load(MX.S / f"{f}.npz"); s, e, val, qq = t[:-1], t[1:], v[1:], q[1:]; L = e - s; ey = MX.wy_of(e)
    fin = np.isfinite(val)
    screen = MX.physical_bad(e, L, val) | MX.bad_quality(qq, "primary") | ~fin
    raw_tot = pd.Series(np.where(fin, val, 0)).groupby(ey).sum(); post_tot = pd.Series(np.where(screen, 0.0, val)).groupby(ey).sum()
    nz = val[fin & (val > 0)]
    up = float(np.mean(nz[1:] >= nz[:-1])) if len(nz) > 10 else np.nan     # counters climb between consecutive non-zero records
    big = fin & (val > 50)
    rows.append((f.split("__", 1)[1][:38], int(big.sum()), round(float(np.median(L[big])), 0) if big.any() else np.nan, round(up, 2),
                 int(raw_tot.max()), int(post_tot.max()), int(np.median(post_tot[post_tot.index >= 2005])), int((post_tot > 12000).sum()), int(screen.sum() - (~fin).sum() - MX.bad_quality(qq, "primary").sum())))
F = pd.DataFrame(rows, columns=["gauge", "records>50mm", "their_median_L_min", "share_rising_between_nonzero", "raw_max_wy_total", "post_screen_max_wy_total", "post_screen_median_wy_total_2005+", "wy_over_12000_post_screen", "records_physically_screened"])
pd.set_option("display.width", 250); print(F.to_string(index=False))

print("\n== per-gauge exceedance diff, review-time (v1_before_screen = 1416f02 set) vs now")
old = pd.read_csv(T / "v1_before_screen" / "gauges.csv").set_index("file")[["years", "exceed"]]
new = pd.read_csv(T / "gauges.csv").set_index("file")[["years", "exceed"]]
j = old.join(new, lsuffix="_old", rsuffix="_new", how="outer")
chg = j[(j.exceed_old != j.exceed_new) | (j.years_old != j.years_new)]
print(chg.to_string())
print("\n== included gauges touched by the record screens (D6+D7), from screen_counts.csv")
inc = set(new.index)
touched = sc[sc.file.isin(inc) & (sc.screened > 0)].sort_values("screened", ascending=False)
print(touched[["file", "records", "screened", "negatives", "max_wy_total"]].to_string(index=False))

print("\n== report counts")
M, H, S = A.load(); M = M[~M.file.isin(faulty)]
g = A.gauge_meta(H, S); m6 = A.qualify(M, 6, "primary"); g, dup = A.dedupe(g, m6[m6.ok].groupby("file").size())
dep = A.depth_of(H, 6, 0.1); yrs = list(range(2017, 2026)); inc6 = A.included(m6, g) & set(dep.file)
x = A.oe_table(A.oos_rows(m6, g), dep, yrs, inc6)
ex = x[x.exceed].copy(); ex["t"] = pd.to_datetime(ex.t_max, unit="m"); ex["server"] = ex.file.str.split("__").str[0]
feb = ex[(ex.t >= "2023-02-01") & (ex.t < "2023-03-01")]
exs = ex.sort_values("t_max"); storm = np.r_[0, np.cumsum(np.diff(exs.t_max.to_numpy()) > 72 * 60)]; sizes = pd.Series(storm).value_counts()
print("Feb 2023:", len(feb), "HB:", int(feb.server.eq("HawkesBay").sum()), "| storms:", len(sizes), "largest:", int(sizes.max()), "HB in largest:", int(exs[storm == sizes.idxmax()].server.eq("HawkesBay").sum()))
m24 = A.qualify(M, 24, "primary"); d24 = A.depth_of(H, 24, 0.1); x24 = A.oe_table(A.oos_rows(m24, g), d24, yrs, set(g.file))
mm = x[["file", "wy", "exceed"]].merge(x24[["file", "wy", "exceed"]], on=["file", "wy"], how="left", suffixes=("6", "24"))
print("6-h exceedances also 24-h exceedances:", int((mm.exceed6 & (mm.exceed24 == True)).sum()), "of", int(mm.exceed6.sum()))
# Lake Tutira NEW Buoy: its three old exceedance years and whether the screens touch those windows
f = "HawkesBay__Lake_Tutira_NEW_Buoy"
Mall = pd.read_parquet(RUN / "data" / "maxima.parquet"); mt = Mall[(Mall.file == f) & (Mall.d == 6) & (Mall.variant == "primary") & (Mall.wy >= 2017)]
dpt = dep.set_index("file").mm.get(f, np.nan)
print(f"\n== {f}: depth {dpt:.1f}; 6-h maxima by year (current maxima.parquet, screens applied):", mt.set_index("wy").max_point.round(1).to_dict())
t, v, q = MX.load(MX.S / f"{f}.npz"); s, e, val, qq = t[:-1], t[1:], v[1:], q[1:]; L = e - s
pb = MX.physical_bad(e, L, val); print("   physically screened records by water year:", pd.Series(pb).groupby(MX.wy_of(e)).sum().loc[lambda z: z > 0].to_dict())
for r in mt[mt.max_point > dpt].itertuples():
    w = (e > r.t_max - 360) & (e <= r.t_max) & ~pb
    print(f"   {r.wy}: max {r.max_point:.1f} ending {pd.Timestamp(int(r.t_max), unit='m')}; records in window {int(w.sum())}, largest {val[w].max():.1f} mm in {L[w][np.argmax(val[w])]:.0f} min, distinct values {len(np.unique(val[w]))}")
