"""H1-H3 and secondaries (plan sections 0 and 6). Written before any model was trained.

Per target, splitter and model: retrospective RMSE = mean over repeats; prospective RMSE on the primary set (or the
plan's fallback definition, recorded in selection.json); signed bias = retrospective - prospective. Bootstrap over
targets (2,000, seed 20261026).
-> results/tables/primary.json, results/tables/bias_long.csv, coverage.json stage fits
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
sys.path.insert(0, str(RUN.parents[1] / "tools"))
from coverage import Coverage  # noqa: E402

SEED, B, PRIMARY_MODEL = 20261026, 2000, "rf"
MODELS = ["rf", "lgbm", "svr", "knn", "mlp"]
SPLITTERS = ["random", "scaffold", "cluster", "document", "author", "assay", "time"]


def load():
    rows_r, rows_p, cov = [], [], Coverage("fits", T / "coverage.json")
    for f in sorted((D / "fits").glob("*.json")):
        r = json.loads(f.read_text())
        for x in r["retro"]:
            rows_r.append({"target": r["target"], **x})
            cov.attempt((r["target"], x["splitter"], x["repeat"], x["model"])); cov.ok((r["target"], x["splitter"], x["repeat"], x["model"]))
        for k, v in r["notes"].items():
            for m in MODELS:
                u = (r["target"], k, m)
                cov.attempt(u); cov.drop(u, v.split(":")[0])
        for x in r["pros"]:
            rows_p.append({"target": r["target"], **x})
    cov.save()
    return pd.DataFrame(rows_r), pd.DataFrame(rows_p)


def boot_med(x, rng, f=np.median):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    bs = [f(x[rng.integers(len(x), size=len(x))]) for _ in range(B)]
    return round(float(f(x)), 4), [round(float(np.percentile(bs, 2.5)), 4), round(float(np.percentile(bs, 97.5)), 4)]


def kendall_rank(a, b):
    from scipy.stats import kendalltau
    return float(kendalltau(a, b).statistic)


def main():
    sel = json.loads((T / "selection.json").read_text())
    pset = sel["primary_definition"]
    rr, pp = load()
    retro = rr.groupby(["target", "splitter", "model"]).agg(retro_rmse=("rmse", "mean"), retro_spearman=("spearman", "mean"),
                                                            retro_auc=("auc", "mean"), retro_lo=("rmse", "min"),
                                                            retro_hi=("rmse", "max"), repeats=("rmse", "size")).reset_index()
    out = {"primary_set": pset}
    rng = np.random.default_rng(SEED)
    longs = []
    for s in sorted(pp.set.unique()):
        pr = pp[pp.set == s].rename(columns={"rmse": "pros_rmse", "spearman": "pros_spearman", "auc": "pros_auc", "n": "pros_n"})
        m = retro.merge(pr[["target", "model", "pros_rmse", "pros_spearman", "pros_auc", "pros_n", "nn_sim_median"]],
                        on=["target", "model"])
        m["bias"] = m.retro_rmse - m.pros_rmse
        m["covers"] = (m.retro_lo <= m.pros_rmse) & (m.pros_rmse <= m.retro_hi)
        longs.append(m.assign(set=s))
    long = pd.concat(longs, ignore_index=True)
    long.to_csv(T / "bias_long.csv", index=False)
    P = long[(long.set == pset) & (long.model == PRIMARY_MODEL)]
    res = {}
    for sp in SPLITTERS:
        x = P[P.splitter == sp]
        if not len(x):
            continue
        med, ci = boot_med(x.bias, rng)
        amed, aci = boot_med(x.bias.abs(), rng)
        res[sp] = {"targets": int(len(x)), "median_bias": med, "ci": ci, "median_abs_bias": amed, "abs_ci": aci,
                   "share_covering_truth": round(float(x.covers.mean()), 3)}
    out["bias_rf"] = res
    h1 = {}
    for sp in ("random", "scaffold"):
        r = res[sp]
        h1[sp] = "Supported" if (r["median_bias"] <= -0.25 and r["ci"][1] < 0) else "Refuted" if r["ci"][0] > -0.25 else "Inconclusive"
    out["H1"] = {"by_splitter": h1, "verdict": "Supported" if all(v == "Supported" for v in h1.values())
                 else "Refuted" if all(v == "Refuted" for v in h1.values()) else "Inconclusive"}
    h2 = {}
    for sp in ("document", "author"):
        r = res.get(sp)
        h2[sp] = "not run" if r is None else ("Supported" if r["abs_ci"][1] <= 0.12 else "Refuted" if r["abs_ci"][0] > 0.12 else "Inconclusive")
    out["H2"] = {"by_splitter": h2, "verdict": "Supported" if all(v == "Supported" for v in h2.values())
                 else "Refuted" if all(v == "Refuted" for v in h2.values()) else "Inconclusive"}
    # H3: Kendall tau between retrospective and prospective rankings of the five models, per target
    L = long[long.set == pset]
    taus = []
    for (t, sp), g in L.groupby(["target", "splitter"]):
        if g.model.nunique() == len(MODELS):
            g = g.set_index("model").loc[MODELS]
            taus.append({"target": t, "splitter": sp, "tau": kendall_rank(g.retro_rmse, g.pros_rmse)})
    tau = pd.DataFrame(taus)
    tau.to_csv(T / "tau_long.csv", index=False)
    mt = {sp: boot_med(tau[tau.splitter == sp].tau, rng, np.mean) for sp in SPLITTERS if (tau.splitter == sp).any()}
    w = tau.pivot(index="target", columns="splitter", values="tau")
    dd = (w["document"] - w["scaffold"]).dropna()
    dmean, dci = boot_med(dd, rng, np.mean)
    s_mean, d_mean, d_ci = mt["scaffold"][0], mt["document"][0], mt["document"][1]
    h3 = ("Supported" if (s_mean <= 0.6 and d_mean >= 0.8 and dci[0] > 0)
          else "Refuted" if (dci[1] <= 0 or d_ci[1] < 0.8) else "Inconclusive")
    out["H3"] = {"mean_tau": {k: {"mean": v[0], "ci": v[1]} for k, v in mt.items()},
                 "document_minus_scaffold": {"mean": dmean, "ci": dci, "targets": int(len(dd))}, "verdict": h3}
    # secondaries: all models and sets
    out["median_bias_all"] = (long.groupby(["set", "model", "splitter"]).bias.median().round(4).unstack().to_dict(orient="index"))
    out["median_bias_all"] = {f"{k[0]}|{k[1]}": v for k, v in out["median_bias_all"].items()}
    out["median_prospective_rmse_rf"] = round(float(P.drop_duplicates("target").pros_rmse.median()), 4)
    P2 = P.copy()
    P2["sim_tercile"] = pd.qcut(P2.nn_sim_median.rank(method="first"), 3, labels=["low", "mid", "high"])
    out["bias_by_similarity_rf"] = P2.groupby(["sim_tercile", "splitter"], observed=True).bias.median().round(4).unstack().to_dict(orient="index")
    (T / "primary.json").write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps({k: out[k] for k in ("primary_set", "bias_rf", "H1", "H2", "H3")}, indent=1, default=str))


if __name__ == "__main__":
    main()
