"""Reviewer checks 3-4: instrument, identification and re-estimation with independent code.
Reads data/series.pkl (and the raw generation files for unit-level Huntly series). Compares with results/tables/mef.json.
Writes out_reestimate.json."""
import glob
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

RUN = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / "out_reestimate.json"
sys.path.insert(0, str(RUN / "code"))
import mef as theirs  # noqa: E402  (the study's module, for comparison only)

out = {}
s = pd.read_pickle(RUN / "data" / "series.pkl").sort_values("ts").reset_index(drop=True)
m = json.load(open(RUN / "results" / "tables" / "mef.json"))
loc = s.ts.dt.tz_convert("Pacific/Auckland")

# ---------------- 1. instrument recomputed independently ----------------
hdd = np.maximum(0.0, 16.0 - s.temp.values)
doy = loc.dt.dayofyear.values
leap_shift = ((loc.dt.is_leap_year) & (doy > 59)).values   # after Feb 29 in a leap year, align on calendar day (Mar 1 = 60)
doy_cal = np.where(leap_shift, doy - 1, doy)
doy_cal = np.minimum(doy_cal, 365)
df = pd.DataFrame(dict(hdd=hdd, hh=s.hh.values, doy=doy_cal))
clim = df.groupby(["hh", "doy"]).hdd.mean().unstack()               # 48 x 365
# circular 15-day centred smoothing along doy
ext = np.concatenate([clim.values[:, -7:], clim.values, clim.values[:, :7]], axis=1)
sm15 = np.column_stack([ext[:, i:i + 15].mean(axis=1) for i in range(365)])
z_mine = hdd - sm15[s.hh.values, doy_cal - 1]
z_theirs = theirs.instrument(s)
out["instrument"] = dict(corr=float(np.corrcoef(z_mine, z_theirs)[0, 1]), max_abs_diff=float(np.abs(z_mine - z_theirs).max()),
                         mean_abs_diff=float(np.abs(z_mine - z_theirs).mean()), sd_z=float(z_theirs.std()),
                         note="mine aligns leap years on calendar day; theirs caps day-of-year at 365, shifting the climatology by one day after Feb 29 in leap years",
                         share_zero_hdd=float((hdd == 0).mean()), share_zero_hdd_winter=float((hdd[np.isin(s.month.values, [6, 7, 8])] == 0).mean()))
s["z"] = z_theirs   # use theirs for the reproduction; mine for a sensitivity
s["z_mine"] = z_mine

# ---------------- 2. controls as in mef.py (re-implemented) ----------------
s["ym"] = s.year.astype(str) + "-" + s.month.astype(str).str.zfill(2)
for k in range(4):
    s[f"zl{k + 1}"] = s.z.shift(1 + 12 * k).rolling(12).mean()
s["D1"], s["E1"] = s.D.shift(1), s.E.shift(1)
s["Dday"], s["Eday"] = s.D.shift(1).rolling(48).mean(), s.E.shift(1).rolling(48).mean()
s["hvdc_day"], s["tiwai_day"] = s.hvdc_north.shift(1).rolling(48).mean(), s.tiwai.shift(1).rolling(48).mean()
di = s.groupby("date").inflow.first()
s["inflow7"] = s.date.map(di.shift(1).rolling(7).mean())
H = [1, 2, 4, 8, 24, 48, 96, 336, 672, 1440]
LAB = theirs.LAB


def wsum(x, h):
    cs = np.concatenate([[0.0], np.cumsum(x)])
    o = np.full(len(x), np.nan); o[: len(x) - h + 1] = cs[h:] - cs[: len(x) - h + 1]; return o


# unit-level Huntly series from the raw files (for the composition probe)
cache = HERE / "cache" / "huntly_units.pkl"
if cache.exists():
    units = pd.read_pickle(cache)
