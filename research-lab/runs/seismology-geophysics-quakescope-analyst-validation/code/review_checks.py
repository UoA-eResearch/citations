"""Review-requested analyses (review/review.md; deviations.md D5). All post hoc; the preregistered verdicts are unchanged
and reported first. Outputs in results/tables/review/.

  python code/review_checks.py zero        loaded station-days with zero catalogue picks (issue 1): H1 refit with a
                                           200-refit bootstrap excluding them; a second variant excluding days with
                                           < 10% of the station's median daily pick count (point estimate); H2 and tails
  python code/review_checks.py weights     H1 model with analyst weight class and onset as covariates (issue 8)
  python code/review_checks.py misc        quadrature SD_p, bootstrap share < 0.10, empirical SDs, local spatial
                                           correlation, regional boxes, recall by period and weight, NCEDC status A share,
                                           noise outliers (issues 3-6, 8, 9, 13, 18)
  python code/review_checks.py misses      decomposition of unmatched H1 picks by distance to the nearest P pick (17)
  python code/review_checks.py falsepick   false-pick proxy caveats: thresholds, diurnal cycle, neighbours loaded,
                                           by network (issue 7)
  python code/review_checks.py table       station_reliability.csv extended with the flags and the variant estimates
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import expit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402

RUN = A.RUN
RAW = RUN / "data" / "raw"
OUT = RUN / "results" / "tables" / "review"
PRIMARY_TAB = RUN / "results" / "tables"
MONTHS = json.load(open(RUN / "data" / "months.json"))
BOXES = {  # regional boxes for the descriptive shares (lat_min, lat_max, lon_min, lon_max)
    "Los Angeles basin": (33.6, 34.4, -118.7, -117.6),
    "Long Valley and Mammoth": (37.4, 38.0, -119.3, -118.6),
    "San Francisco Bay Area": (37.2, 38.3, -122.8, -121.6),
}


def dump(obj, name):
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(obj, open(OUT / name, "w"), indent=1, default=float)
    print(json.dumps(obj, indent=1, default=float), flush=True)


def station_days():
    """npks summed over location codes per (netsta, date) for loaded rows, within the sampled months; with each
    station's median daily count over those days."""
    a = pd.concat([pd.read_parquet(RAW / "availability" / f"{n}.parquet", columns=["tid", "date", "status", "npks"])
                   for n in ("CI", "NC", "BK")])
    a = a[a.status == "loaded"].copy()
    a["netsta"] = a.tid.str.rsplit(".", n=1).str[0]
    a["date"] = pd.to_datetime(a.date)
    ym = set(map(tuple, MONTHS))
    a = a[[(y, m) in ym for y, m in zip(a.date.dt.year, a.date.dt.month)]]
    a["npks"] = a.npks.astype("float")
    sd = a.groupby(["netsta", "date"]).npks.sum(min_count=1).rename("npks").reset_index()
    sd["med"] = sd.groupby("netsta").npks.transform("median")
    return sd


def flagged():
    d = A.prepare(pd.read_parquet(RUN / "data" / "matched.parquet"))
    sd = station_days()
    d = d.merge(sd, on=["netsta", "date"], how="left")
    d["zero_day"] = d.npks.fillna(0) == 0
    d["low_day"] = d.npks.fillna(0) < 0.10 * d.med.fillna(0)
    return d, sd


def refilter(d):
    n = d.groupby("netsta").size()
    return d[d.netsta.isin(n[n >= A.MIN_H1].index)].copy()


def tails(f, d):
    eff = A.station_effects(f, d)
    b = f["beta"]
    eta = b["Intercept"] + b["M"] * A.REF_M + b["logd"] * np.log10(A.REF_D)
    r = expit(eta + eff.u)
    n = d.groupby("netsta").size().reindex(eff.index)
    r30 = r[n >= A.MIN_H2]
    return dict(typical=float(expit(eta)), median=float(r30.median()), q10=float(r30.quantile(0.10)),
                q05=float(r30.quantile(0.05)), below80=float((r30 < 0.80).mean()), below90=float((r30 < 0.90).mean()),
                empirical_sd_recall_ge30=float(r30.std()), empirical_sd_recall_all=float(r.std()),
                n_stations=int(len(eff)), n_ge30=int(len(r30)), n_picks=int(len(d))), eff.assign(recall_ref=r)


