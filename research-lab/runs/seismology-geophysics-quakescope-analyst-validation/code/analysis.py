"""Primary and secondary analyses (plan section 6). Inputs: data/matched.parquet (match.py) and
data/covariates.parquet (covariates.py). Outputs in results/tables/.

H1: matched ~ M + log10(max(dist, 1 km)) + (1 | station), variational Bayes; SD_p = SD over u ~ N(0, s_u^2) of
invlogit(b0 + bM*2.0 + bd*log10(30) + u), Monte Carlo 1e5; station-cluster bootstrap, 200 refits, seed 20261011.
H2: stations with >= 30 reference P picks; target = posterior-mean station effect; HistGradientBoostingRegressor on band
code, instrument code, sampling rate, log10 noise; GroupKFold(5) on 1-degree cells; pooled out-of-fold R^2; station
bootstrap of the out-of-fold predictions (2,000 draws)."""
import json
import multiprocessing as mp
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
SEED = 20261011
REF_M, REF_D = 2.0, 30.0
MIN_H1, MIN_H2 = 10, 30


def prepare(d, tol=0.5, phase="P"):
    d = d[d.loaded & d.in_stations & (d.phase == phase)].copy()
    d["y"] = d[f"matched_{tol}"].astype(float)
    d["M"] = d.mag.astype(float)
    d["logd"] = np.log10(np.maximum(d.dist_km.astype(float), 1.0))
    d = d.dropna(subset=["M", "logd"])
    n = d.groupby("netsta").size()
    return d[d.netsta.isin(n[n >= MIN_H1].index)]


def fit(d):
    from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
    m = BinomialBayesMixedGLM.from_formula("y ~ M + logd", {"station": "0 + C(netsta)"}, d)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        r = m.fit_vb(minim_opts={"maxiter": 5000})
    conv = not any("converge" in str(x.message).lower() for x in w)
    names = list(m.exog_names)
    beta = dict(zip(names, r.fe_mean))
    s_u = float(np.exp(r.vcp_mean[0]))
    levels = [n.split("[")[-1].rstrip("]") for n in m.exog_vc.names] if hasattr(m.exog_vc, "names") else None
    return dict(beta=beta, s_u=s_u, converged=conv, u_mean=np.asarray(r.vc_mean), u_sd=np.asarray(r.vc_sd), levels=levels,
                vc_names=list(getattr(m, "vc_names", [])))


def sd_p(beta, s_u, rng=None, n=100000):
    rng = rng or np.random.default_rng(SEED)
    eta = beta["Intercept"] + beta["M"] * REF_M + beta["logd"] * np.log10(REF_D)
    u = rng.normal(0, s_u, n)
    return float(np.std(1 / (1 + np.exp(-(eta + u)))))


def _boot(args):
    d, b = args
    rng = np.random.default_rng(SEED + 1 + b)
    st = d.netsta.unique()
    pick = rng.choice(st, size=len(st), replace=True)
    g = dict(tuple(d.groupby("netsta")))
    parts = [g[s].assign(netsta=f"{s}#{k}") for k, s in enumerate(pick)]
    f = fit(pd.concat(parts, ignore_index=True))
    return sd_p(f["beta"], f["s_u"]), f["converged"]


def h1(d, B=200, workers=8):
    f = fit(d)
    est = sd_p(f["beta"], f["s_u"])
    with mp.Pool(workers) as pool:
        res = pool.map(_boot, [(d, b) for b in range(B)])
    draws = np.array([x[0] for x in res])
    lo, hi = np.percentile(draws, [2.5, 97.5])
    verdict = "Supported" if (est >= 0.10 and lo >= 0.05) else "Refuted" if hi < 0.10 else "Inconclusive"
    return f, dict(SD_p=est, lower95=float(lo), upper95=float(hi), sigma_u_logit=f["s_u"], beta=f["beta"],
                   converged=f["converged"], boot_converged_share=float(np.mean([x[1] for x in res])),
                   n_picks=int(len(d)), n_stations=int(d.netsta.nunique()), verdict=verdict)


def station_effects(f, d):
    """Posterior mean and SD of each station's effect, keyed by station (level order of the vc design)."""
    names = f["vc_names"] or []
    if f["levels"]:
        keys = f["levels"]
    else:
        keys = sorted(d.netsta.unique())
    return pd.DataFrame({"netsta": keys, "u": f["u_mean"], "u_sd": f["u_sd"]}).set_index("netsta")


def cv_r2(X, y, groups, cat, seed=SEED, model="hgb"):
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.linear_model import LinearRegression
    from sklearn.model_selection import GroupKFold
    pred = np.full(len(y), np.nan)
    for tr, te in GroupKFold(n_splits=5).split(X, y, groups):
        if model == "hgb":
            mdl = HistGradientBoostingRegressor(random_state=seed, categorical_features=cat)
            mdl.fit(X.iloc[tr], y[tr])
            pred[te] = mdl.predict(X.iloc[te])
        else:
            Xd = pd.get_dummies(X, columns=[c for c, k in zip(X.columns, cat) if k], dummy_na=True).astype(float)
            Xd = Xd.fillna(Xd.iloc[tr].mean())
            mdl = LinearRegression().fit(Xd.iloc[tr], y[tr])
            pred[te] = mdl.predict(Xd.iloc[te])
    r2 = 1 - np.sum((y - pred) ** 2) / np.sum((y - y.mean()) ** 2)
    rng = np.random.default_rng(seed)
    bs = []
    for _ in range(2000):
        i = rng.integers(0, len(y), len(y))
        bs.append(1 - np.sum((y[i] - pred[i]) ** 2) / np.sum((y[i] - y[i].mean()) ** 2))
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return dict(R2=float(r2), lower95=float(lo), upper95=float(hi), n_stations=int(len(y))), pred


