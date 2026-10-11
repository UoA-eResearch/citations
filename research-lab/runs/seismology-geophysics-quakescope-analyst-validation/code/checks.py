"""Post-outcome diagnostics and exploratory analyses (deviations.md D4). Written after the primary results were seen;
nothing here changes a preregistered verdict. Outputs in results/tables/checks/.

  python code/checks.py vb SEED [METHOD]  VB refit of the H1 model with fixed start seed; records the optimiser's message
  python code/checks.py aghq K START      independent maximum-likelihood fit by adaptive Gauss-Hermite quadrature
  python code/checks.py misc              level alignment, busiest month, reference recall, SD_p at other reference events
  python code/checks.py h2x               H2 exploratory: single covariates, location, AGHQ station effects
  python code/checks.py falsepick         the plan's exploratory false-pick proxy
  python code/checks.py falsepick_nn      post-hoc variant: isolation tested against the 5 nearest stations
"""
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit, logsumexp

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402

RUN = A.RUN
OUT = A.TAB / "checks"
RAW = RUN / "data" / "raw"


def data():
    return A.prepare(pd.read_parquet(RUN / "data" / "matched.parquet"))


def dump(obj, name):
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(obj, open(OUT / name, "w"), indent=1, default=float)
    print(json.dumps(obj, indent=1, default=float), flush=True)


# --- 1. VB refits with fixed starting values -------------------------------------------------------------------
def vb(seed, method="BFGS"):
    from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
    d = data()
    m = BinomialBayesMixedGLM.from_formula("y ~ M + logd", {"station": "0 + C(netsta)"}, d)
    t = time.time()
    opts = {"maxiter": 5000} if method == "BFGS" else {"maxiter": 50000, "maxfun": 100000}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = m.fit_vb(fit_method=method, minim_opts=opts, rng=int(seed))
    mm = r.optim_retvals
    beta = dict(zip(m.exog_names, r.fe_mean))
    s_u = float(np.exp(r.vcp_mean[0]))
    dump(dict(seed=int(seed), method=method, success=bool(mm.success), message=str(mm.message), nit=int(mm.nit),
              grad_norm=float(np.linalg.norm(mm.jac)), grad_max=float(np.max(np.abs(mm.jac))), neg_elbo=float(mm.fun),
              beta=beta, sigma_u=s_u, SD_p=A.sd_p(beta, s_u), minutes=(time.time() - t) / 60), f"vb_seed{seed}_{method}.json")


# --- 2. Maximum likelihood by adaptive Gauss-Hermite quadrature (as lme4::glmer nAGQ) --------------------------
class AGHQ:
    def __init__(self, d, K):
        self.y = d.y.values.astype(float)
        self.X = np.column_stack([np.ones(len(d)), d.M.values, d.logd.values])
        self.st, self.levels = pd.factorize(d.netsta, sort=True)
        self.S = len(self.levels)
        self.z, self.w = np.polynomial.hermite.hermgauss(K)
        self.u = np.zeros(self.S)

    def _sum(self, v):
        return np.bincount(self.st, weights=v, minlength=self.S)

    def modes(self, eta0, s2):
        """Conditional modes by Newton steps clipped to +-1 (the objective is concave in u). Warm start from the last
        evaluation; if that has not converged after 100 steps, restart from zero."""
        for start in (self.u.copy(), np.zeros(self.S)):
            u = start
            for _ in range(200):
                p = expit(eta0 + u[self.st])
                g = self._sum(self.y - p) - u / s2
                H = self._sum(p * (1 - p)) + 1 / s2
                step = np.clip(g / H, -1, 1)
                u = u + step
                if np.max(np.abs(step)) < 1e-10:
                    break
            if np.max(np.abs(step)) < 1e-10:
                break
        p = expit(eta0 + u[self.st])
        H = self._sum(p * (1 - p)) + 1 / s2
        self.u = u
        return u, H

    def negll(self, th):
        beta, s2 = th[:3], np.exp(2 * th[3])
        eta0 = self.X @ beta
        u, H = self.modes(eta0, s2)
        sc = np.sqrt(2 / H)
        terms = []
        for zk, wk in zip(self.z, self.w):
            uk = u + sc * zk
            eta = eta0 + uk[self.st]
            ll = self._sum(self.y * eta - np.logaddexp(0, eta))
            terms.append(np.log(wk) + zk ** 2 + ll - uk ** 2 / (2 * s2))
        li = np.log(sc) + logsumexp(np.vstack(terms), axis=0) - 0.5 * np.log(2 * np.pi * s2)
        return -float(np.sum(li))


