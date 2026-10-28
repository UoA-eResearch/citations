"""Reviewer check 6: residual implausible records after the D6 screen; what the screen touched; Auckland diagnostics
(aggregate only, no raw values); remaining report numbers; the five gauges with coordinates 'outside NZ'."""
import re, sys
from pathlib import Path
import numpy as np, pandas as pd
RUN = Path("/mnt/citations/research-lab/runs/auckland-nz-hirds-out-of-sample-exceedance-audit")
D = RUN / "data"
sys.path.insert(0, str(RUN / "code"))
import analyse as A, maxima as MX
M, H, S = A.load()
g = A.gauge_meta(H, S); m6 = A.qualify(M, 6, "primary")
g, dup = A.dedupe(g, m6[m6.ok].groupby("file").size())
dep = A.depth_of(H, 6, 0.1); yrs = list(range(2017, 2026))
inc = A.included(m6, g) & set(dep.file)
x = A.oe_table(A.oos_rows(m6, g), dep, yrs, inc)
d250 = H[(H.table == "historical") & np.isclose(H.ari, 250)].pivot_table(index="file", columns="duration_h", values="mm")

print("== maximum-window structure for the 258 exceedances (records inside the 6-h window ending at t_max)")
flags = []
screen_hits = 0; screen_files = 0
for f in sorted(inc):
    t, v, q = MX.load(MX.S / f"{f}.npz")
    s, e, val, qq = t[:-1], t[1:], v[1:], q[1:]; L = e - s
    pb = MX.physical_bad(L, val)
    oos = (e >= MX.wy_start(2017)) & (e < MX.wy_start(2026))
    if (pb & oos).any():
        screen_hits += int((pb & oos).sum()); screen_files += 1
    for r in x[(x.file == f) & x.exceed].itertuples():
        m = (e > r.t_max - 360) & (e <= r.t_max) & ~MX.bad_quality(qq, "primary") & np.isfinite(val) & ~pb
        vv, LL = val[m], L[m]
        nz = vv[vv > 0]
        # longest run of identical non-zero values inside the window
        run = 1; best = 1
        for i in range(1, len(nz)):
            run = run + 1 if nz[i] == nz[i - 1] else 1; best = max(best, run)
        flags.append((f, r.wy, round(r.max_point, 1), round(r.mm, 1), int(m.sum()), int((vv > 0).sum()), round(float(vv.max()) if len(vv) else 0, 1),
                      round(float(LL[np.argmax(vv)]) if len(vv) else 0, 1), best, round(float(np.median(nz)) if len(nz) else 0, 2)))
F = pd.DataFrame(flags, columns=["file", "wy", "max6h", "depth", "recs", "wet_recs", "largest_rec", "its_interval_min", "longest_identical_run", "median_wet_value"])
F.to_csv(RUN / "review" / "reviewer_checks" / "c6_exceedance_windows.csv", index=False)
print("D6 screen flagged", screen_hits, "out-of-sample records at", screen_files, "of 201 included gauges")
print("exceedance windows with <= 3 wet records:", int((F.wet_recs <= 3).sum()))
print("exceedance windows whose largest single record is >= 20 mm:", int((F.largest_rec >= 20).sum()))
print(F[F.largest_rec >= 20].sort_values("largest_rec", ascending=False).to_string(index=False))
print("exceedance windows with a run of >= 8 identical non-zero values:", int((F.longest_identical_run >= 8).sum()))
print(F[F.longest_identical_run >= 8].sort_values("longest_identical_run", ascending=False).head(15).to_string(index=False))
print("exceedance 6-h maxima above 1.0x / 1.5x the gauge's 250-yr 6-h depth:", int((F.max6h > F.file.map(d250[6.0])).sum()), int((F.max6h > 1.5 * F.file.map(d250[6.0])).sum()))

print("\n== secondaries: included ok gauge-years whose maxima exceed the 250-yr depth at that duration")
for d_ in (1, 6, 24):
    md = A.qualify(M, d_, "primary"); dd = A.depth_of(H, d_, 0.1); xd = A.oe_table(A.oos_rows(md, g), dd, yrs, A.included(md, g) & set(dd.file))
    xd["r250"] = xd.max_point / xd.file.map(d250[float(d_)])
    print(f"  {d_} h: gauge-years {len(xd)}, exceed {int(xd.exceed.sum())}, above 250-yr depth {int((xd.r250 > 1).sum())}, above 1.5x {int((xd.r250 > 1.5).sum())}")
    print(xd[xd.r250 > 1][["file", "wy", "max_point", "mm", "r250"]].sort_values("r250", ascending=False).head(8).round(2).to_string(index=False))