PRIMARY_X = ["band", "instrument", "sample_rate", "log_noise"]
SECONDARY_X = PRIMARY_X + ["network", "elevation", "n_ref"]


def design(eff, cov, d, cols):
    x = eff.join(cov, how="inner")
    x["n_ref"] = d.groupby("netsta").size().reindex(x.index)
    for c in ("band", "instrument", "network"):
        if c in x:
            x[c] = x[c].astype("category").cat.codes.replace(-1, np.nan) if c in cols else x[c]
    cat = [c in ("band", "instrument", "network") for c in cols]
    groups = (np.floor(x.latitude).astype(int).astype(str) + "_" + np.floor(x.longitude).astype(int).astype(str)).values
    return x[cols], x.u.values, groups, cat, x


def h2(f, d, cov):
    eff = station_effects(f, d)
    n = d.groupby("netsta").size()
    eff = eff[eff.index.isin(n[n >= MIN_H2].index)]
    X, y, groups, cat, x = design(eff, cov, d, PRIMARY_X)
    res, pred = cv_r2(X, y, groups, cat)
    res["verdict"] = "Supported" if (res["R2"] >= 0.5 and res["lower95"] >= 0.35) else "Refuted" if res["upper95"] < 0.5 else "Inconclusive"
    noise_share = float(np.mean(x.u_sd ** 2) / (np.var(x.u) + np.mean(x.u_sd ** 2)))
    res["noise_share"] = noise_share
    res["R2_reliability_corrected"] = float(res["R2"] / (1 - noise_share))
    lin, _ = cv_r2(X, y, groups, cat, model="linear")
    X2, y2, g2, cat2, _ = design(eff, cov, d, SECONDARY_X)
    sec, _ = cv_r2(X2, y2, g2, cat2)
    return res, dict(linear=lin, hgb_secondary_covariates=sec), x.assign(pred_oof=pred)


def main(*args):
    TAB.mkdir(parents=True, exist_ok=True)
    m = pd.read_parquet(RUN / "data" / "matched.parquet")
    cov = pd.read_parquet(RUN / "data" / "covariates.parquet").set_index("netsta")
    d = prepare(m)
    n30 = int((d.groupby("netsta").size() >= MIN_H2).sum())
    out = dict(n_stations_ge30=n30)
    if n30 < 100:
        out["verdict_H1"] = out["verdict_H2"] = "Inconclusive (insufficient stations)"
        json.dump(out, open(TAB / "primary.json", "w"), indent=1)
        print(out)
        return
    f, r1 = h1(d)
    out["H1"] = r1
    r2, sec2, x = h2(f, d, cov)
    out["H2"] = r2
    out["H2_secondary"] = sec2
    json.dump(out, open(TAB / "primary.json", "w"), indent=1, default=float)
    print(json.dumps(out, indent=1, default=float))
    # station reliability table: adjusted recall at the reference event, with posterior interval
    eff = station_effects(f, d)
    b = f["beta"]
    eta = b["Intercept"] + b["M"] * REF_M + b["logd"] * np.log10(REF_D)
    inv = lambda z: 1 / (1 + np.exp(-z))  # noqa: E731
    tab = eff.assign(recall_ref=inv(eta + eff.u), lower=inv(eta + eff.u - 1.96 * eff.u_sd), upper=inv(eta + eff.u + 1.96 * eff.u_sd),
                     n_ref=d.groupby("netsta").size(), raw_recall=d.groupby("netsta").y.mean()).join(cov, how="left")
    tab.to_csv(TAB / "station_reliability.csv")
    secondary(m, d, out)


def secondary(m, d, out):
    rows = []
    for tol in (0.2, 1.0):
        dd = prepare(m, tol=tol)
        f = fit(dd)
        rows.append(dict(analysis=f"P recall SD_p at tolerance {tol} s", value=sd_p(f["beta"], f["s_u"]), n=len(dd)))
    ds = prepare(m, phase="S")
    if ds.netsta.nunique() > 20:
        f = fit(ds)
        rows.append(dict(analysis="S recall SD_p (0.5 s)", value=sd_p(f["beta"], f["s_u"]), n=len(ds)))
    di = d[d.onset == "i"]
    f = fit(di)
    rows.append(dict(analysis="P recall SD_p, impulsive reference picks only", value=sd_p(f["beta"], f["s_u"]), n=len(di)))
    month = d.t_ref.dt.to_period("M")
    share = month.value_counts(normalize=True)
    if share.iloc[0] > 0.25:
        dm = d[month != share.index[0]]
        f = fit(dm)
        rows.append(dict(analysis=f"P recall SD_p excluding the busiest month {share.index[0]}", value=sd_p(f["beta"], f["s_u"]), n=len(dm)))
    rows.append(dict(analysis="pooled raw P recall (0.5 s)", value=float(d.y.mean()), n=len(d)))
    pd.DataFrame(rows).to_csv(TAB / "secondary.csv", index=False)
    mm = m[m.loaded & m.in_stations & (m.phase == "P") & m["matched_0.5"]]
    mm.assign(band=mm["cha_qs_0.5"].str[:2]).groupby("band")["resid_0.5"].agg(
        n="size", median="median", mad=lambda s: float(np.median(np.abs(s - np.median(s))))).to_csv(TAB / "timing_by_band.csv")
    print(pd.DataFrame(rows).to_string())


if __name__ == "__main__":
    main(*sys.argv[1:])
