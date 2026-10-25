"""Observed centroid velocities and the two nulls (plan sections 2-3).

One function, `shift`, computes thinned per-period centroids and velocities for a batch of period assignments; the
observed velocity is `shift` applied to the true assignment, so observed and null share every step.

usage: velocity.py VARIANT [WORKERS]
  primary   5-arcmin thinning, 1-degree effort, data/clean.parquet
  thin30    30-arcmin thinning, 1-degree effort
  eff30     5-arcmin thinning, 30-arcmin effort
  eff2deg   5-arcmin thinning, 2-degree effort
  no_r5     primary settings on data/clean_no_r5.parquet
-> results/tables/observed_<variant>.parquet (every species with >= 1 thinned cell per period; observed only)
   results/tables/nulls_<variant>.parquet (species with >= 10 thinned cells per period; observed and null summaries)
"""
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
sys.path.insert(0, str(RUN.parents[1] / "tools"))
from coverage import Coverage  # noqa: E402

R_EARTH, YEARS, NREP, BATCH, MIN_CELLS, SEED = 6371.0088, 28.0, 999, 64, 10, 20261026
KM_PER_DEG = np.pi * R_EARTH / 180
VARIANTS = {"primary": ("clean.parquet", 12, 1.0), "thin30": ("clean.parquet", 2, 1.0),
            "eff30": ("clean.parquet", 12, 2.0), "eff2deg": ("clean.parquet", 12, 0.5),
            "no_r5": ("clean_no_r5.parquet", 12, 1.0)}
G = {}


def load(src, f, fe):
    t = pq.read_table(D / src, columns=["specieskey", "lat", "lon", "period"])
    sp = t["specieskey"].to_numpy()
    o = np.argsort(sp, kind="stable")
    sp = sp[o]
    lat, lon = t["lat"].to_numpy()[o], t["lon"].to_numpy()[o]
    per = t["period"].to_numpy()[o].astype(np.int8)
    cy, cx = np.floor(lat * f).astype(np.int64), np.floor(lon * f).astype(np.int64)
    cx = np.where(cx >= 180 * f, cx - 360 * f, cx)                        # lon = 180 joins the -180 column
    starts = np.r_[0, np.flatnonzero(np.diff(sp)) + 1]
    G.update(sp=sp, cy=cy, cx=cx, per=per, starts=starts, ends=np.r_[starts[1:], len(sp)], f=f, fe=fe)
    # effort: thinned species x cell units per period, by effort cell (cell centre -> effort grid)
    W = 360 * f + 3
    code = (cy + 90 * f + 1) * W + (cx + 180 * f + 1)
    u = pd.DataFrame({"sp": sp, "code": code, "per": per}).drop_duplicates()
    uy, ux = u.code.to_numpy() // W - 90 * f - 1, u.code.to_numpy() % W - 180 * f - 1
    u["ecell"] = effort_cell(uy, ux)
    E = u.groupby(["ecell", "per"]).size().unstack(fill_value=0).reindex(columns=[1, 2], fill_value=0)
    G["E"] = {1: E[1].to_dict(), 2: E[2].to_dict()}
    G["Etot"] = {1: float(E[1].sum()), 2: float(E[2].sum())}


def effort_cell(cy, cx):
    f, fe = G["f"], G["fe"]
    ey = np.floor((cy + 0.5) / f * fe).astype(np.int64)
    ex = np.floor((cx + 0.5) / f * fe).astype(np.int64)
    return ey * 100000 + ex


def unit(lat, lon):
    la, lo = np.radians(lat), np.radians(lon)
    return np.c_[np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)]


