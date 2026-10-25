"""H1 and secondary analyses (plan sections 0, 2 and 4). Written before any real velocity was computed.

H1: ratio = median over species of the noise-plus-effort null median / median over species of observed velocity,
species bootstrap (2,000, seed 20261026). Supported if the lower bound >= 0.5; Refuted if the upper bound < 0.5;
Inconclusive otherwise.
-> results/tables/primary.json, results/tables/reproduction.csv
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"
SEED, B = 20261026, 2000
DARU = {"median_km_yr": 5.6, "species": 109242, "records": 16219436}


def boot(df, stat, rng):
    est = stat(df)
    n = len(df)
    bs = [stat(df.iloc[rng.integers(n, size=n)]) for _ in range(B)]
    return round(float(est), 4), [round(float(np.percentile(bs, 2.5)), 4), round(float(np.percentile(bs, 97.5)), 4)]


def ratio(null_col, obs_col="v_sph"):
    return lambda d: d[null_col].median() / d[obs_col].median()


def verdict(ci):
    return "Supported" if ci[0] >= 0.5 else "Refuted" if ci[1] < 0.5 else "Inconclusive"


def summarise(nu, rng, full=True):
    out = {"species": int(len(nu)), "median_observed_km_yr": round(float(nu.v_sph.median()), 3),
           "median_effort_null_km_yr": round(float(nu.effort_med.median()), 3),
           "median_noise_null_km_yr": round(float(nu.noise_med.median()), 3)}
    out["ratio_effort"], out["ci_effort"] = boot(nu, ratio("effort_med"), rng)
    if full:
        out["ratio_noise"], out["ci_noise"] = boot(nu, ratio("noise_med"), rng)
        out["exceed_effort_p95"], out["ci_exceed_effort_p95"] = boot(nu, lambda d: (d.v_sph > d.effort_p95).mean(), rng)
        out["exceed_noise_p95"] = round(float((nu.v_sph > nu.noise_p95).mean()), 4)
        out["median_excess_km_yr"], out["ci_median_excess"] = boot(nu, lambda d: (d.v_sph - d.effort_med).median(), rng)
    return out


def main():
    rng = np.random.default_rng(SEED)
    nu = pd.read_parquet(T / "nulls_primary.parquet")
    out = {"H1": summarise(nu, rng)}
    out["H1"]["verdict"] = verdict(out["H1"]["ci_effort"])
    out["direction"] = {"observed_share_poleward": round(float((nu.pole_km > 0).mean()), 4),
                        "effort_null_share_poleward": round(float(nu.effort_pole_pos.mean()), 4),
                        "noise_null_share_poleward": round(float(nu.noise_pole_pos.mean()), 4),
                        "median_observed_pole_km": round(float(nu.pole_km.median()), 2),
                        "median_effort_null_pole_km": round(float(nu.effort_pole_med.median()), 2)}
    band = pd.cut(nu.pooled_lat.abs(), [0, 23.5, 50, 90], labels=["tropical", "temperate", "boreal"], include_lowest=True)
    out["by_latitude_band"] = {str(b): summarise(g, rng, full=False) | {"exceed_effort_p95": round(float((g.v_sph > g.effort_p95).mean()), 4)}
                               for b, g in nu.groupby(band, observed=True)}
    kmin = np.minimum(nu.k1, nu.k2)
    cls = pd.cut(kmin, [10, 20, 50, np.inf], right=False, labels=["10-19", "20-49", ">=50"])
    out["by_cells"] = {str(c): summarise(g, rng, full=False) | {"exceed_effort_p95": round(float((g.v_sph > g.effort_p95).mean()), 4)}
                       for c, g in nu.groupby(cls, observed=True)}
    rob = {}
    for t in (20, 50):
        g = nu[kmin >= t]
        rob[f"threshold_{t}"] = summarise(g, rng, full=False)
    rob["arithmetic_centroids"] = {"species": int(len(nu))}
    rob["arithmetic_centroids"]["ratio_effort"], rob["arithmetic_centroids"]["ci_effort"] = boot(nu, ratio("effort_med_ari", "v_ari"), rng)
    for v in ("thin30", "eff30", "eff2deg", "no_r5"):
        p = T / f"nulls_{v}.parquet"
        rob[v] = summarise(pd.read_parquet(p), rng, full=False) if p.exists() else "not run"
    out["robustness"] = rob
    out["effort_default_records_share"] = round(float(nu.effort_default_records.sum() / (nu.n1 + nu.n2).sum()), 5)
    ob = pd.read_parquet(T / "observed_primary.parquet")
    rep = []
    for t in (1, 3, 5, 10, 20, 50):
        g = ob[(ob.k1 >= t) & (ob.k2 >= t)]
        rep.append({"min_cells_per_period": t, "species": len(g), "records": int((g.n1 + g.n2).sum()),
                    "median_v_km_yr": round(float(g.v_sph.median()), 3), "median_v_ari_km_yr": round(float(g.v_ari.median()), 3)})
    pd.DataFrame(rep).to_csv(T / "reproduction.csv", index=False)
    out["reproduction"] = {"daru": DARU, "ours": rep}
    (T / "primary.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
