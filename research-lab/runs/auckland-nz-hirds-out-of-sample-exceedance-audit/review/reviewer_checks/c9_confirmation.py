"""Confirmation pass (D7, commit da57d4d): reproduce H1 on the regenerated maxima; inspect the 12 series excluded as
non-incremental; Okoraka's screened records; the 9 duplicate pairs; strictness of the same-name fitting-site match;
the window screen's handling of NaN; coverage sums; an independent studentized interval; beyond-250-year cases."""
import re, sys, json
from pathlib import Path
import numpy as np, pandas as pd
RUN = Path("/mnt/citations/research-lab/runs/auckland-nz-hirds-out-of-sample-exceedance-audit")
D, T = RUN / "data", RUN / "results" / "tables"
sys.path.insert(0, str(RUN / "code"))
import analyse as A, maxima as MX
M, H, S = A.load()
sc = pd.read_csv(T / "screen_counts.csv")
faulty = sorted(sc.file[sc.gauge_fault == 1])
M2 = M[~M.file.isin(faulty)]
g = A.gauge_meta(H, S); m6 = A.qualify(M2, 6, "primary")
g, dup = A.dedupe(g, m6[m6.ok].groupby("file").size())
dep = A.depth_of(H, 6, 0.1); yrs = list(range(2017, 2026))
inc = A.included(m6, g) & set(dep.file)
x = A.oe_table(A.oos_rows(m6, g), dep, yrs, inc)
print("== H1 reproduced:", int(x.exceed.sum()), len(x), x.file.nunique(), round(x.exceed.sum() / (0.1 * len(x)), 3))
old = set(pd.read_csv(T / "v1_before_screen" / "gauges.csv").file)   # the 201 at review time (same set as 1416f02)
new = set(x.file)
print("gauges left since review:", sorted(old - new)); print("gauges entered:", sorted(new - old))

print("\n== the 12 series excluded as non-incremental")
inv = pd.read_parquet(D / "inventory.parquet"); inv["stem"] = inv.server + "__" + inv.site.map(lambda s: re.sub(r"[^A-Za-z0-9._-]+", "_", s))
oldx = pd.read_csv(T / "v1_before_screen" / "gauges.csv").set_index("file")
rows = []
for f in faulty:
    z = np.load(D / "series" / f"{f}.npz", allow_pickle=False); v = z["v"].astype(float); t = z["t"].astype(float)
    meas = str(z["measurement"]) if "measurement" in z.files else ""
    r = inv[(inv.stem == f) & (inv.measurement == meas)]
    interp = r.interpolation.iloc[0] if len(r) else "?"
    fin = v[np.isfinite(v)]
    rows.append((f, meas, interp, len(v), int((fin < 0).sum()), round(float(np.percentile(fin, 50)), 2), round(float(np.percentile(fin, 99)), 1), round(float(fin.max()), 1),
                 round(float(sc.set_index("file").max_wy_total[f]), 0), round(float(np.mean(np.diff(fin[:50000]) >= 0)), 2) if len(fin) > 100 else np.nan,
                 int(oldx.exceed.get(f, -1)), int(oldx.years.get(f, -1))))
F = pd.DataFrame(rows, columns=["file", "measurement", "interp", "records", "negatives", "p50", "p99", "max", "max_wy_total", "share_nondecreasing_first50k", "old_exceed", "old_years"])
pd.set_option("display.width", 250); print(F.to_string(index=False))
print("gauges with isolated negatives (not excluded):", sc[(sc.gauge_fault == 0) & (sc.negatives > 0)][["file", "negatives", "screened"]].to_string(index=False))

print("\n== Okoraka at Ngatawhiti Road: records removed by the screen, by date")
f = "Northland__Okoraka_at_Ngatawhiti_Road"
t, v, q = MX.load(MX.S / f"{f}.npz"); s, e, val = t[:-1], t[1:], v[1:]; L = e - s
pb = MX.physical_bad(e, L, val)
dates = pd.to_datetime(e[pb], unit="m").normalize()
print(pd.Series(val[pb]).groupby(dates).agg(["size", "sum"]).round(1).to_string())
print("2024/25 6-h max now:", m6[(m6.file == f) & (m6.wy == 2024)].max_point.round(1).tolist(), "| depth", round(float(dep.set_index("file").mm[f]), 1))
print("screen_counts row:", sc[sc.file == f].to_dict("records"))

