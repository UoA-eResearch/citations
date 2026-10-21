"""Reviewer check: (1) trading-period alignment from solar-shaped injection profiles (peak TP vs solar noon);
(2) solar farms recorded in the Commercial segment (behind-the-meter exposure); (3) composition of the H4 bootstrap
distribution by whether EASH and TOPE were drawn."""
import sys, io, numpy as np, pandas as pd
from pathlib import Path
RUN = "/mnt/citations/research-lab/runs/energy-nz-embedded-solar-edb-demand"; RAW = Path("/mnt/data/edb-solar/raw")
sys.path.insert(0, RUN + "/code")
# (1) solar-shaped injection profiles, Feb 2026 and Jan 2025
for ym in ("202601", "202501"):
    x = pd.read_csv(RAW/"emi"/"Grid_import"/f"{ym}_Grid_import.csv", dtype=str); x.columns = [c.upper() for c in x.columns]
    x = x[x.UNIT_MEASURE.str.lower() == "kwh"]
    tp = x[[f"TP{k}" for k in range(1, 49)]].apply(pd.to_numeric, errors="coerce")
    prof = tp.groupby([x.POC, x.NWK_CODE, x.GENERATION_TYPE]).mean()
    night = prof[[f"TP{k}" for k in range(1, 9)]].mean(axis=1); peak = prof.max(axis=1)
    sol = prof[(night < 0.02 * peak) & (peak > 2000)]
    print(ym, "solar-shaped injection POCs (night<2% of peak): peak TP ->", {f"{p}/{n}/{g}": f"TP{int(r.idxmax()[2:])} ({r.max()/500:.0f} MW)" for (p, n, g), r in sol.iterrows()})
# (2) Commercial-segment steps > 3 MW in a month (farms recorded as commercial?)
def ea(name):
    lines = (RAW/"ea"/name).read_text().splitlines(); i = next(k for k, l in enumerate(lines) if l.startswith("Month end,"))
    x = pd.read_csv(io.StringIO("\n".join(lines[i:]))); x["month"] = pd.to_datetime(x["Month end"], dayfirst=True)
    return x.rename(columns={"Region ID": "pid", "Total capacity installed (MW)": "mw"})
com = ea("solar_Com_All_Total.csv").sort_values(["pid", "month"]); com["step"] = com.groupby("pid").mw.diff()
print("Commercial-segment monthly steps > 3 MW:", [(r.pid, r.month.strftime("%Y-%m"), round(r.step, 1)) for r in com[com.step > 3].itertuples()])
res = ea("solar_Res_All_Total.csv").sort_values(["pid", "month"]); res["step"] = res.groupby("pid").mw.diff()
print("Residential-segment monthly steps > 3 MW:", [(r.pid, r.month.strftime("%Y-%m"), round(r.step, 1)) for r in res[res.step > 3].itertuples()])
# (3) bootstrap composition (same scheme and seed as analysis.fast_bootstrap)
s = pd.read_csv(RUN + "/results/tables/panel_summer.csv")
s["mid_pi"] = s.mid_mw * 1000 / s.icps; s["solar_all_pi"] = s.solar_all_mw * 1000 / s.icps
d = s.dropna(subset=["mid_pi", "solar_all_pi", "tmax", "icps"])
rng = np.random.default_rng(20261021)
Y = d.mid_pi.to_numpy(float); X = d[["solar_all_pi", "tmax"]].to_numpy(float); W = np.sqrt(d.icps.to_numpy(float))
tcode = pd.factorize(d.summer)[0]; units = pd.unique(d.unit); rows = {u: np.flatnonzero(d.unit.to_numpy() == u) for u in units}
ie, it = list(units).index("EASH"), list(units).index("TOPE")
out = []
for _ in range(4999):
    pick = rng.choice(len(units), size=len(units), replace=True)
    idx = np.concatenate([rows[units[k]] for k in pick]); cl = np.concatenate([np.full(len(rows[units[k]]), j) for j, k in enumerate(pick)])
    m = len(idx); U = np.zeros((m, len(pick))); U[np.arange(m), cl] = 1.0
    tt = tcode[idx]; present = np.unique(tt); T = (tt[:, None] == present[None, 1:]).astype(float)
    M = np.column_stack([X[idx], U, T]) * W[idx, None]
    beta = np.linalg.lstsq(M, Y[idx] * W[idx], rcond=None)[0]
    out.append((beta[0], (pick == ie).sum(), (pick == it).sum()))
b = pd.DataFrame(out, columns=["est", "nE", "nT"])
print("reproduced percentile CI:", np.round(np.percentile(b.est, [2.5, 97.5]), 3).tolist())
grp = b.assign(both0=(b.nE == 0) & (b.nT == 0), oneof=((b.nE == 0) ^ (b.nT == 0))).groupby(["both0", "oneof"]).est.agg(["size", "median", lambda v: np.percentile(v, 2.5), lambda v: np.percentile(v, 97.5)])
print("draws by whether EASH/TOPE absent (both0=neither drawn; oneof=exactly one absent):\n", grp.round(3).to_string())
print("share of draws > -0.3:", round((b.est > -0.3).mean(), 3), "; share > 0:", round((b.est > 0).mean(), 3))