def zero():
    d, sd = flagged()
    ld = sd[sd.netsta.isin(d.netsta.unique())]
    base = dict(loaded_station_days=int(len(sd)), zero_pick_station_day_share=float((sd.npks.fillna(0) == 0).mean()),
                under5_station_day_share=float((sd.npks.fillna(0) < 5).mean()),
                h1_station_days_zero_share=float((ld.npks.fillna(0) == 0).mean()),
                picks_on_zero_days=int(d.zero_day.sum()), recall_on_zero_days=float(d.y[d.zero_day].mean()),
                picks_on_low_days=int(d.low_day.sum()), recall_on_low_days=float(d.y[d.low_day].mean()),
                pooled_recall_all=float(d.y.mean()), pooled_recall_excl_zero=float(d.y[~d.zero_day].mean()),
                pooled_recall_excl_low=float(d.y[~d.low_day].mean()),
                recall_by_day_count={k: float(v) for k, v in d.groupby(pd.cut(d.npks.fillna(0), [-1, 0, 2, 5, 10, 20, 50, 1000, 1e9]),
                                                                          observed=True).y.mean().items()})
    base["recall_by_day_count"] = {str(k): v for k, v in base["recall_by_day_count"].items()}
    dump(base, "zero_days_descriptive.json")
    # variant B first (point estimate, one fit), then variant A with the bootstrap
    dB = refilter(d[~d.low_day])
    fB = A.fit(dB)
    tB, effB = tails(fB, dB)
    dump(dict(SD_p=A.sd_p(fB["beta"], fB["s_u"]), sigma_u=fB["s_u"], beta=fB["beta"], converged=fB["converged"], **tB),
         "h1_excl_low_days_point.json")
    effB.to_csv(OUT / "effects_excl_low_days.csv")
    dA = refilter(d[~d.zero_day])
    A.TAB = OUT / "excl_zero"  # h1() writes its bootstrap draws to A.TAB; keep the primary file untouched
    A.TAB.mkdir(parents=True, exist_ok=True)
    fA, rA = A.h1(dA)
    tA, effA = tails(fA, dA)
    res = dict(H1=rA, tails=tA)
    dump(res, "h1_excl_zero_days.json")
    effA.to_csv(OUT / "effects_excl_zero_days.csv")
    cov = pd.read_parquet(RUN / "data" / "covariates.parquet").set_index("netsta")
    cov.loc[~np.isfinite(cov.log_noise) & cov.log_noise.notna(), "log_noise"] = np.nan
    r2, sec2, _ = A.h2(fA, dA, cov)
    res["H2"] = r2
    res["H2_secondary"] = sec2
    dump(res, "h1_excl_zero_days.json")


def weights():
    d, _ = flagged()
    q = {1.0: "0", 0.8: "1", 0.75: "1", 0.5: "2", 0.25: "3", 0.2: "3"}
    d["q"] = d.weight.round(2).map(q).fillna("other")
    d["on"] = d.onset.where(d.onset.isin(["i", "e"]), "other")
    from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
    import warnings
    m = BinomialBayesMixedGLM.from_formula("y ~ M + logd + C(q) + C(on)", {"station": "0 + C(netsta)"}, d)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = m.fit_vb(minim_opts={"maxiter": 5000}, rng=1)
    beta = dict(zip(m.exog_names, r.fe_mean))
    s_u = float(np.exp(r.vcp_mean[0]))
    # linear predictor at the reference event: (a) best picks (class 0, impulsive); (b) averaged over the observed mix
    X = pd.DataFrame(m.exog, columns=m.exog_names)
    contrib = X.drop(columns=["Intercept", "M", "logd"]).values @ np.array([beta[c] for c in X.columns if c not in ("Intercept", "M", "logd")])
    eta0 = beta["Intercept"] + beta["M"] * A.REF_M + beta["logd"] * np.log10(A.REF_D)
    u = np.random.default_rng(A.SEED).normal(0, s_u, 20000)
    mix = np.random.default_rng(A.SEED).choice(contrib, 2000)
    p_mix = expit(eta0 + mix[None, :] + u[:, None]).mean(axis=1)
    dump(dict(beta=beta, sigma_u=s_u, sigma_u_primary=json.load(open(PRIMARY_TAB / "primary.json"))["H1"]["sigma_u_logit"],
              SD_p_best_picks=float(np.std(expit(eta0 + u))), typical_recall_best_picks=float(expit(eta0)),
              SD_p_observed_mix=float(np.std(p_mix)), typical_recall_observed_mix=float(expit(eta0 + mix).mean()),
              converged=bool(r.optim_retvals.success), message=str(r.optim_retvals.message),
              recall_by_source_weight=d.groupby(["source", d.weight.round(2)]).y.agg(["mean", "size"]).reset_index().to_dict("records"),
              recall_by_onset=d.groupby("on").y.agg(["mean", "size"]).to_dict("index")), "h1_weight_onset_covariates.json")


