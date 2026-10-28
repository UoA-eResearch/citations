"""Reviewer check 6b (tail of c6 after a file-name mismatch): plausibility.md traces, 'outside NZ' coordinates,
Auckland diagnostics (aggregate only), Auckland post hoc with the out-of-sample start at 2017/18."""
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
dep = A.depth_of(H, 6, 0.1).set_index("file").mm; se = A.depth_of(H, 6, 0.1, "historical_se").set_index("file").mm
for key, wy in (("Maharakeke", 2022), ("Anatoki_at_Paradise", 2017), ("Akatarawa_River_at_Cemetery", 2022)):
    fs = [f for f in m6.file.unique() if key in f]
    for f in fs:
        r = m6[(m6.file == f) & (m6.wy == wy)]
        if len(r):
            r = r.iloc[0]; print(f"trace {f} {wy}: max {r.max_point:.1f} at {pd.Timestamp(int(r.t_max), unit='m')} | depth {dep.get(f, np.nan):.1f} (SE {se.get(f, np.nan):.1f}) | known {r.known_frac} | exceeds {r.max_point > dep.get(f, np.inf)}")
inv = pd.read_parquet(D / "inventory.parquet"); inv["stem"] = inv.server + "__" + inv.site.map(lambda s: re.sub(r"[^A-Za-z0-9._-]+", "_", s))
sk = pd.read_csv(D / "hirds_depths_skipped.csv")
print("\n== skipped gauges' raw coordinates (NZTM E 1.0-2.1e6 / N 4.7-6.2e6; NZMG E 2.0-3.0e6 / N 5.3-6.8e6):")
print(inv[inv.stem.isin(sk.file)][["stem", "easting", "northing"]].drop_duplicates("stem").to_string(index=False))
print("   ok out-of-sample years (6 h primary) of the skipped gauges:", m6[m6.file.isin(sk.file) & (m6.wy >= 2017) & m6.ok].groupby("file").size().to_dict())
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
        rows.append((f, y, int(m.sum()), float(np.mean(~np.isfinite(val[m]))), float(np.mean(h == 2)), float(np.mean((h == 1) | (h == 3))), float(np.mean(h == -1)), float(np.mean(h >= 4)), bool(np.nanmin(val[m]) >= 0)))
R = pd.DataFrame(rows, columns=["file", "wy", "records", "nan_share", "share_2xx", "share_1xx_3xx", "share_nocode", "share_4xx_6xx", "nonneg"])
print("Auckland per-year mean shares over gauges:\n", R.groupby("wy")[["records", "nan_share", "share_2xx", "share_1xx_3xx", "share_nocode", "share_4xx_6xx"]].mean().round(3).to_string())
print("all Auckland values non-negative:", bool(R.nonneg.all()))
a6 = m6[m6.file.isin(ak) & (m6.wy >= 2017)]
for y in (2018, 2019, 2021, 2022):
    z = a6[a6.wy == y]
    print(f"Auckland {y}/{str(y+1)[2:]} primary: known_frac q10/50/90 {np.round(np.percentile(z.known_frac, [10, 50, 90]), 2)} | dense {z.dense.mean():.2f} | resolved {z.resolved.mean():.2f} | ok {z.ok.mean():.2f}")
a6s3 = A.qualify(M, 6, "S3"); a6s3 = a6s3[a6s3.file.isin(ak)]
for y in (2018, 2019):
    z = a6s3[a6s3.wy == y]; print(f"Auckland {y} S3: known_frac q10/50/90 {np.round(np.percentile(z.known_frac, [10, 50, 90]), 2)} | ok {z.ok.mean():.2f} | wet_median_min q50/90 {np.round(np.percentile(z.wet_median_min.dropna(), [50, 90]), 1)}")
ga = g.copy(); ga.loc[ga.server == "Auckland", "oos_first"] = 2017
for variant in ("primary", "S3"):
    for k in (8, 6):
        A.MIN_OOS = k
        r, _ = A.run(M, H, ga, rng=np.random.default_rng(11), variant=variant, servers=["Auckland"])
        print(f"Auckland post hoc with out-of-sample from 2017/18, {variant}, >= {k} years:", {k_: r[k_] for k_ in ('O', 'E', 'gauges', 'OE', 'ci')})
A.MIN_OOS = 8