def aghq(K, sname):
    """One AGHQ fit: K nodes (1 = Laplace), start 'vb' (the primary VB estimate) or 'zero'. Tolerances in log-likelihood
    units (fatol 1e-3) and parameters (xatol 1e-4)."""
    K = int(K)
    d = data()
    prim = json.load(open(A.TAB / "primary.json"))["H1"]
    x0 = {"vb": [prim["beta"]["Intercept"], prim["beta"]["M"], prim["beta"]["logd"], np.log(prim["sigma_u_logit"])],
          "zero": [0.0, 0.0, 0.0, 0.0]}[sname]
    g = AGHQ(d, K)
    t = time.time()
    calls = [0]

    def f(th):
        calls[0] += 1
        v = g.negll(th)
        if calls[0] % 50 == 0:
            print(calls[0], round(v, 3), np.round(th, 4), flush=True)
        return v
    r = minimize(f, np.array(x0, float), method="Nelder-Mead", options={"xatol": 1e-4, "fatol": 1e-3, "maxiter": 3000, "maxfev": 3000})
    beta = dict(zip(["Intercept", "M", "logd"], r.x[:3]))
    s_u = float(np.exp(r.x[3]))
    res = dict(K=K, start=sname, success=bool(r.success), message=str(r.message), nfev=int(r.nfev), negll=float(r.fun),
               beta=beta, sigma_u=s_u, SD_p=A.sd_p(beta, s_u), minutes=(time.time() - t) / 60)
    if K == 15 and sname == "vb":
        u, H = g.modes(g.X @ r.x[:3], s_u ** 2)
        OUT.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"netsta": g.levels, "u_ml": u, "u_ml_sd": 1 / np.sqrt(H)}).to_csv(OUT / "aghq_effects.csv", index=False)
    dump(res, f"aghq_K{K}_{sname}.json")


# --- 3. Alignment and descriptive checks ------------------------------------------------------------------------
def misc():
    from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
    d = data()
    m = BinomialBayesMixedGLM.from_formula("y ~ M + logd", {"station": "0 + C(netsta)"}, d)
    vc = [n.split("[")[-1].rstrip("]") for n in m.vc_names]
    keys = sorted(d.netsta.unique())
    rel = pd.read_csv(A.TAB / "station_reliability.csv")
    prim = json.load(open(A.TAB / "primary.json"))["H1"]
    b, s_u = prim["beta"], prim["sigma_u_logit"]
    month = d.t_ref.dt.to_period("M").value_counts(normalize=True)
    eta_ref = b["Intercept"] + b["M"] * A.REF_M + b["logd"] * np.log10(A.REF_D)
    alt = {}
    for M, D in ((1.5, 30), (1.5, 60), (2.0, 60), (2.5, 30), (1.5, 90)):
        e = b["Intercept"] + b["M"] * M + b["logd"] * np.log10(D)
        u = np.random.default_rng(A.SEED).normal(0, s_u, 100000)
        alt[f"M{M}_{D}km"] = dict(recall_typical=float(expit(e)), SD_p=float(np.std(expit(e + u))))
    r30 = rel[rel.n_ref >= 30]
    q = r30.recall_ref.quantile([0.05, 0.1, 0.25, 0.5, 0.75, 0.9]).to_dict()
    sp = rel[["u", "raw_recall"]].corr(method="spearman").iloc[0, 1]
    dump(dict(vc_levels_equal_sorted=vc == keys, n_levels=len(vc), table_order_equal=list(rel.netsta) == keys,
              spearman_u_raw_recall=float(sp), busiest_month=str(month.index[0]), busiest_month_share=float(month.iloc[0]),
              recall_at_reference_typical_station=float(expit(eta_ref)), sd_p_other_reference_events=alt,
              recall_ref_quantiles_ge30=q, share_recall_ref_below_0_80_ge30=float((r30.recall_ref < 0.80).mean()),
              share_recall_ref_below_0_90_ge30=float((r30.recall_ref < 0.90).mean()),
              n_picks_per_station_ge30=r30.n_ref.describe().to_dict(),
              icc_latent=float(s_u ** 2 / (s_u ** 2 + np.pi ** 2 / 3)),
              pooled_recall_by_network=d.assign(net=d.netsta.str[:2]).groupby("net").y.agg(["mean", "size"]).to_dict("index"),
              pooled_recall_by_source=d.groupby("source").y.agg(["mean", "size"]).to_dict("index") if "source" in d else None),
         "misc.json")


