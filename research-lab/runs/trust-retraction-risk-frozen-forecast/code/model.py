"""Fit, freeze and score the retraction-risk models (plan sections 4-5).

  model.py fit     fit on 2015-2019 articles with labels dated <= 2020-12-31: the primary gradient-boosted model, the
                   block ablations (without A; A, B, C alone) and the logistic regression. Writes data/models/*.pkl and
                   results/tables/model_hashes.json, to be committed BEFORE `score` reads any test label.
  model.py score   verify the hashes, score the 2021-2022 test cohort (labels as of the 2026-10-21 registry), and
                   compute E@k with a publisher-clustered bootstrap, leave-one-publisher-out refits, the ablations,
                   PR-AUC, top-decile calibration and the bias audit. Writes results/tables/h1_h2.json.
"""
import glob
import hashlib
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
FE, MD, T = RUN / "data" / "features", RUN / "data" / "models", RUN / "results" / "tables"
SEED = 20261022
TRAIN, TEST = (2015, 2019), (2021, 2022)
LABEL_CUT = 2020                      # training labels: retraction year <= 2020
NEG_SHARE = 0.05
A = ["src_rate", "host_rate", "src_growth", "src_missing", "stype", "oa", "field_c"]
B = ["nauth", "auth_prior_ret_n", "auth_prior_ret_max", "newcomer_share", "n_inst", "inst_max_rate", "n_countries"]
C = ["n_refs", "ref_unresolved_share", "ref_retracted_share", "ref_same_source_share", "ref_year_sd", "ref_recency_gap"]
CAT = ["stype", "field_c"]
SETS = {"full": A + B + C, "no_A": B + C, "A_only": A, "B_only": B, "C_only": C}
KS = [0.001, 0.01, 0.05, 0.10]


def load(years):
    parts = []
    for f in sorted(glob.glob(str(FE / "*.parquet"))):
        d = pd.read_parquet(f)
        parts.append(d[d.year.between(*years)])
    return pd.concat(parts, ignore_index=True)


def field_codes(train):
    top = train.field.value_counts().index[:20].tolist()
    return {f: i + 1 for i, f in enumerate(top)}


def prep(d, fmap):
    d = d.copy()
    d["field_c"] = d.field.map(fmap).fillna(0).astype(int)
    return d


def hgb(cols):
    from sklearn.ensemble import HistGradientBoostingClassifier
    return HistGradientBoostingClassifier(max_iter=300, early_stopping=True, validation_fraction=0.1,
                                          random_state=SEED, categorical_features=[c in CAT for c in cols])


def sample(train):
    rng = np.random.default_rng(SEED)
    y = ((train.ret > 0) & (train.ret <= LABEL_CUT)).to_numpy()
    keep = y | (rng.random(len(train)) < NEG_SHARE)
    w = np.where(y, 1.0, 1.0 / NEG_SHARE)[keep]
    return train[keep], y[keep], w


def fit_one(train, cols):
    X, y, w = sample(train)
    m = hgb(cols)
    m.fit(X[cols], y, sample_weight=w)
    return m