else:
    key = {(d, i + 1): t for d, g in s.groupby("date") for i, t in enumerate(g.ts.values)}
    parts = []
    for f in sorted(glob.glob(str(RUN / "data" / "raw" / "generation" / "*.csv"))):
        d = pd.read_csv(f); d.columns = [c if not c.lower().startswith("trading") else "Trading_Date" for c in d.columns]
        d = d[d.Gen_Code.isin(["huntly_1_4", "huntly_e3p", "huntly_p40", "stratford", "otahuhu_b", "mckee", "McKee", "junctionroad", "te_rapa", "kapuni", "whareroa", "southdown", "whirinaki"])]
        tps = [c for c in d.columns if re.fullmatch(r"TP\d+", c)]
        mm = d.melt(id_vars=["Gen_Code", "Trading_Date"], value_vars=tps, var_name="tp", value_name="kwh").dropna(subset=["kwh"])
        mm["tp"] = mm.tp.str[2:].astype(int)
        mm["ts"] = [key.get((dd[:10], tp)) for dd, tp in zip(mm.Trading_Date.astype(str), mm.tp)]
        parts.append(mm.dropna(subset=["ts"]))
    u = pd.concat(parts)
    units = u.pivot_table(index="ts", columns="Gen_Code", values="kwh", aggfunc="sum").fillna(0) / 1000
    units = units.reindex(s.ts.values).fillna(0)
    units.to_pickle(cache)
for c in units.columns:
    s[f"u_{c}"] = units[c].values
gas_other = [c for c in units.columns if c not in ("huntly_1_4", "huntly_e3p")]
s["u_gas_other"] = units[gas_other].sum(axis=1).values

SRC = {"D": "D", "E": "E", "W": "wind", "G": "geo", "Y": "hydro", "TH": "thermal", "C": "coal", "GS": "gas",
       "RK": "u_huntly_1_4", "E3P": "u_huntly_e3p", "GO": "u_gas_other", "Z": "z", "ZM": "z_mine"}
new = {f"{v}_{h}": wsum(s[src].values, h) for h in H for v, src in SRC.items()}
s = pd.concat([s, pd.DataFrame(new)], axis=1)
# daily-mean instruments: mean z over the first 24 h of the window, and the mean over the local calendar day of t
s["zbar24"] = s["Z_48"] / 48
s["zday"] = s.groupby("date").z.transform("mean")
need = ["zl4", "Dday", "inflow7", "hvdc_day", "storage", f"D_{max(H)}"]
IDX = np.where(s[need].notna().all(axis=1))[0]
out["n_common_sample"] = dict(mine=int(len(IDX)), theirs=m["n"])


def design(d, extra_fe=False, drop_lags=False):
    fe = [pd.get_dummies(d.hh.astype(str) + "_" + d.daytype.astype(str), dtype=float),
          pd.get_dummies(d.month, prefix="m", drop_first=True, dtype=float),
          pd.get_dummies(d.year, prefix="y", drop_first=True, dtype=float)]
    if extra_fe:   # half-hour x month interactions (seasonality probe)
        fe.append(pd.get_dummies(d.hh.astype(str) + "_mo" + d.month.astype(str), drop_first=True, dtype=float))
    cols = ["zl1", "zl2", "zl3", "zl4", "storage", "inflow7", "hvdc_day", "tiwai_day"] + ([] if drop_lags else ["D1", "Dday", "E1", "Eday"])
    cont = d[cols]; cont = (cont - cont.mean()) / cont.std()
    X = np.column_stack([pd.concat(fe, axis=1).values, cont.values])
    # drop exactly collinear columns (can arise with hh x month dummies)
    q, r = np.linalg.qr(X)
    keep = np.abs(np.diag(r)) > 1e-8
    return X[:, keep]