def misc():
    prim = json.load(open(PRIMARY_TAB / "primary.json"))["H1"]
    b, s_u = prim["beta"], prim["sigma_u_logit"]
    eta = b["Intercept"] + b["M"] * A.REF_M + b["logd"] * np.log10(A.REF_D)
    z, w = np.polynomial.hermite.hermgauss(200)
    p = expit(eta + np.sqrt(2) * s_u * z)
    m1, m2 = (w * p).sum() / np.sqrt(np.pi), (w * p ** 2).sum() / np.sqrt(np.pi)
    draws = pd.read_csv(PRIMARY_TAB / "h1_bootstrap_draws.csv").SD_p
    mc = [A.sd_p(b, s_u, rng=np.random.default_rng(s)) for s in range(1, 6)]
    rel = pd.read_csv(PRIMARY_TAB / "station_reliability.csv").set_index("netsta")
    r30 = rel[rel.n_ref >= A.MIN_H2].copy()
    # local spatial correlation of station effects (5 nearest, nearest, 10 nearest)
    lat, lon = np.deg2rad(r30.latitude.values), np.deg2rad(r30.longitude.values)
    dist = 6371 * np.hypot((lon[:, None] - lon[None, :]) * np.cos((lat[:, None] + lat[None, :]) / 2), lat[:, None] - lat[None, :])
    np.fill_diagonal(dist, np.inf)
    order = np.argsort(dist, axis=1)
    loc = {f"r_u_mean_{k}nn": float(np.corrcoef(r30.u.values, r30.u.values[order[:, :k]].mean(axis=1))[0, 1]) for k in (1, 5, 10)}
    loc["median_5nn_mean_km"] = float(np.median(np.take_along_axis(dist, order[:, :5], axis=1).mean(axis=1)))
    # plain (ungrouped) 5-fold CV with and without location
    d = A.prepare(pd.read_parquet(RUN / "data" / "matched.parquet"))
    cov = pd.read_parquet(RUN / "data" / "covariates.parquet").set_index("netsta")
    cov.loc[~np.isfinite(cov.log_noise) & cov.log_noise.notna(), "log_noise"] = np.nan
    eff = rel.loc[r30.index, ["u", "u_sd"]]
    plain = {}
    for label, cols in (("location only", ["latitude", "longitude"]), ("primary", A.PRIMARY_X),
                        ("primary + location", A.PRIMARY_X + ["latitude", "longitude"])):
        X, y, g, cat, _ = A.design(eff, cov, d, cols)
        rng = np.random.default_rng(A.SEED)
        groups = rng.permutation(len(y))  # every station its own group, in random order: plain 5-fold CV
        plain[label] = A.cv_r2(X, y, groups, cat)[0]
    # regional shares (explicit boxes), on the primary effects
    def region(row):
        for k, (a, bb, c, e) in BOXES.items():
            if a <= row.latitude <= bb and c <= row.longitude <= e:
                return k
        return "elsewhere"
    r30["region"] = r30.apply(region, axis=1)
    q10 = r30.recall_ref.quantile(0.10)
    regions = r30.groupby("region").recall_ref.agg(n="size", median="median", share_below_q10=lambda s: float((s < q10).mean())).to_dict("index")
    # recall by period and data centre (training overlap of PhaseNet `original` with NCEDC picks)
    dd = d.assign(period=np.where(d.t_ref.dt.year <= 2017, "2010-2017", "2018-2024"))
    period = {f"{k[0]} {k[1]}": float(v) for k, v in dd.groupby(["source", "period"]).y.mean().items()}
    # NCEDC status A share among M >= 1.5 events in the sampled months
    st = []
    for y in sorted({y for y, _ in MONTHS}):
        f = RAW / "catalogues" / f"ncedc_{y}.ehpcsv"
        if f.exists():
            c = pd.read_csv(f, low_memory=False)
            st.append(c.assign(_y=y))
    cat_info = None
    if st:
        c = pd.concat(st)
        tcol = [x for x in c.columns if x.lower().startswith("datetime") or x.lower() == "time"]
        mcol = [x for x in c.columns if x.lower() in ("magnitude", "mag")]
        scol = [x for x in c.columns if "review" in x.lower() or x.lower() == "status"]
        if tcol and mcol and scol:
            t = pd.to_datetime(c[tcol[0]], errors="coerce", format="mixed")
            keep = [(yy, mm) in set(map(tuple, MONTHS)) for yy, mm in zip(t.dt.year, t.dt.month)]
            cc = c[np.array(keep) & (pd.to_numeric(c[mcol[0]], errors="coerce") >= 1.5)]
            cat_info = dict(columns=[tcol[0], mcol[0], scol[0]], n_events=int(len(cc)),
                            status_share=cc[scol[0]].value_counts(normalize=True).to_dict())
        else:
            cat_info = dict(columns_found=list(c.columns))
    # noise covariate outliers and window counts
    cv = cov.loc[cov.index.isin(r30.index)].copy()
    cv["windows"] = pd.to_numeric(cv.noise_note.str.extract(r"(\d+) windows")[0], errors="coerce")
    noise = dict(above_minus6=int((cv.log_noise > -6).sum()), below_minus8_7=int((cv.log_noise < -8.7).sum()),
                 full_180_windows=int((cv.windows == 180).sum()), under_60_windows=int((cv.windows < 60).sum()),
                 missing=int(cv.log_noise.isna().sum()))
    band = r30.assign(cha=r30.read_band).groupby(["network", "cha"]).recall_ref.agg(["median", "size"]).reset_index().to_dict("records")
    dump(dict(SD_p_quadrature=float(np.sqrt(m2 - m1 ** 2)), SD_p_mc_primary=prim["SD_p"], SD_p_mc_other_seeds=mc,
              boot_share_below_0_10=float((draws < 0.10).mean()), boot_sd=float(draws.std()), boot_min=float(draws.min()),
              boot_max=float(draws.max()), empirical_sd_recall_ge30=float(r30.recall_ref.std()),
              empirical_sd_recall_all=float(rel.recall_ref.std()),
              empirical_sd_recall_ge100=float(rel[rel.n_ref >= 100].recall_ref.std()),
              u_skew_ge30=float(r30.u.skew()), local_spatial=loc, plain_kfold=plain, boxes=BOXES, regions=regions,
              recall_by_source_period=period, ncedc_catalogue=cat_info, noise=noise, recall_by_network_readband=band),
         "misc.json")