# --- 4. H2 exploratory ------------------------------------------------------------------------------------------
def h2x():
    d = data()
    cov = pd.read_parquet(RUN / "data" / "covariates.parquet").set_index("netsta")
    cov.loc[~np.isfinite(cov.log_noise) & cov.log_noise.notna(), "log_noise"] = np.nan
    rel = pd.read_csv(A.TAB / "station_reliability.csv").set_index("netsta")
    n = d.groupby("netsta").size()
    eff = rel.loc[rel.index.isin(n[n >= A.MIN_H2].index), ["u", "u_sd"]]
    rows = []

    def run(label, cols, e=eff, model="hgb"):
        X, y, g, cat, x = A.design(e, cov, d, cols)
        r, _ = A.cv_r2(X, y, g, cat, model=model)
        rows.append(dict(analysis=label, model=model, **r))
        print(rows[-1], flush=True)
        return x

    for c in A.PRIMARY_X:
        run(f"single covariate: {c}", [c])
    run("network only", ["network"])
    run("location only (latitude, longitude)", ["latitude", "longitude"])
    run("primary covariates + location", A.PRIMARY_X + ["latitude", "longitude"])
    run("primary + secondary + location", A.SECONDARY_X + ["latitude", "longitude"])
    ml = pd.read_csv(OUT / "aghq_effects.csv").set_index("netsta").rename(columns={"u_ml": "u", "u_ml_sd": "u_sd"})
    run("primary covariates, ML (AGHQ) station effects as target", A.PRIMARY_X, e=ml.loc[ml.index.isin(eff.index)])
    pd.DataFrame(rows).to_csv(OUT / "h2_exploratory.csv", index=False)
    x = eff.join(cov, how="inner")
    x["noise_tercile"] = pd.qcut(x.log_noise, 3, labels=["quiet", "middle", "noisy"])
    desc = {c: x.groupby(c, observed=True).u.agg(["mean", "std", "size"]).round(3).to_dict("index")
            for c in ("band", "instrument", "sample_rate", "network", "noise_tercile")}
    desc["noise_missing"] = x[x.log_noise.isna()].u.agg(["mean", "std", "size"]).to_dict()
    desc["spearman_u_log_noise"] = float(x[["u", "log_noise"]].corr(method="spearman").iloc[0, 1])
    dump(desc, "h2_descriptive.json")