def iv(idx, h, outcomes, inst="z", wind=True, extra_fe=False, drop_lags=False, with_se=False):
    """2SLS of window outcome on window demand instrumented by inst, controls partialled out jointly (one QR)."""
    d = s.iloc[idx]
    X = design(d, extra_fe, drop_lags)
    if wind:
        X = np.column_stack([X, d[f"W_{h}"].values])
    q, _ = np.linalg.qr(X)
    def res(v): return v - q @ (q.T @ v)
    zr = res(d[inst].values.astype(float)); Dr = res(d[f"D_{h}"].values)
    pi = (zr @ Dr) / (zr @ zr); u = Dr - pi * zr
    g = d.ym.values
    sc = pd.Series(zr * u).groupby(g).sum().values
    F_plain = float((pi / (np.sqrt((sc ** 2).sum()) / (zr @ zr))) ** 2)         # their formula (no small-sample factor)
    G = len(sc); N = len(zr); K = X.shape[1] + 1
    F_adj = F_plain / (G / (G - 1) * (N - 1) / (N - K))
    r = dict(F=F_plain, F_adj=F_adj, pi=float(pi), n=int(N), months=int(G))
    for o in outcomes:
        Yr = res(d[f"{o}_{h}"].values)
        b = float((zr @ Yr) / (zr @ Dr))
        r[o] = b
        if with_se:   # cluster-robust 2SLS SE for the single endogenous regressor after partialling
            e = Yr - b * Dr
            sc2 = pd.Series(zr * e).groupby(g).sum().values
            r[f"{o}_se"] = float(np.sqrt((sc2 ** 2).sum()) / abs(zr @ Dr))
    return r


OUTC = ["E", "Y", "TH", "G", "C", "GS", "RK", "E3P", "GO"]
# ---------------- 3. reproduction at every horizon ----------------
rep = {}
for h in H:
    r = iv(IDX, h, ["E", "Y", "TH", "G"], with_se=True)
    t = next(x for x in m["horizons"] if x["h"] == h)
    rep[LAB[h]] = dict(mef_mine=r["E"], mef_theirs=t["mef"], F_mine=r["F"], F_theirs=t["first_stage_F"], F_small_sample_adj=r["F_adj"],
                       hydro_mine=r["Y"], hydro_theirs=t["hydro"], thermal_mine=r["TH"], thermal_theirs=t["thermal"], geo_mine=r["G"], geo_theirs=t["geo"],
                       analytic_95ci=[r["E"] - 1.96 * r["E_se"], r["E"] + 1.96 * r["E_se"]], boot_ci_theirs=t["ci"])
out["reproduction"] = rep

# FWL two-step vs joint: redo their two-step at h=48 and compare
d = s.iloc[IDX]
Xb = design(d); qb, _ = np.linalg.qr(Xb)
def rb(v): return v - qb @ (qb.T @ v)
zr, Dr, Wr, Er = rb(d.z.values), rb(d.D_48.values), rb(d.W_48.values), rb(d.E_48.values)
bw = lambda v: v - Wr * (Wr @ v) / (Wr @ Wr)
two_step = float((bw(zr) @ bw(Er)) / (bw(zr) @ bw(Dr)))
out["fwl_two_step_vs_joint_1d"] = dict(two_step=two_step, joint=rep["1d"]["mef_mine"], theirs=rep["1d"]["mef_theirs"])

# ---------------- 4. alternatives at 1 h, 1 d, 7 d (and 0.5 h for composition) ----------------
HS = [1, 2, 8, 48, 336]
def run_variant(name, idx=IDX, **kw):
    res = {}
    for h in HS:
        r = iv(idx, h, OUTC, **kw)
        res[LAB[h]] = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()}
    out.setdefault("variants", {})[name] = res
    print(name); print(pd.DataFrame(res).T[["E", "F", "Y", "TH", "G", "C", "GS", "RK", "E3P", "GO"]].to_string())

