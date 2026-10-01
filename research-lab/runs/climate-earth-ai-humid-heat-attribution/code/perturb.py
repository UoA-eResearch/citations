#!/usr/bin/env python
"""Counterfactual initial conditions (plan.md sec 3).

deltas_to_n320(): each CMIP6 model's event-month warming signal (ta at 13 levels, tas, ts) interpolated bilinearly to the
N320 points; ta levels below the model surface (NaN) are filled from the nearest valid level above, or from tas.
counterfactual(): world 'A' (temperature only) or 'B' (constant relative humidity) from a factual N320 state.
"""
import sys
from pathlib import Path

import numpy as np
import xarray as xr
from scipy.interpolate import RegularGridInterpolator

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wetbulb import es, qsat  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
PROC = RUN / "data" / "processed"
LEVELS = [1000, 925, 850, 700, 600, 500, 400, 300, 250, 200, 150, 100, 50]
RD = 287.05


def _interp(field, lat, lon, plat, plon):
    """Bilinear interpolation of a (lat, lon) field to points, periodic in longitude."""
    order = np.argsort(lat)
    lat, field = lat[order], field[order]
    lon = np.asarray(lon) % 360
    o2 = np.argsort(lon)
    lon, field = lon[o2], field[:, o2]
    lon_ext = np.concatenate([lon[-1:] - 360, lon, lon[:1] + 360])
    f_ext = np.concatenate([field[:, -1:], field, field[:, :1]], axis=1)
    f = RegularGridInterpolator((lat, lon_ext), f_ext, bounds_error=False, fill_value=None)
    return f(np.column_stack([np.clip(plat, lat.min(), lat.max()), plon % 360]))


def deltas_to_n320(model, month):
    path = PROC / "deltas_n320" / f"{model}_m{month}.npz"
    if path.exists():
        return dict(np.load(path))
    ll = np.load(PROC / "n320_latlon.npz")
    plat, plon = ll["lat"].astype(float), ll["lon"].astype(float)
    ds = xr.open_dataset(PROC / "deltas" / f"{model}.nc").sel(month=month)
    lat, lon = ds.lat.values, ds.lon.values
    tas = _interp(ds.tas.values, lat, lon, plat, plon)
    ts = _interp(ds.ts.values, lat, lon, plat, plon)
    ta = ds.ta.values                                                  # (13, lat, lon), levels 1000 -> 50 hPa
    ta_f = ta.copy()
    for k in range(len(LEVELS) - 2, -1, -1):                         # fill below-ground NaN from the level above
        ta_f[k] = np.where(np.isfinite(ta_f[k]), ta_f[k], ta_f[k + 1])
    ta_f = np.where(np.isfinite(ta_f), ta_f, ds.tas.values[None])
    ta_n = np.stack([_interp(ta_f[k], lat, lon, plat, plon) for k in range(len(LEVELS))])
    path.parent.mkdir(parents=True, exist_ok=True)
    out = dict(ta=ta_n.astype(np.float32), tas=tas.astype(np.float32), ts=ts.astype(np.float32))
    np.savez(path, **out)
    return out


def counterfactual(state, d, world, scale=1.0):
    """state: dict name -> (2, n) arrays (factual). d: deltas (ta (13, n), tas, ts). world: 'A' or 'B'.
    scale=0 must reproduce the factual state exactly (validation V3)."""
    s = {k: v.astype(np.float64).copy() for k, v in state.items()}
    dta, dtas, dts = scale * d["ta"].astype(np.float64), scale * d["tas"].astype(np.float64), scale * d["ts"].astype(np.float64)
    sp = s["sp"]
    col_q_old = np.zeros_like(sp)
    col_q_new = np.zeros_like(sp)
    dtv = {}
    edges = [1050.0] + [(a + b) / 2 for a, b in zip(LEVELS[:-1], LEVELS[1:])] + [0.0]   # layer edges (hPa)
    for k, lev in enumerate(LEVELS):
        p = lev * 100.0
        t_old, q_old = s[f"t_{lev}"], s[f"q_{lev}"]
        t_new = t_old - dta[k][None]
        qs_old, qs_new = qsat(t_old, p), qsat(t_new, p)
        if world == "B":
            q_new = q_old / qs_old * qs_new                              # relative humidity unchanged
        else:                                                            # specific humidity unchanged, capped so RH
            q_new = np.minimum(q_old, qs_new * np.maximum(1.0, q_old / qs_old))   # does not exceed its original max(1, RH)
        dtv[lev] = t_new * (1 + 0.608 * q_new) - t_old * (1 + 0.608 * q_old)
        s[f"t_{lev}"], s[f"q_{lev}"] = t_new, q_new
        dp = (edges[k] - edges[k + 1]) * 100.0
        col_q_old += q_old * dp
        col_q_new += q_new * dp
    # hydrostatic geopotential: dPhi(p) = Rd * integral_{p}^{sp} dTv dln p (trapezoid over levels; surface dTv = -dtas)
    lnp = {lev: np.log(lev * 100.0) for lev in LEVELS}
    dtv_sfc = -dtas[None] * np.ones_like(sp)
    lnsp = np.log(sp)
    for lev in LEVELS:
        acc = np.zeros_like(sp)
        above = lev * 100.0 < sp                                         # level above the ground
        # integrate from the surface up through the levels between sp and p
        prev_ln, prev_dtv = lnsp, dtv_sfc
        for lev2 in LEVELS:
            if lev2 < lev:
                break
            inside = lev2 * 100.0 < sp
            seg = np.where(inside, (prev_ln - lnp[lev2]) * 0.5 * (prev_dtv + dtv[lev2]), 0.0)
            acc += seg
            prev_ln = np.where(inside, lnp[lev2], prev_ln)
            prev_dtv = np.where(inside, dtv[lev2], prev_dtv)
        below = RD * dtv_sfc * (lnsp - lnp[lev])                        # below-ground levels: surface dTv, negative log
        s[f"z_{lev}"] = s[f"z_{lev}"] + np.where(above, RD * acc, below)
    rh2 = es(s["2d"] - 273.15) / es(s["2t"] - 273.15)
    excess = np.maximum(0.0, s["2d"] - s["2t"])                         # keep any original dewpoint excess unchanged
    s["2t"] = s["2t"] - dtas[None]
    if world == "B":
        a = np.log(rh2 * es(s["2t"] - 273.15) / 6.112)
        s["2d"] = 243.5 * a / (17.67 - a) + 273.15
    s["2d"] = np.minimum(s["2d"], s["2t"] + excess)
    s["skt"] = s["skt"] - dts[None]
    for k in ("stl1", "stl2"):
        s[k] = s[k] - dtas[None]
    ratio = np.where(col_q_old > 0, col_q_new / np.maximum(col_q_old, 1e-12), 1.0)
    s["tcw"] = s["tcw"] * ratio
    return {k: v.astype(np.float32) for k, v in s.items()}