def misses():
    """For each unmatched H1 reference P pick: is it on a zero-pick station-day, and how far is the nearest catalogue P
    pick at the same station (any location or band)?"""
    import match as Mt
    d, _ = flagged()
    u = d[d.y == 0].copy()
    u["nearest_s"] = np.nan
    for net in ("CI", "NC", "BK"):
        for y, mo in MONTHS:
            r = u[(u.netsta.str.split(".").str[0] == net) & (u.t_ref.dt.year == y) & (u.t_ref.dt.month == mo)]
            if r.empty:
                continue
            p = Mt.load_picks(net, y, mo)
            p = p[p.pha == "P"]
            g = {k: np.sort(v.peak.values.astype("datetime64[ns]").astype(np.int64)) for k, v in p.groupby("netsta")}
            near = []
            for ns, t in zip(r.netsta, r.t_ref.values.astype("datetime64[ns]").astype(np.int64)):
                a = g.get(ns)
                if a is None or len(a) == 0:
                    near.append(np.inf)
                    continue
                i = np.searchsorted(a, t)
                c = [abs(a[j] - t) for j in (i - 1, i) if 0 <= j < len(a)]
                near.append(min(c) / 1e9)
            u.loc[r.index, "nearest_s"] = near
            print(net, y, mo, len(r), flush=True)
    bins = pd.cut(u.nearest_s, [0, 1.0, 3.0, 300.0, np.inf], right=False, labels=["0.5-1 s", "1-3 s", "3-300 s", "none within 300 s"])
    dec = dict(unmatched=int(len(u)), on_zero_pick_days=float(u.zero_day.mean()),
               by_nearest_not_zero_day=bins[~u.zero_day].value_counts(normalize=True).mul((~u.zero_day).mean()).to_dict(),
               by_nearest_all=bins.value_counts(normalize=True).to_dict())
    dump({k: ({str(kk): vv for kk, vv in v.items()} if isinstance(v, dict) else v) for k, v in dec.items()}, "misses.json")