run_variant("baseline")
run_variant("no_wind_control", wind=False)
run_variant("instrument_mine_leapfix", inst="z_mine")
run_variant("instrument_mean_first_24h", inst="zbar24")
run_variant("instrument_calendar_day_mean", inst="zday")
run_variant("drop_2021_2024", idx=IDX[~np.isin(s.year.values[IDX], [2021, 2024])])
run_variant("no_lagged_D_E_controls", drop_lags=True)
run_variant("hh_x_month_FE", extra_fe=True)
run_variant("years_2015_2019", idx=IDX[s.year.values[IDX] <= 2019])
run_variant("years_2020_2024", idx=IDX[s.year.values[IDX] >= 2020])
# daytime window starts only (06-18) and night starts (18-06)
blk = s.hh.values // 12
run_variant("starts_06_18", idx=IDX[np.isin(blk[IDX], [1, 2])])
run_variant("starts_18_06", idx=IDX[np.isin(blk[IDX], [0, 3])])
# Tiwai demand-response exclusion: days with daily Tiwai MW at least 100 MW below the trailing 30-day median, or below 450 MW
dly = s.groupby("date").tiwai.sum() / 24
base = dly.shift(1).rolling(30).median()
flag_days = set(dly.index[(dly <= base - 100) | (dly < 450)])
out["tiwai_flagged_days"] = dict(n=len(flag_days), years=pd.Series(sorted(flag_days)).str[:4].value_counts().to_dict())
flag = s.date.isin(flag_days).values.astype(float)
# exclude window starts whose window [t, t+336) touches a flagged day (use the 7-day window for all horizons, conservatively)
touch = wsum(flag, 336)
keep = IDX[(touch[IDX] == 0)]
out["tiwai_exclusion_n"] = int(len(keep))
run_variant("exclude_tiwai_DR_windows", idx=keep)

# ---------------- 5. gradient under each variant ----------------
grad = {}
for name, res in out["variants"].items():
    grad[name] = dict(mef_1h=res["1h"]["E"], mef_1d=res["1d"]["E"], mef_7d=res["7d"]["E"], d_1d_1h=round(res["1d"]["E"] - res["1h"]["E"], 4),
                      d_7d_1h=round(res["7d"]["E"] - res["1h"]["E"], 4), F_1h=res["1h"]["F"], F_1d=res["1d"]["F"], F_7d=res["7d"]["F"])
out["gradient_by_variant"] = grad
print(pd.DataFrame(grad).T.to_string())

# ---------------- 6. bootstrap: their draws, my re-implementation, and a 2-month block ----------------
dr = np.load(RUN / "data" / "mef_draws.npz")
draws = dr["horizons"]
i1, i48, i336 = H.index(2), H.index(48), H.index(336)
def ci(x): return [float(np.nanpercentile(x, 2.5)), float(np.nanpercentile(x, 97.5))]
out["descriptive_gradient_from_their_draws"] = dict(
    d_1d_1h_point=m["horizons"][i48]["mef"] - m["horizons"][i1]["mef"], d_1d_1h_ci=ci(draws[:, i48] - draws[:, i1]),
    d_7d_1h_point=m["horizons"][i336]["mef"] - m["horizons"][i1]["mef"], d_7d_1h_ci=ci(draws[:, i336] - draws[:, i1]),
    d_7d_1h_boot_median=float(np.nanmedian(draws[:, i336] - draws[:, i1])), mef_7d_boot_median=float(np.nanmedian(draws[:, i336])),
    share_draws_7d_gt_1h=float(np.mean(draws[:, i336] > draws[:, i1])))

def month_sums(idx, h, wind=True):
    d = s.iloc[idx]; X = design(d)
    if wind: X = np.column_stack([X, d[f"W_{h}"].values])
    q, _ = np.linalg.qr(X)
    def res(v): return v - q @ (q.T @ v)
    zr, Dr, Er = res(d.z.values), res(d[f"D_{h}"].values), res(d[f"E_{h}"].values)
    g = pd.DataFrame(dict(m=d.ym.values, zD=zr * Dr, zE=zr * Er)).groupby("m").sum()
    return g