print("\n== remaining report numbers")
ex = x[x.exceed].copy(); ex["t"] = pd.to_datetime(ex.t_max, unit="m"); ex["server"] = ex.file.str.split("__").str[0]
print("Feb 2018 exceedances by council:", ex[(ex.t >= "2018-02-01") & (ex.t < "2018-03-01")].server.value_counts().to_dict())
print("2017/18 exceedances by council:", ex[ex.wy == 2017].server.value_counts().to_dict())
exs = ex.sort_values("t_max"); storm = np.r_[0, np.cumsum(np.diff(exs.t_max.to_numpy()) > 72 * 60)]; big = pd.Series(storm).value_counts().idxmax()
print("largest storm cluster by council:", exs[storm == big].server.value_counts().to_dict(), "| dates:", exs[storm == big].t.min(), "to", exs[storm == big].t.max())
print("2025/26 exceedances by council:", ex[ex.wy == 2025].server.value_counts().to_dict(), "| 2021/22:", ex[ex.wy == 2021].server.value_counts().to_dict())
# plausibility.md traces
se = A.depth_of(H, 6, 0.1, "historical_se").set_index("file").mm
for f, wy in (("HawkesBay__Maharakeke_Stream_at_Limeworks", 2022), ("Tasman__HY_Anatoki_at_Paradise", 2017), ("Wellington__Akatarawa_River_at_Cemetery", 2022)):
    r = m6[(m6.file == f) & (m6.wy == wy)].iloc[0]
    print(f"  trace {f} {wy}: max {r.max_point:.1f} at {pd.Timestamp(int(r.t_max), unit='m')} | depth {dep.set_index('file').mm[f]:.1f} (SE {se[f]:.1f}) | known {r.known_frac}")
# the five 'outside NZ' gauges: raw coordinates
inv = pd.read_parquet(D / "inventory.parquet"); inv["stem"] = inv.server + "__" + inv.site.map(lambda s: re.sub(r"[^A-Za-z0-9._-]+", "_", s))
sk = pd.read_csv(D / "hirds_depths_skipped.csv")
print("\n== skipped gauges' raw coordinates (NZTM easting ~1.0-2.1e6, northing ~4.7-6.2e6; NZMG easting ~2.0-3.0e6, northing ~5.3-6.8e6):")
print(inv[inv.stem.isin(sk.file)][["stem", "easting", "northing"]].drop_duplicates("stem").to_string(index=False))
print("   ok years (6 h primary) of the skipped gauges:", m6[m6.file.isin(sk.file) & (m6.wy >= 2017) & m6.ok].groupby("file").size().to_dict())

print("\n== Auckland diagnostics (aggregate only)")
ak = [f for f in M.file.unique() if f.startswith("Auckland__")]
rows = []
for f in ak:
    t, v, q = MX.load(MX.S / f"{f}.npz")
    if len(t) < 2:
        continue
    e, val, qq = t[1:], v[1:], q[1:]; wy = MX.wy_of(e)
    for y in range(2017, 2026):
        m = wy == y
        if not m.any():
            continue
        h = np.where(qq[m] >= 0, qq[m] // 100, -1)
        rows.append((f, y, int(m.sum()), float(np.mean(~np.isfinite(val[m]))), float(np.mean(h == 2)), float(np.mean(h == 1) + np.mean(h == 3)), float(np.mean(h == -1)), float(np.mean(h >= 4)), float(np.nanmin(val[m])) >= 0))
R = pd.DataFrame(rows, columns=["file", "wy", "records", "nan_share", "share_2xx", "share_1xx_3xx", "share_nocode", "share_4xx_6xx", "nonneg"])
print("Auckland per-year mean shares (over gauges):\n", R.groupby("wy")[["nan_share", "share_2xx", "share_1xx_3xx", "share_nocode", "share_4xx_6xx"]].mean().round(3).to_string())
print("all Auckland values non-negative:", bool(R.nonneg.all()))
a6 = m6[m6.file.isin(ak) & (m6.wy >= 2017)]
print("Auckland 2018/19 under primary: known_frac quantiles", np.round(np.percentile(a6[a6.wy == 2018].known_frac, [10, 50, 90]), 2), "| dense share", round(float(a6[a6.wy == 2018].dense.mean()), 2), "| resolved share", round(float(a6[a6.wy == 2018].resolved.mean()), 2))
a6s3 = A.qualify(M, 6, "S3"); a6s3 = a6s3[a6s3.file.isin(ak) & (a6s3.wy == 2018)]
print("Auckland 2018/19 under S3: known_frac quantiles", np.round(np.percentile(a6s3.known_frac, [10, 50, 90]), 2), "| ok share", round(float(a6s3.ok.mean()), 2))
# post hoc Auckland under S3 with the out-of-sample start at 2017/18 (HIRDS report: Auckland data to early 2017)
ga = g.copy(); ga.loc[ga.server == "Auckland", "oos_first"] = 2017
for variant in ("primary", "S3"):
    for k in (8, 6):
        A.MIN_OOS = k
        r, _ = A.run(M, H, ga, rng=np.random.default_rng(11), variant=variant, servers=["Auckland"])
        print(f"  Auckland post hoc, oos from 2017/18, {variant}, >= {k} years:", r)
A.MIN_OOS = 8