print("\n== duplicates dropped (9) with their kept partner and distance")
gk = g.set_index("file")
gall = A.gauge_meta(H, S).set_index("file")
for d_ in dup:
    best = None
    for k in gk.index:
        km = np.hypot((gall.lon[d_] - gk.lon[k]) * 111.32 * np.cos(np.radians(gall.lat[d_])), (gall.lat[d_] - gk.lat[k]) * 110.57)
        if km <= 2.0 and (km <= 0.1 or A.same_site(k, d_)):
            if best is None or km < best[1]:
                best = (k, km)
    print(f"  {d_}  <-  {best[0] if best else '?'}  ({best[1]:.2f} km)" if best else f"  {d_}  <- ?")
# false-positive risk of same_site among kept gauges: pairs within 2 km that same_site would merge but which are different sites by name
print("\n== fitting-site match strictness")
print("fitting_by counts (gauges with depth):", gall.fitting_by.value_counts().to_dict() if "fitting_by" in gall else "n/a")
gi = gall.loc[sorted(inc)]
print("included: fitting", int(gi.fitting_site.sum()), "not", int((~gi.fitting_site).sum()))
S2 = S.assign(end=S.apply(A.hirds_coverage_end, axis=1))
def toks(sname):
    return A.site_tokens("x__" + sname)
missed = []
for fname, r in gi[~gi.fitting_site].iterrows():
    dx = (r.lon - S2.longitude.to_numpy()) * 111.32 * np.cos(np.radians(r.lat)); dy = (r.lat - S2.latitude.to_numpy()) * 110.57
    dist = np.hypot(dx, dy); near = np.flatnonzero(dist <= 3)
    hits = [(dist[j], S2.site_name.iloc[j], S2.end.iloc[j]) for j in near if A.same_site(fname, "x__" + S2.site_name.iloc[j])]
    if hits:
        hits.sort(); missed.append((fname, round(hits[0][0], 2), hits[0][1], int(hits[0][2])))
print("'not fitting' included gauges whose own same_site() rule matches a HIRDS site within 3 km:", len(missed), "| any with end >= 2017:", sum(1 for m in missed if m[3] >= 2017))
for m_ in missed[:12]:
    print("   ", m_)

print("\n== window screen with NaN values (Auckland series; aggregate only)")
nan_files = 0; disabled = 0
for fz in sorted(MX.S.glob("Auckland__*.npz")):
    z = np.load(fz, allow_pickle=False); v = z["v"].astype(float)
    if np.isnan(v).any():
        nan_files += 1
        e = z["t"].astype(float)[1:]; val = v[1:]
        C = np.r_[0.0, np.cumsum(val)]; tot = C[1:] - np.interp(e - 5, e, C[1:], left=0.0)
        disabled += int(np.isnan(tot).sum() > 0.5 * len(tot))
print(f"Auckland series with NaN: {nan_files}; series where the window total is NaN for more than half the records (screen effectively off): {disabled}")

print("\n== coverage sums")
cov = json.load(open(T / "coverage.json"))
for k, v in cov.items():
    print(k, "attempted", v["attempted"], "= ok", v["ok"], "+ drops", sum(v["drop_reasons"].values()), "->", v["ok"] + sum(v["drop_reasons"].values()) == v["attempted"])

print("\n== independent studentized interval from year_by_year.csv (cluster-robust t and bootstrap-t)")
from scipy import stats
y = pd.read_csv(T / "year_by_year.csv"); o, n = y.exceed.to_numpy(float), y.gauges.to_numpy(float); e_ = 0.1 * n
R = o.sum() / e_.sum(); u = (o - R * e_) / e_.mean(); se = u.std(ddof=1) / 3
print("O/E", round(R, 3), "| cluster-robust t(8):", np.round(R + np.array(stats.t.interval(0.95, 8)) * se, 3))
rng = np.random.default_rng(7); tb = []
for _ in range(4000):
    k = rng.integers(0, 9, 9); ob, eb = o[k], e_[k]; Rb = ob.sum() / eb.sum(); ub = (ob - Rb * eb) / eb.mean(); sb = ub.std(ddof=1) / 3
    if sb > 0: tb.append((Rb - R) / sb)
qq = np.percentile(tb, [2.5, 97.5]); print("bootstrap-t:", np.round([R - qq[1] * se, R - qq[0] * se], 3), "| reported ci_bootstrap_t:", json.load(open(T / "primary.json"))["H1"].get("ci_bootstrap_t"))

print("\n== beyond-250-year cases now (6 h)")
d250 = H[(H.table == "historical") & (H.duration_h == 6) & np.isclose(H.ari, 250)].set_index("file").mm
x["r250"] = x.max_point / x.file.map(d250)
print("above 250-yr:", int((x.r250 > 1).sum()), "| above 1.5x:", int((x.r250 > 1.5).sum()))
print(x[x.r250 > 1.3][["file", "wy", "max_point", "mm", "r250"]].sort_values("r250", ascending=False).round(2).to_string(index=False))