def shift(cidx, k, clat, clon, xyz, P1):
    """P1: (b, n) bool, True = record assigned to period 1. Returns per-assignment spherical velocity, arithmetic
    velocity, poleward displacement (km, spherical centroids), cells in P1 and P2."""
    b, n = P1.shape
    flat = (np.arange(b)[:, None] * k + cidx[None, :])
    inc1 = np.zeros(b * k, bool); inc1[flat[P1]] = True; inc1 = inc1.reshape(b, k)
    inc2 = np.zeros(b * k, bool); inc2[flat[~P1]] = True; inc2 = inc2.reshape(b, k)
    k1, k2 = inc1.sum(1), inc2.sum(1)
    out = []
    for inc, kk in ((inc1, k1), (inc2, k2)):
        S = inc.astype(np.float64) @ xyz
        S /= np.linalg.norm(S, axis=1, keepdims=True)
        alat = inc @ clat / kk
        alon = inc @ clon / kk
        out.append((S, alat, alon))
    (S1, a1, o1), (S2, a2, o2) = out
    ang = np.arctan2(np.linalg.norm(np.cross(S1, S2), axis=1), np.einsum("ij,ij->i", S1, S2))
    v_sph = ang * R_EARTH / YEARS
    p1, p2, l1, l2 = np.radians(a1), np.radians(a2), np.radians(o1), np.radians(o2)
    h = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin((l2 - l1) / 2) ** 2
    v_ari = 2 * R_EARTH * np.arcsin(np.sqrt(np.clip(h, 0, 1))) / YEARS
    lat1, lat2 = np.degrees(np.arcsin(S1[:, 2])), np.degrees(np.arcsin(S2[:, 2]))
    pole = (np.abs(lat2) - np.abs(lat1)) * KM_PER_DEG
    return v_sph, v_ari, pole, k1, k2, (S1, S2)


def species_arrays(i):
    s0, s1 = G["starts"][i], G["ends"][i]
    f = G["f"]
    cy, cx, per = G["cy"][s0:s1], G["cx"][s0:s1], G["per"][s0:s1]
    W = 360 * f + 3
    ucode, cidx = np.unique((cy + 90 * f + 1) * W + (cx + 180 * f + 1), return_inverse=True)
    uy, ux = ucode // W - 90 * f - 1, ucode % W - 180 * f - 1
    clat, clon = (uy + 0.5) / f, (ux + 0.5) / f
    return cy, cx, per, cidx.ravel(), len(ucode), clat, clon, unit(clat, clon), uy, ux


def observed(i):
    cy, cx, per, cidx, k, clat, clon, xyz, _, _ = species_arrays(i)
    if not ((per == 1).any() and (per == 2).any()):
        return None
    vs, va, po, k1, k2, (S1, S2) = shift(cidx, k, clat, clon, xyz, (per == 1)[None, :])
    if k1[0] == 0 or k2[0] == 0:
        return None
    Sp = S1[0] + S2[0]
    bearing = np.degrees(np.arctan2(*bearing_terms(S1[0], S2[0]))) % 360
    return {"specieskey": int(G["sp"][G["starts"][i]]), "n1": int((per == 1).sum()), "n2": int((per == 2).sum()),
            "k1": int(k1[0]), "k2": int(k2[0]), "v_sph": float(vs[0]), "v_ari": float(va[0]), "pole_km": float(po[0]),
            "bearing": float(bearing), "pooled_lat": float(np.degrees(np.arcsin(Sp[2] / np.linalg.norm(Sp))))}


def bearing_terms(a, b):
    la1, lo1 = np.arcsin(a[2]), np.arctan2(a[1], a[0])
    la2, lo2 = np.arcsin(b[2]), np.arctan2(b[1], b[0])
    y = np.sin(lo2 - lo1) * np.cos(la2)
    x = np.cos(la1) * np.sin(la2) - np.sin(la1) * np.cos(la2) * np.cos(lo2 - lo1)
    return y, x


def weights(cy, cx, per, uy, ux, cidx):
    """Odds weight per record, theta = s1 / s2: P1's share of its total effort in the record's effort cell over P2's,
    leave-one-species-out. Pareto order sampling with these odds targets inclusion probabilities
    n1 s1 / (n1 s1 + n2 s2), the chance that a record from a fixed range in that cell was collected in P1 (D1)."""
    ec = effort_cell(cy, cx)
    own = pd.DataFrame({"ecell": effort_cell(uy[cidx], ux[cidx]), "cell": cidx, "per": per}).drop_duplicates()
    own = own.groupby(["ecell", "per"]).size().to_dict()
    E, Et = G["E"], G["Etot"]
    e1 = np.array([E[1].get(c, 0) - own.get((c, 1), 0) for c in ec], float)
    e2 = np.array([E[2].get(c, 0) - own.get((c, 2), 0) for c in ec], float)
    s1, s2 = e1 / Et[1], e2 / Et[2]
    with np.errstate(divide="ignore", invalid="ignore"):
        theta = np.where(s1 + s2 > 0, s1 / s2, 1.0)          # s2 = 0 -> inf (P1 first); s1 = 0 -> 0 (P2)
    return theta, int((s1 + s2 == 0).sum())