def fit_lr(train):
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler
    from sklearn.compose import ColumnTransformer
    from sklearn.impute import SimpleImputer
    X, y, w = sample(train)
    num = [c for c in SETS["full"] if c not in CAT]
    pre = ColumnTransformer([("num", make_pipeline(SimpleImputer(add_indicator=True), StandardScaler()), num),
                             ("cat", OneHotEncoder(handle_unknown="ignore"), CAT)])
    m = make_pipeline(pre, LogisticRegression(C=1.0, max_iter=2000))
    m.fit(X[SETS["full"]], y, logisticregression__sample_weight=w)
    return m


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def fit():
    MD.mkdir(parents=True, exist_ok=True)
    train = load(TRAIN)
    fmap = field_codes(train)
    train = prep(train, fmap)
    log = {"train_articles": len(train), "train_positive": int(((train.ret > 0) & (train.ret <= LABEL_CUT)).sum()),
           "field_codes": {str(k): v for k, v in fmap.items()}, "models": {}}
    for name, cols in SETS.items():
        m = fit_one(train, cols)
        p = MD / f"hgb_{name}.pkl"
        pickle.dump({"model": m, "cols": cols, "fmap": fmap}, open(p, "wb"))
        log["models"][p.name] = {"sha256": sha(p), "iterations": int(m.n_iter_)}
        print(name, m.n_iter_, flush=True)
    m = fit_lr(train)
    p = MD / "lr_full.pkl"
    pickle.dump({"model": m, "cols": SETS["full"], "fmap": fmap}, open(p, "wb"))
    log["models"][p.name] = {"sha256": sha(p)}
    json.dump(log, open(T / "model_hashes.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in log.items() if k != "field_codes"}, indent=1))


def enrichment(score, y, k):
    n = max(1, int(round(k * len(score))))
    top = np.argsort(-score, kind="stable")[:n]
    return (y[top].mean() / y.mean()) if y.mean() > 0 else float("nan"), top


def boot(score, y, clusters, k, B=1000):
    """Publisher-clustered bootstrap with Poisson(1) cluster weights; the top-k set is fixed from the full ranking."""
    n = max(1, int(round(k * len(score))))
    intop = np.zeros(len(score), dtype=bool)
    intop[np.argsort(-score, kind="stable")[:n]] = True
    cid, inv = np.unique(clusters, return_inverse=True)
    agg = np.stack([np.bincount(inv, minlength=len(cid)),
                    np.bincount(inv, weights=y, minlength=len(cid)),
                    np.bincount(inv, weights=intop, minlength=len(cid)),
                    np.bincount(inv, weights=y * intop, minlength=len(cid))])
    rng = np.random.default_rng(SEED)
    out = []
    for _ in range(B // 50):
        w = rng.poisson(1.0, size=(50, len(cid))).astype(np.float32)
        s = w @ agg.T                                       # 50 x 4
        out.append((s[:, 3] / np.maximum(s[:, 2], 1)) / (s[:, 1] / np.maximum(s[:, 0], 1)))
    e = np.concatenate(out)
    return [round(float(np.percentile(e, 2.5)), 3), round(float(np.percentile(e, 97.5)), 3)]


def clusters_of(d):
    h = d.host.to_numpy().astype(np.int64)
    return np.where(h > 0, h, -(np.arange(len(d)) + 1))     # no host: each article its own cluster


def evaluate(score, y, cl):
    out = {}
    for k in KS:
        e, _ = enrichment(score, y, k)
        out[f"E@{k:g}"] = {"enrichment": round(float(e), 3), "ci": boot(score, y, cl, k)}
    from sklearn.metrics import average_precision_score
    out["pr_auc"] = round(float(average_precision_score(y, score)), 5)
    out["base_rate"] = round(float(y.mean()), 6)
    return out


def predict(bundle, d):
    return bundle["model"].predict_proba(prep(d, bundle["fmap"])[bundle["cols"]])[:, 1]


def score():
    hashes = json.load(open(T / "model_hashes.json"))
    for name, h in hashes["models"].items():
        assert sha(MD / name) == h["sha256"], f"{name}: model changed after it was frozen"
    test = load(TEST)
    y = (test.ret > 0).to_numpy().astype(float)
    cl = clusters_of(test)
    res = {"test_articles": len(test), "test_retracted": int(y.sum()), "base_rate": round(float(y.mean()), 6),
           "models": {}}
    scores = {}
    for name in hashes["models"]:
        b = pickle.load(open(MD / name, "rb"))
        s = predict(b, test)
        scores[name] = s
        res["models"][name] = evaluate(s, y, cl)
        print(name, res["models"][name]["E@0.01"], flush=True)
    # calibration of the top decile (primary): predicted mean (rescaled for the 5% negative sample) vs observed
    s = scores["hgb_full.pkl"]
    top = np.argsort(-s)[: len(s) // 10]
    res["top_decile"] = {"observed_rate": round(float(y[top].mean()), 6), "mean_score": round(float(s[top].mean()), 6)}
    # leave-one-publisher-out: the host organisations with the most test-period retractions
    hosts = test.loc[y > 0].groupby("host").size().drop(0, errors="ignore").sort_values(ascending=False)
    train_all = load(TRAIN)
    fmap = {int(k): v for k, v in hashes["field_codes"].items()}
    res["lopo"] = {}
    for h in hosts.index[:3]:
        m = fit_one(prep(train_all[train_all.host != h], fmap), SETS["full"])
        te = test[test.host != h]
        yy = (te.ret > 0).to_numpy().astype(float)
        ss = m.predict_proba(prep(te, fmap)[SETS["full"]])[:, 1]
        e1, _ = enrichment(ss, yy, 0.01)
        res["lopo"][str(int(h))] = {"test_retractions_removed": int(hosts[h]), "E@0.01": round(float(e1), 3),
                                    "ci": boot(ss, yy, clusters_of(te), 0.01)}
        print("lopo", h, res["lopo"][str(int(h))], flush=True)
    # decisions
    full = res["models"]["hgb_full.pkl"]["E@0.01"]
    first = res["lopo"][str(int(hosts.index[0]))]["E@0.01"] if len(hosts) else None
    res["H1"] = {"E@1%": full["enrichment"], "ci": full["ci"], "lopo_top_publisher": first,
                 "verdict": "Supported" if full["ci"][0] >= 5 and (first or 0) >= 5 else
                 "Refuted" if full["ci"][1] < 5 else "Inconclusive"}
    noA = res["models"]["hgb_no_A.pkl"]["E@0.01"]
    res["H2"] = {"E@1%": noA["enrichment"], "ci": noA["ci"],
                 "verdict": "Supported" if noA["ci"][0] >= 3 else "Refuted" if noA["ci"][1] < 3 else "Inconclusive"}
    # bias audit (aggregate only): shares in the top 1% against shares of the cohort
    n1 = max(1, int(round(0.01 * len(s))))
    t1 = np.zeros(len(s), dtype=bool); t1[np.argsort(-s, kind="stable")[:n1]] = True
    audit = {}
    for col in ("country1", "host"):
        g = pd.DataFrame({"g": test[col].astype(str), "top": t1}).groupby("g").top.agg(["size", "sum"])
        g = g.sort_values("size", ascending=False).head(20)
        audit[col] = {k: {"cohort_share": round(r["size"] / len(s), 4), "top1_share": round(r["sum"] / n1, 4)}
                      for k, r in g.iterrows()}
    res["bias_audit"] = audit
    json.dump(res, open(T / "h1_h2.json", "w"), indent=1)
    print(json.dumps({k: res[k] for k in ("test_articles", "test_retracted", "base_rate", "H1", "H2")}, indent=1))


if __name__ == "__main__":
    {"fit": fit, "score": score}[sys.argv[1]]()
