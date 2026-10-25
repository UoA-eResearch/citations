"""SDM-centroid variant (plan section 4): a random 1,000 species (seed 20261026) from the primary population.

Per species and period: MaxEnt-type model (elapid MaxentModel, default features) on WorldClim 2.1 bioclim (all 19, 10
arcmin). Presences are the period's thinned 5-arcmin cells; 10,000 background points are drawn with probability
proportional to that period's all-tracheophyte effort (thinned units per 10-arcmin cell), among land cells within
1,000 km of any of the species' pooled records. The binary range is the region's cells with suitability at or above
the 5th percentile of training-presence suitability; its centroid is the cell-area-weighted spherical mean.
Fitted on the observed assignment and on one noise-plus-effort null replicate (Pareto order sampling, D1).
-> results/tables/sdm_variant.parquet, results/tables/sdm_variant.json
"""
import json
import os
import sys
import time
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import rasterio  # noqa: E402
from sklearn.neighbors import BallTree  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
sys.path.insert(0, str(RUN.parents[1] / "tools"))
import velocity as V  # noqa: E402
from coverage import Coverage  # noqa: E402

T, WC = RUN / "results" / "tables", RUN / "data" / "ref" / "wc"
N_SPECIES, N_BG, RADIUS_KM, SEED = 1000, 10000, 1000.0, 20261026
G = {}


def load_env():
    layers = []
    for i in range(1, 20):
        with rasterio.open(WC / f"wc2.1_10m_bio_{i}.tif") as r:
            a = r.read(1).astype(np.float32)
            a[a == r.nodata] = np.nan
            layers.append(a)
    env = np.stack(layers)                                     # (19, 1080, 2160), row 0 = 90N
    land = np.all(np.isfinite(env), axis=0)
    rows, cols = np.nonzero(land)
    G.update(env=env, land_rows=rows, land_cols=cols, land_lat=90 - (rows + 0.5) / 6, land_lon=-180 + (cols + 0.5) / 6)
    G["land_tree_xyz"] = None


def to_rc(lat, lon):
    r = np.clip(np.floor((90 - lat) * 6).astype(int), 0, 1079)
    c = np.clip(np.floor((lon + 180) * 6).astype(int), 0, 2159)
    return r, c


def effort_grid():
    """Thinned all-tracheophyte units per period counted per 10-arcmin cell."""
    f = V.G["f"]
    W = 360 * f + 3
    code = (V.G["cy"] + 90 * f + 1) * W + (V.G["cx"] + 180 * f + 1)
    u = pd.DataFrame({"sp": V.G["sp"], "code": code, "per": V.G["per"]}).drop_duplicates()
    uy, ux = u.code.to_numpy() // W - 90 * f - 1, u.code.to_numpy() % W - 180 * f - 1
    r, c = to_rc((uy + 0.5) / f, (ux + 0.5) / f)
    for p in (1, 2):
        m = u.per.to_numpy() == p
        g = np.zeros((1080, 2160), np.float64)
        np.add.at(g, (r[m], c[m]), 1)
        G[f"eff{p}"] = g


def fit_range(pres_lat, pres_lon, p, region, rng):
    import elapid
    r, c = to_rc(pres_lat, pres_lon)
    Xp = G["env"][:, r, c].T
    Xp = Xp[np.all(np.isfinite(Xp), axis=1)]
    if len(Xp) < 5:
        return None, "fewer than 5 presences with climate data"
    rr, cc = G["land_rows"][region], G["land_cols"][region]
    w = G[f"eff{p}"][rr, cc]
    if w.sum() == 0:
        return None, "no effort in region"
    bg = rng.choice(len(region), N_BG, replace=True, p=w / w.sum())
    Xb = G["env"][:, rr[bg], cc[bg]].T
    X = np.vstack([Xp, Xb])
    y = np.r_[np.ones(len(Xp)), np.zeros(len(Xb))]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m = elapid.MaxentModel()
        m.fit(X, y)
        thr = np.percentile(m.predict(Xp), 5)
        suit = np.concatenate([m.predict(G["env"][:, rr[j:j + 50000], cc[j:j + 50000]].T)
                               for j in range(0, len(rr), 50000)])          # chunked: bounded memory per worker
    inr = suit >= thr
    if not inr.any():
        return None, "empty binary range"
    lat, lon = G["land_lat"][region][inr], G["land_lon"][region][inr]
    v = (V.unit(lat, lon) * np.cos(np.radians(lat))[:, None]).sum(0)
    return v / np.linalg.norm(v), None