def nulls(i):
    cy, cx, per, cidx, k, clat, clon, xyz, uy, ux = species_arrays(i)
    key = int(G["sp"][G["starts"][i]])
    n, n1 = len(per), int((per == 1).sum())
    w, nodefault = weights(cy, cx, per, uy, ux, cidx)
    res = {"specieskey": key, "effort_default_records": nodefault}
    for name in ("noise", "effort"):
        vs_all, va_all, po_all = [], [], []
        for r0 in range(0, NREP, BATCH):
            b = min(BATCH, NREP - r0)
            rng = np.random.default_rng([SEED, 0 if name == "noise" else 1, key, r0])
            if name == "noise":
                keys = rng.random((b, n))
            else:                                           # Pareto order sampling (Rosen 1997) with odds theta
                u = rng.random((b, n))
                with np.errstate(divide="ignore", invalid="ignore"):
                    keys = (u / (1 - u)) / w[None, :]
                keys = np.nan_to_num(keys, nan=np.inf, posinf=np.inf)
            sel = np.argpartition(keys, n1 - 1, axis=1)[:, :n1]
            P1 = np.zeros((b, n), bool)
            P1[np.arange(b)[:, None], sel] = True
            vs, va, po, _, _, _ = shift(cidx, k, clat, clon, xyz, P1)
            vs_all.append(vs); va_all.append(va); po_all.append(po)
        vs, va, po = np.concatenate(vs_all), np.concatenate(va_all), np.concatenate(po_all)
        res.update({f"{name}_med": float(np.median(vs)), f"{name}_p5": float(np.percentile(vs, 5)),
                    f"{name}_p95": float(np.percentile(vs, 95)), f"{name}_med_ari": float(np.median(va)),
                    f"{name}_pole_med": float(np.median(po)), f"{name}_pole_pos": float((po > 0).mean())})
    return res


def main():
    variant = sys.argv[1]
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    src, f, fe = VARIANTS[variant]
    t0 = time.time()
    load(src, f, fe)
    nsp = len(G["starts"])
    print(f"{variant}: {len(G['sp']):,} records, {nsp:,} species, loaded in {time.time() - t0:.0f}s", flush=True)
    obs = [r for r in map(observed, range(nsp)) if r]
    ob = pd.DataFrame(obs)
    ob.to_parquet(T / f"observed_{variant}.parquet", index=False)
    print(f"observed: {len(ob):,} species with >= 1 cell per period ({time.time() - t0:.0f}s)", flush=True)
    idx_of = {int(G["sp"][G["starts"][i]]): i for i in range(nsp)}
    pop = ob[(ob.k1 >= MIN_CELLS) & (ob.k2 >= MIN_CELLS)]
    order = sorted((idx_of[s] for s in pop.specieskey), key=lambda i: -(G["ends"][i] - G["starts"][i]))
    cov = Coverage(f"nulls_{variant}", T / "coverage.json")
    rows = []
    with ProcessPoolExecutor(workers) as ex:
        for j, r in enumerate(ex.map(nulls, order, chunksize=4)):
            cov.attempt(r["specieskey"]); cov.ok(r["specieskey"])
            rows.append(r)
            if (j + 1) % 2000 == 0:
                print(time.strftime("%H:%M:%S"), j + 1, "of", len(order), flush=True)
    cov.save()
    nu = pop.merge(pd.DataFrame(rows), on="specieskey")
    nu.to_parquet(T / f"nulls_{variant}.parquet", index=False)
    print(f"== done {variant}: {len(nu):,} species in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
