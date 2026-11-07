"""Post hoc checks after the independent review (D3). -> results/tables/absorption_test.json

1. Absorption (finding 1). Synthetic worlds run through the study's own velocity.py: 300 species, 150 records each,
   ranges 40-50 N, 0-10 E, collecting effort uniform and identical in both periods. A share of species ("movers")
   really moves 1 degree north in period 2. If the effort null were a fixed-range null, it would leave the movers'
   observed velocity unexplained; instead its leave-one-species-out effort surface is built from the other species'
   records, which moved too.
2. Pareto order sampling (finding 2). For the smallest real primary-population species, the empirical inclusion
   probability of each record over 5,000 draws against the stated target n1 s1 / (n1 s1 + n2 s2).
"""
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
import velocity as V  # noqa: E402

T = RUN / "results" / "tables"


def world(share, seed=7):
    rng = np.random.default_rng(seed)
    rows, movers = [], set()
    for s in range(1, 301):
        n = 150
        per = rng.choice([1, 2], n)
        move = rng.random() < share
        if move:
            movers.add(s)
        lat = rng.uniform(40, 50, n) + np.where((per == 2) & move, 1.0, 0.0)
        rows.append(pd.DataFrame({"specieskey": s, "lat": lat, "lon": rng.uniform(0, 10, n), "period": per}))
    return pd.concat(rows), movers


def absorption():
    out = {}
    for name, share in (("none move", 0.0), ("all move 1 deg N", 1.0), ("half move 1 deg N", 0.5), ("20% move 1 deg N", 0.2)):
        df, movers = world(share)
        tmp = Path(tempfile.mkdtemp())
        df.to_parquet(tmp / "clean.parquet", index=False)
        V.D, V.T, V.NREP = tmp, tmp, 199
        V.G.clear()
        V.load("clean.parquet", 12, 1.0)
        obs = pd.DataFrame([r for r in map(V.observed, range(len(V.G["starts"]))) if r])
        res = pd.DataFrame([V.nulls(i) for i in range(len(V.G["starts"]))]).merge(obs, on="specieskey")
        res["mover"] = res.specieskey.isin(movers)
        grp = {"movers": res[res.mover], "stayers": res[~res.mover]} if 0 < share < 1 else {"all": res}
        out[name] = {g: {"species": int(len(d)), "observed_med": round(float(d.v_sph.median()), 2),
                         "noise_null_med": round(float(d.noise_med.median()), 2), "effort_null_med": round(float(d.effort_med.median()), 2),
                         "ratio_effort": round(float(d.effort_med.median() / d.v_sph.median()), 2),
                         "ratio_noise": round(float(d.noise_med.median() / d.v_sph.median()), 2),
                         "exceed_effort_p95": round(float((d.v_sph > d.effort_p95).mean()), 2),
                         "exceed_noise_p95": round(float((d.v_sph > d.noise_p95).mean()), 2)} for g, d in grp.items() if len(d)}
        print(name, out[name], flush=True)
    return out


def inclusion(n_species=5, draws=5000):
    V.D, V.T = RUN / "data", T
    V.G.clear()
    V.load("clean.parquet", 12, 1.0)
    nu = pd.read_parquet(T / "nulls_primary.parquet")
    small = nu.assign(n=nu.n1 + nu.n2).sort_values("n").head(n_species)
    idx_of = {int(V.G["sp"][V.G["starts"][i]]): i for i in range(len(V.G["starts"]))}
    res = []
    for key in small.specieskey:
        i = idx_of[int(key)]
        cy, cx, per, cidx, k, clat, clon, xyz, uy, ux = V.species_arrays(i)
        n, n1 = len(per), int((per == 1).sum())
        w, _ = V.weights(cy, cx, per, uy, ux, cidx)
        # stated target: inclusion probability n1 s1 / (n1 s1 + n2 s2) = n1 theta / (n1 theta + n2)
        n2 = n - n1
        with np.errstate(divide="ignore", invalid="ignore"):
            target = np.where(np.isinf(w), 1.0, n1 * w / (n1 * w + n2))
        rng = np.random.default_rng(20261107)
        hits = np.zeros(n)
        for _ in range(draws // 100):
            u = rng.random((100, n))
            with np.errstate(divide="ignore", invalid="ignore"):
                keys = np.nan_to_num((u / (1 - u)) / w[None, :], nan=np.inf, posinf=np.inf)
            sel = np.argpartition(keys, n1 - 1, axis=1)[:, :n1]
            np.add.at(hits, sel.ravel(), 1)
        emp = hits / draws
        res.append({"specieskey": int(key), "records": int(n), "n1": n1, "target_sum": round(float(target.sum()), 1),
                    "max_abs_dev": round(float(np.abs(emp - target).max()), 3), "mean_abs_dev": round(float(np.abs(emp - target).mean()), 3),
                    "corr": round(float(np.corrcoef(emp, target)[0, 1]), 3) if target.std() > 0 else None})
        print(res[-1], flush=True)
    share_small = float(((nu.n1 + nu.n2) < 100).mean())
    return {"species": res, "share_primary_species_under_100_records": round(share_small, 3)}


if __name__ == "__main__":
    out = {"absorption": absorption(), "pareto_inclusion": inclusion()}
    (T / "absorption_test.json").write_text(json.dumps(out, indent=1) + "\n")
    print("written")