rng = np.random.default_rng(20261018)
boot = {}
for h in (2, 48, 336):
    g = month_sums(IDX, h)
    months = g.index.values; M = len(months)
    S = rng.integers(0, M, size=(999, M))
    b1 = g.zE.values[S].sum(1) / g.zD.values[S].sum(1)
    # 2-month blocks (circular), same number of months
    nb = (M + 1) // 2
    S2 = rng.integers(0, M, size=(999, nb)); S2 = np.concatenate([S2, (S2 + 1) % M], axis=1)[:, :M]
    b2 = g.zE.values[S2].sum(1) / g.zD.values[S2].sum(1)
    # 3-month blocks
    nb3 = (M + 2) // 3
    S3 = rng.integers(0, M, size=(999, nb3)); S3 = np.concatenate([S3, (S3 + 1) % M, (S3 + 2) % M], axis=1)[:, :M]
    b3 = g.zE.values[S3].sum(1) / g.zD.values[S3].sum(1)
    boot[LAB[h]] = dict(point=float(g.zE.sum() / g.zD.sum()), ci_1month_mine=ci(b1), ci_2month=ci(b2), ci_3month=ci(b3),
                        ci_theirs=next(x for x in m["horizons"] if x["h"] == h)["ci"])
out["bootstrap"] = boot
print(json.dumps(boot, indent=1))

# ---------------- 7. time-of-day blocks at 1 d (reproduce) and first stage by block at short horizons ----------------
blocks = {}
for b in range(4):
    idb = IDX[blk[IDX] == b]
    r48 = iv(idb, 48, ["E", "Y", "TH", "G"], with_se=True)
    r1 = iv(idb, 1, ["E"]); r8 = iv(idb, 8, ["E"])
    blocks[f"{6 * b:02d}-{6 * b + 6:02d}"] = dict(mef_1d_mine=r48["E"], mef_1d_theirs=m["blocks_1d"][b]["mef"], F_1d_mine=r48["F"], F_1d_theirs=m["blocks_1d"][b]["F"],
                                                  pi_1d=r48["pi"], F_halfhour=r1["F"], mef_halfhour=r1["E"], F_4h=r8["F"], mef_4h=r8["E"],
                                                  hydro_1d=r48["Y"], thermal_1d=r48["TH"], n=r48["n"])
out["blocks_1d"] = blocks
print(pd.DataFrame(blocks).T.to_string())
# night block with the daily-mean instrument (is the weakness a property of the half-hour instrument?)
idb = IDX[blk[IDX] == 0]
out["night_block_alt_instruments"] = {k: iv(idb, 48, ["E"], inst=k) for k in ("z", "zbar24", "zday")}
print("night block alt instruments:", out["night_block_alt_instruments"])

# ---------------- 8. storage terciles (reproduce) ----------------
rel = s.storage - s.groupby(loc.dt.dayofyear).storage.transform("mean")
terc = pd.qcut(rel.iloc[IDX], 3, labels=False).values
ter = {}
for k in range(3):
    r = iv(IDX[terc == k], 48, ["E"])
    ter[k] = dict(mef_mine=r["E"], mef_theirs=m["storage_terciles_1d"][k]["mef"], F_mine=r["F"], F_theirs=m["storage_terciles_1d"][k]["F"])
out["storage_terciles"] = ter

# ---------------- 9. exclusion probes: reduced forms of fuel availability on z ----------------
# Does the cold anomaly predict gas-plant availability? Regress the window's e3p output and 'other gas' output on z (reduced form, per MW of D)
# at 0.5 h with and without the lagged D/E controls; and the response of coal at 0.5 h by season (winter only)
win = IDX[np.isin(s.month.values[IDX], [5, 6, 7, 8, 9])]
run_variant("winter_only_May_Sep", idx=win)
# e3p out-of-service periods: share of half-hours with e3p = 0 by year
out["e3p_zero_share_by_year"] = (s.u_huntly_e3p == 0).groupby(s.year).mean().round(3).to_dict()
out["rankine_zero_share_by_year"] = (s.u_huntly_1_4 == 0).groupby(s.year).mean().round(3).to_dict()
# mean reversion check: correlation of z with the previous half-hour's change in gas output (is 'gas down' a continuation of ramp-down?)
json.dump(out, open(OUT, "w"), indent=1, default=float)
print("written", OUT)