# --- 5. False-pick proxy (plan section 6, exploratory) ----------------------------------------------------------
def falsepick():
    """Catalogue P picks with conf >= 0.5 at a station that have (a) no reference pick of either phase at that station
    within 1 s and (b) no catalogue P pick at any other CI/NC/BK station within 10 s. Rate per loaded station-day in the
    sampled months."""
    ms = json.load(open(RUN / "data" / "months.json"))
    ref = pd.read_parquet(RUN / "data" / "reference_picks.parquet", columns=["net", "sta", "t_ref"])
    ref["netsta"] = ref.net + "." + ref.sta
    av = pd.concat([pd.read_parquet(RAW / "availability" / f"{n}.parquet", columns=["tid", "date", "status"]) for n in ("CI", "NC", "BK")])
    av = av[av.status == "loaded"]
    av["netsta"] = av.tid.str.rsplit(".", n=1).str[0]
    av["date"] = pd.to_datetime(av.date)
    av = av.drop_duplicates(["netsta", "date"])
    cnt = {}
    for y, mo in ms:
        t0 = pd.Timestamp(year=y, month=mo, day=1)
        t1 = t0 + pd.offsets.MonthBegin(1)
        ps = []
        for net in ("CI", "NC", "BK"):
            fs = sorted((RAW / "western" / "picks" / f"network={net}" / f"year={y}" / f"month={mo:02d}").glob("*.parquet"))
            for f in fs:
                p = pd.read_parquet(f, columns=["tid", "pha", "peak", "conf"])
                ps.append(p[p.pha == "P"])
        p = pd.concat(ps, ignore_index=True)
        p = p[(p.peak >= t0) & (p.peak < t1)]
        p["netsta"] = p.tid.str.rsplit(".", n=1).str[0]
        p = p.drop_duplicates(["netsta", "peak"])  # one pick per station and time across location/band codes
        sta, lev = pd.factorize(p.netsta)
        tus = ((p.peak - t0).dt.total_seconds().values * 1e6).astype(np.int64)
        BIG = np.int64(10 ** 13)
        allt = np.sort(tus)
        key = np.sort(sta.astype(np.int64) * BIG + tus)
        k = sta.astype(np.int64) * BIG + tus
        W = 10 * 10 ** 6
        tot = np.searchsorted(allt, tus + W, "right") - np.searchsorted(allt, tus - W, "left")
        same = np.searchsorted(key, k + W, "right") - np.searchsorted(key, k - W, "left")
        isolated = (tot - same) == 0
        r = ref[(ref.t_ref >= t0) & (ref.t_ref < t1) & ref.netsta.isin(lev)]
        rk = np.sort(pd.Index(lev).get_indexer(r.netsta).astype(np.int64) * BIG
                     + ((r.t_ref - t0).dt.total_seconds().values * 1e6).astype(np.int64))
        V = 1 * 10 ** 6
        referenced = (np.searchsorted(rk, k + V, "right") - np.searchsorted(rk, k - V, "left")) > 0
        hi = p.conf.values >= 0.5
        g = pd.DataFrame({"netsta": p.netsta.values, "n_p05": hi, "n_false_proxy": hi & isolated & ~referenced,
                          "n_isolated": hi & isolated})
        s = g.groupby("netsta").sum()
        days = av[(av.date >= t0) & (av.date < t1)].groupby("netsta").size().rename("days")
        s = s.join(days, how="outer").fillna(0)
        cnt[(y, mo)] = s
        print(y, mo, len(p), int(s.n_false_proxy.sum()), flush=True)
    allst = pd.concat(cnt.values()).groupby(level=0).sum()
    allst["rate_per_day"] = allst.n_false_proxy / allst.days.replace(0, np.nan)
    rel = pd.read_csv(A.TAB / "station_reliability.csv").set_index("netsta")
    x = allst.join(rel[["u", "n_ref"]], how="inner")
    x30 = x[x.n_ref >= 30]
    OUT.mkdir(parents=True, exist_ok=True)
    allst.to_csv(OUT / "false_pick_proxy_by_station.csv")
    dump(dict(stations=int((allst.days > 0).sum()), station_days=float(allst.days.sum()),
              p_picks_conf05=float(allst.n_p05.sum()), isolated=float(allst.n_isolated.sum()),
              false_proxy=float(allst.n_false_proxy.sum()),
              rate_per_day_pooled=float(allst.n_false_proxy.sum() / allst.days.sum()),
              rate_per_day_quantiles_h2_stations=x30.rate_per_day.quantile([0.1, 0.25, 0.5, 0.75, 0.9]).to_dict(),
              spearman_u_rate_h2_stations=float(x30[["u", "rate_per_day"]].corr(method="spearman").iloc[0, 1]),
              n_h2_stations=int(len(x30))), "false_pick_proxy.json")