def one(i):
    cy, cx, per, cidx, k, clat, clon, xyz, uy, ux = V.species_arrays(i)
    key = int(V.G["sp"][V.G["starts"][i]])
    rng = np.random.default_rng([SEED, 3, key])
    tree = BallTree(np.radians(np.c_[clat, clon]), metric="haversine")
    lat0, lat1 = clat.min() - 10, clat.max() + 10
    cand = np.flatnonzero((G["land_lat"] >= lat0) & (G["land_lat"] <= lat1))
    d, _ = tree.query(np.radians(np.c_[G["land_lat"][cand], G["land_lon"][cand]]), k=1)
    region = cand[d[:, 0] * V.R_EARTH <= RADIUS_KM]
    n, n1 = len(per), int((per == 1).sum())
    theta, _ = V.weights(cy, cx, per, uy, ux, cidx)
    u = np.random.default_rng([SEED, 2, key]).random(n)
    with np.errstate(divide="ignore", invalid="ignore"):
        keys = np.nan_to_num((u / (1 - u)) / theta, nan=np.inf, posinf=np.inf)
    null_p1 = np.zeros(n, bool)
    null_p1[np.argpartition(keys, n1 - 1)[:n1]] = True
    out = {"specieskey": key, "region_cells": int(len(region))}
    for name, P1 in (("obs", per == 1), ("null", null_p1)):
        cents = []
        for p, mask in ((1, P1), (2, ~P1)):
            cells = np.unique(cidx[mask])
            S, why = fit_range(clat[cells], clon[cells], p, region, rng)
            if S is None:
                out["drop"] = f"{name} P{p}: {why}"
                return out
            cents.append(S)
        a, b = cents
        out[f"v_sdm_{name}"] = float(np.arctan2(np.linalg.norm(np.cross(a, b)), a @ b) * V.R_EARTH / V.YEARS)
    return out


def main():
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    t0 = time.time()
    V.load("clean.parquet", 12, 1.0)
    load_env()
    effort_grid()
    nu = pd.read_parquet(T / "nulls_primary.parquet")
    pick = nu.sample(min(N_SPECIES, len(nu)), random_state=SEED)
    idx_of = {int(V.G["sp"][V.G["starts"][i]]): i for i in range(len(V.G["starts"]))}
    order = [idx_of[s] for s in pick.specieskey]
    print(f"loaded in {time.time() - t0:.0f}s; {len(order)} species", flush=True)
    cov = Coverage("sdm_variant", T / "coverage.json")
    rows = []
    with ProcessPoolExecutor(workers) as ex:
        for j, r in enumerate(ex.map(one, order, chunksize=2)):
            cov.attempt(r["specieskey"])
            if "drop" in r:
                cov.drop(r["specieskey"], r["drop"].split(": ", 1)[1])
            else:
                cov.ok(r["specieskey"])
            rows.append(r)
            if (j + 1) % 100 == 0:
                print(time.strftime("%H:%M:%S"), j + 1, flush=True)
    cov.save()
    df = pd.DataFrame(rows).merge(pick[["specieskey", "v_sph", "effort_med"]], on="specieskey")
    df.to_parquet(T / "sdm_variant.parquet", index=False)
    ok = df.dropna(subset=["v_sdm_obs", "v_sdm_null"])
    rng = np.random.default_rng(SEED)
    bs = [ok.iloc[rng.integers(len(ok), size=len(ok))] for _ in range(2000)]
    rat = [b.v_sdm_null.median() / b.v_sdm_obs.median() for b in bs]
    out = {"species_attempted": int(len(df)), "species_ok": int(len(ok)),
           "median_v_sdm_obs": round(float(ok.v_sdm_obs.median()), 3), "median_v_sdm_null": round(float(ok.v_sdm_null.median()), 3),
           "ratio": round(float(ok.v_sdm_null.median() / ok.v_sdm_obs.median()), 4),
           "ci": [round(float(np.percentile(rat, 2.5)), 4), round(float(np.percentile(rat, 97.5)), 4)],
           "same_species_point_median_obs": round(float(ok.v_sph.median()), 3),
           "same_species_point_median_effort_null": round(float(ok.effort_med.median()), 3)}
    (T / "sdm_variant.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
