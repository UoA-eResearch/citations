"""Reviewer check 3: independent exact (event-based) sliding 6-h annual maxima for every primary gauge-year, without
maxima.py's grid or functions; decisions flipped by the 5-minute grid; year assignment at the boundary; np.interp
behaviour on exact-duplicate time stamps; HIRDS depth monotonicity failures."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
RUN = Path("/mnt/citations/research-lab/runs/auckland-nz-hirds-out-of-sample-exceedance-audit")
D, T = RUN / "data", RUN / "results" / "tables"
sys.path.insert(0, str(RUN / "code"))
import analyse as A   # only for the include list and depth join

def load_raw(stem):
    parts = []
    for p in (D / "series_early" / f"{stem}.npz", D / "series" / f"{stem}.npz"):
        if p.exists():
            z = np.load(p, allow_pickle=False); parts.append((z["t"].astype(float), z["v"].astype(float), z["q"].astype(int)))
    if len(parts) == 2 and len(parts[0][0]) and len(parts[1][0]):
        k = parts[1][0] > parts[0][0].max(); parts[1] = tuple(a[k] for a in parts[1])
    t, v, q = (np.concatenate([p[i] for p in parts]) for i in range(3))
    o = np.argsort(t, kind="stable"); return t[o], v[o], q[o]

def my_bad(L, val, q):
    h = np.where(q >= 0, q // 100, -1)
    bad = np.isin(h, [1, 2, 3]) | ~np.isfinite(val)
    bad |= ((val > 50) & (L <= 15)) | ((val > 150) & (L <= 60))
    big = val >= 2
    same = np.r_[False, (val[1:] == val[:-1]) & big[1:] & big[:-1]]
    rid = np.cumsum(~same); rl = np.bincount(rid)[rid]
    return bad | (big & (rl >= 24))

def exact_max(t, v, q, y, d=6):
    """Largest d-hour total with the window end in (1 Jul y, 1 Jul y+1]: rain spread evenly within each (s, e]."""
    s, e, val, qq = t[:-1], t[1:], v[1:], q[1:]
    L = e - s
    rain = np.where(my_bad(L, val, qq), 0.0, val)
    # cumulative at record times; duplicates in e collapse to the last value
    C = np.r_[0.0, np.cumsum(rain)]; x = np.r_[s[0], e]
    ux, idx = np.unique(x, return_index=True)            # first index of each distinct time
    last = np.r_[idx[1:] - 1, len(x) - 1]                # last index -> cumulative after all tips at that instant
    Cu = C[last]
    a = int(pd.Timestamp(f"{y}-07-01").value // 60_000_000_000); b = int(pd.Timestamp(f"{y + 1}-07-01").value // 60_000_000_000)
    ends = np.unique(np.r_[ux, ux + d * 60]); ends = ends[(ends > a) & (ends <= b)]
    if not len(ends):
        return np.nan, np.nan
    w = np.interp(ends, ux, Cu) - np.interp(ends - d * 60, ux, Cu)
    i = int(np.argmax(w)); return float(w[i]), float(ends[i])

M, H, S = A.load()
g = A.gauge_meta(H, S); m6 = A.qualify(M, 6, "primary")
g, dup = A.dedupe(g, m6[m6.ok].groupby("file").size())
inc = A.included(m6, g) & set(A.depth_of(H, 6, 0.1).file)
x = A.oe_table(A.oos_rows(m6, g), A.depth_of(H, 6, 0.1), list(range(2017, 2026)), inc)
print("primary gauge-years:", len(x))
rows = []
cache = {}
for r in x.itertuples():
    if r.file not in cache:
        cache[r.file] = load_raw(r.file)
    t, v, q = cache[r.file]
    ex, tend = exact_max(t, v, q, r.wy)
    rows.append((r.file, r.wy, r.max_point, ex, tend, r.t_max, r.mm, r.exceed))
E = pd.DataFrame(rows, columns=["file", "wy", "grid", "exact", "t_exact", "t_grid", "mm", "exceed"])
E["ratio"] = E.grid / E.exact
print("grid/exact: min %.4f, 1st pct %.4f, median %.4f; grid > exact + 1e-6 in %d gauge-years" % (E.ratio.min(), E.ratio.quantile(0.01), E.ratio.median(), int((E.grid > E.exact + 1e-6).sum())))
print("gauge-years where exact > depth but grid <= depth (missed by the grid):", int(((E.exact > E.mm) & (E.grid <= E.mm)).sum()))
print("gauge-years where grid > depth but exact <= depth:", int(((E.grid > E.mm) & (E.exact <= E.mm)).sum()))
print("exceedances by exact method:", int((E.exact > E.mm).sum()), "vs grid:", int(E.exceed.sum()), "-> O/E exact", round(float((E.exact > E.mm).sum() / (0.1 * len(E))), 3))
print("window-end time agreement (|t_exact - t_grid| <= 5 min):", round(float((np.abs(E.t_exact - E.t_grid) <= 5).mean()), 3))
E.to_csv(RUN / "review" / "reviewer_checks" / "c3_exact_vs_grid.csv", index=False)
bad = E[(E.exact > E.mm) & (E.grid <= E.mm)]
print(bad[["file", "wy", "grid", "exact", "mm"]].to_string(index=False))
# duplicate time stamps: how common, and does np.interp with duplicates give the right cumulative?
ndup = 0; ntot = 0; worst = 0.0
for f, (t, v, q) in cache.items():
    ntot += len(t); ndup += int((np.diff(t) == 0).sum())
print("exact-duplicate time stamps across included gauges:", ndup, "of", ntot, "records")
xp = np.array([0., 10., 10., 10., 20.]); fp = np.array([0., 1., 2., 3., 4.])
print("np.interp at a triple-duplicate x=10 returns", np.interp(10.0, xp, fp), "(cumulative after all tips = 3.0); at 15:", np.interp(15.0, xp, fp), "(expected 3.5)")
# depth monotonicity in duration: where does it fail?
piv = H[H.table == "historical"].pivot_table(index=["file", "ari"], columns="duration_h", values="mm")
dec = (piv.diff(axis=1).iloc[:, 1:] < 0)
print("file x ARI rows with a depth decreasing in duration:", int(dec.any(axis=1).sum()), "of", len(piv), "| columns involved:", dec.sum().to_dict())
print(piv[dec.any(axis=1)].head(5).round(1).to_string())