def falsepick_nn(K=5):
    """Post-hoc variant (D4): the preregistered isolation test is met by chance (about one P pick per second across
    CI/NC/BK). Here a catalogue P pick (conf >= 0.5) is isolated if none of the station's K nearest stations that have
    picks that month has a P pick within 10 s; unreferenced as before (no reference pick at the station within 1 s)."""
    ms = json.load(open(RUN / "data" / "months.json"))
    ref = pd.read_parquet(RUN / "data" / "reference_picks.parquet", columns=["net", "sta", "t_ref"])
    ref["netsta"] = ref.net + "." + ref.sta
    stc = pd.read_parquet(RAW / "stations.parquet")
    stc["netsta"] = stc.network_code + "." + stc.station_code
    stc = stc.groupby("netsta")[["latitude", "longitude"]].mean()
    BIG, W, V = np.int64(10 ** 13), 10 * 10 ** 6, 1 * 10 ** 6
    parts = []
    for y, mo in ms:
        t0 = pd.Timestamp(year=y, month=mo, day=1)
        t1 = t0 + pd.offsets.MonthBegin(1)
        ps = []
        for net in ("CI", "NC", "BK"):
            for f in sorted((RAW / "western" / "picks" / f"network={net}" / f"year={y}" / f"month={mo:02d}").glob("*.parquet")):
                p = pd.read_parquet(f, columns=["tid", "pha", "peak", "conf"])
                ps.append(p[p.pha == "P"])
        p = pd.concat(ps, ignore_index=True)
        p = p[(p.peak >= t0) & (p.peak < t1)]
        p["netsta"] = p.tid.str.rsplit(".", n=1).str[0]
        p = p.drop_duplicates(["netsta", "peak"])
        p = p[p.netsta.isin(stc.index)]
        sta, lev = pd.factorize(p.netsta)
        tus = ((p.peak - t0).dt.total_seconds().values * 1e6).astype(np.int64)
        key = np.sort(sta.astype(np.int64) * BIG + tus)
        xy = stc.loc[lev]
        lat, lon = np.deg2rad(xy.latitude.values), np.deg2rad(xy.longitude.values)
        dx = (lon[:, None] - lon[None, :]) * np.cos((lat[:, None] + lat[None, :]) / 2)
        dist = 6371 * np.hypot(dx, lat[:, None] - lat[None, :])
        np.fill_diagonal(dist, np.inf)
        nn = np.argsort(dist, axis=1)[:, :K]
        nn_km = np.take_along_axis(dist, nn, axis=1)
        hi = p.conf.values >= 0.5
        idx = np.flatnonzero(hi)
        s_hi, t_hi = sta[idx].astype(np.int64), tus[idx]
        found = np.zeros(len(idx), bool)
        for k in range(K):
            nb = nn[s_hi, k].astype(np.int64)
            c = np.searchsorted(key, nb * BIG + t_hi + W, "right") - np.searchsorted(key, nb * BIG + t_hi - W, "left")
            found |= c > 0
        r = ref[(ref.t_ref >= t0) & (ref.t_ref < t1) & ref.netsta.isin(lev)]
        rk = np.sort(pd.Index(lev).get_indexer(r.netsta).astype(np.int64) * BIG
                     + ((r.t_ref - t0).dt.total_seconds().values * 1e6).astype(np.int64))
        kk = s_hi * BIG + t_hi
        referenced = (np.searchsorted(rk, kk + V, "right") - np.searchsorted(rk, kk - V, "left")) > 0
        g = pd.DataFrame({"netsta": lev[sta[idx]], "n_p05": 1, "n_unref": ~referenced, "n_isolated_nn": ~found,
                          "n_false_proxy_nn": ~found & ~referenced, "nn_km_median": nn_km[sta[idx]].mean(axis=1)})
        parts.append(g.groupby("netsta").agg(n_p05=("n_p05", "sum"), n_unref=("n_unref", "sum"), n_isolated_nn=("n_isolated_nn", "sum"),
                                             n_false_proxy_nn=("n_false_proxy_nn", "sum"), nn_km=("nn_km_median", "mean")))
        print(y, mo, len(idx), int((~found & ~referenced).sum()), flush=True)
    allst = pd.concat(parts).groupby(level=0).agg(n_p05=("n_p05", "sum"), n_unref=("n_unref", "sum"), n_isolated_nn=("n_isolated_nn", "sum"),
                                                 n_false_proxy_nn=("n_false_proxy_nn", "sum"), nn_km=("nn_km", "mean"))
    days = pd.read_csv(OUT / "false_pick_proxy_by_station.csv").set_index("netsta").days
    allst = allst.join(days, how="left")
    allst["rate_per_day_nn"] = allst.n_false_proxy_nn / allst.days.replace(0, np.nan)
    allst.to_csv(OUT / "false_pick_proxy_nn_by_station.csv")
    rel = pd.read_csv(A.TAB / "station_reliability.csv").set_index("netsta")
    x30 = allst.join(rel[["u", "n_ref"]], how="inner")
    x30 = x30[x30.n_ref >= 30]
    dump(dict(K=K, p_picks_conf05=float(allst.n_p05.sum()), unreferenced_share=float(allst.n_unref.sum() / allst.n_p05.sum()),
              isolated_nn_share=float(allst.n_isolated_nn.sum() / allst.n_p05.sum()),
              false_proxy_nn=float(allst.n_false_proxy_nn.sum()),
              false_proxy_nn_share_of_p05=float(allst.n_false_proxy_nn.sum() / allst.n_p05.sum()),
              rate_per_day_nn_pooled=float(allst.n_false_proxy_nn.sum() / allst.days.sum()),
              rate_per_day_nn_quantiles_h2_stations=x30.rate_per_day_nn.quantile([0.1, 0.25, 0.5, 0.75, 0.9]).to_dict(),
              spearman_u_rate_nn_h2_stations=float(x30[["u", "rate_per_day_nn"]].corr(method="spearman").iloc[0, 1]),
              spearman_rate_nn_nn_km_h2_stations=float(x30[["nn_km", "rate_per_day_nn"]].corr(method="spearman").iloc[0, 1]),
              n_h2_stations=int(len(x30))), "false_pick_proxy_nn.json")


if __name__ == "__main__":
    cmd = sys.argv[1]
    {"vb": lambda: vb(*sys.argv[2:]), "aghq": lambda: aghq(*sys.argv[2:]), "misc": misc, "h2x": h2x, "falsepick": falsepick,
     "falsepick_nn": falsepick_nn}[cmd]()