def falsepick():
    """Caveats for the nearest-neighbour proxy (checks.falsepick_nn), over all 30 months: shares at confidence >= 0.5,
    0.7, 0.9; hour-of-day profile (UTC-8) of isolated-unreferenced vs referenced vs non-isolated unreferenced picks;
    how many of the 5 neighbours were loaded that day; isolated share by network; confidence quantiles."""
    ref = pd.read_parquet(RUN / "data" / "reference_picks.parquet", columns=["net", "sta", "t_ref"])
    ref["netsta"] = ref.net + "." + ref.sta
    stc = pd.read_parquet(RAW / "stations.parquet")
    stc["netsta"] = stc.network_code + "." + stc.station_code
    stc = stc.groupby("netsta")[["latitude", "longitude"]].mean()
    sd = station_days()
    loaded = set(zip(sd.netsta, sd.date))
    BIG, W, V, K = np.int64(10 ** 13), 10 * 10 ** 6, 1 * 10 ** 6, 5
    acc = []
    total_p, total_s = 0, 0.0
    for y, mo in MONTHS:
        t0 = pd.Timestamp(year=y, month=mo, day=1)
        t1 = t0 + pd.offsets.MonthBegin(1)
        total_s += (t1 - t0).total_seconds()
        ps = []
        for net in ("CI", "NC", "BK"):
            for f in sorted((RAW / "western" / "picks" / f"network={net}" / f"year={y}" / f"month={mo:02d}").glob("*.parquet")):
                p = pd.read_parquet(f, columns=["tid", "pha", "peak", "conf"])
                ps.append(p[p.pha == "P"])
        p = pd.concat(ps, ignore_index=True)
        p = p[(p.peak >= t0) & (p.peak < t1)]
        p["netsta"] = p.tid.str.rsplit(".", n=1).str[0]
        n_raw = len(p)
        p = p.drop_duplicates(["netsta", "peak"])
        total_p += len(p)
        p = p[p.netsta.isin(stc.index)]
        sta, lev = pd.factorize(p.netsta)
        tus = ((p.peak - t0).dt.total_seconds().values * 1e6).astype(np.int64)
        key = np.sort(sta.astype(np.int64) * BIG + tus)
        xy = stc.loc[lev]
        lat, lon = np.deg2rad(xy.latitude.values), np.deg2rad(xy.longitude.values)
        dist = 6371 * np.hypot((lon[:, None] - lon[None, :]) * np.cos((lat[:, None] + lat[None, :]) / 2), lat[:, None] - lat[None, :])
        np.fill_diagonal(dist, np.inf)
        nn = np.argsort(dist, axis=1)[:, :K]
        idx = np.flatnonzero(p.conf.values >= 0.5)
        s_hi, t_hi = sta[idx].astype(np.int64), tus[idx]
        found = np.zeros(len(idx), bool)
        for k in range(K):
            nb = nn[s_hi, k].astype(np.int64)
            found |= (np.searchsorted(key, nb * BIG + t_hi + W, "right") - np.searchsorted(key, nb * BIG + t_hi - W, "left")) > 0
        r = ref[(ref.t_ref >= t0) & (ref.t_ref < t1) & ref.netsta.isin(lev)]
        rk = np.sort(pd.Index(lev).get_indexer(r.netsta).astype(np.int64) * BIG + ((r.t_ref - t0).dt.total_seconds().values * 1e6).astype(np.int64))
        kk = s_hi * BIG + t_hi
        referenced = (np.searchsorted(rk, kk + V, "right") - np.searchsorted(rk, kk - V, "left")) > 0
        peak = p.peak.values[idx]
        day = pd.DatetimeIndex(peak).floor("D")
        cls = np.where(referenced, "referenced", np.where(~found, "isolated_unreferenced", "unreferenced_not_isolated"))
        # neighbours loaded that day (isolated-unreferenced picks only)
        iso = np.flatnonzero(cls == "isolated_unreferenced")
        nl = np.full(len(idx), -1)
        if len(iso):
            nbn = lev.values[nn[s_hi[iso]]]
            dd = day[iso]
            nl[iso] = [sum((n, dy) in loaded for n in row) for row, dy in zip(nbn, dd)]
        acc.append(pd.DataFrame({"net": lev.values[s_hi].astype(str), "conf": p.conf.values[idx], "cls": cls,
                                 "hour_local": (pd.DatetimeIndex(peak).hour - 8) % 24, "nb_loaded": nl}))
        print(y, mo, n_raw, len(p), len(idx), flush=True)
    x = pd.concat(acc, ignore_index=True)
    x["net"] = x.net.str.split(".").str[0]
    iso = x.cls == "isolated_unreferenced"
    thr = {f"conf>={c}": dict(n=int((x.conf >= c).sum()), share_isolated_unreferenced=float(iso[x.conf >= c].mean()))
           for c in (0.5, 0.7, 0.9)}
    hours = x.groupby(["cls", "hour_local"]).size().unstack(0)
    hours = (hours / hours.sum() * 24).round(3)
    hours.to_csv(OUT / "falsepick_hour_profile.csv")
    day = x.hour_local.between(7, 18)
    dump(dict(p_picks_all_conf=int(total_p), seconds=total_s, p_picks_per_second=total_p / total_s, thresholds=thr,
              daytime_07_18_share={c: float(day[x.cls == c].mean()) for c in x.cls.unique()},
              isolated_neighbours_loaded={str(k): float(v) for k, v in x.nb_loaded[iso].value_counts(normalize=True).sort_index().items()},
              isolated_share_by_network=x.groupby("net").apply(lambda g: float((g.cls == "isolated_unreferenced").mean())).to_dict(),
              conf_quantiles={c: x.conf[x.cls == c].quantile([0.25, 0.5, 0.75]).round(3).tolist() for c in x.cls.unique()}),
         "falsepick_caveats.json")


def table():
    """station_reliability.csv with review columns: share of the station's H1 picks on zero-pick and low-count days,
    adjusted recall without zero-pick days, the noise window count and flags."""
    d, _ = flagged()
    rel = pd.read_csv(PRIMARY_TAB / "station_reliability.csv").set_index("netsta")
    rel["zero_pick_day_share"] = d.groupby("netsta").zero_day.mean().reindex(rel.index)
    rel["low_day_share"] = d.groupby("netsta").low_day.mean().reindex(rel.index)
    eA = pd.read_csv(OUT / "effects_excl_zero_days.csv").set_index("netsta")
    rel["recall_ref_excl_zero_days"] = eA.recall_ref.reindex(rel.index)
    rel["noise_windows"] = pd.to_numeric(rel.noise_note.str.extract(r"(\d+) windows")[0], errors="coerce")
    rel["flag_zero_pick_days_gt_25pct"] = rel.zero_pick_day_share > 0.25
    rel["flag_noise_implausible"] = (rel.log_noise > -6) | (rel.log_noise < -8.7)
    rel.to_csv(PRIMARY_TAB / "station_reliability.csv")
    print(rel[["zero_pick_day_share", "recall_ref", "recall_ref_excl_zero_days"]].describe())
    print("flagged zero-pick stations:", int(rel.flag_zero_pick_days_gt_25pct.sum()), "noise:", int(rel.flag_noise_implausible.sum()))


if __name__ == "__main__":
    {"zero": zero, "weights": weights, "misc": misc, "misses": misses, "falsepick": falsepick, "table": table}[sys.argv[1]]()
