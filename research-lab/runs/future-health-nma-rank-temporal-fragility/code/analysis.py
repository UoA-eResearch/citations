"""Primary and further analyses (plan sections 2, 4 and 7; D2). Reads data/fits.jsonl, data/holdouts.csv,
results/tables/direction.csv and data/std. Writes results/tables/primary.json and results/tables/network_results.csv."""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import kendalltau, norm

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"
B = 2000
rng = np.random.default_rng(20261018)


def pscores(TE, se, trts, keep, small):
    """P-scores over the treatment subset `keep`, from a fit's estimate matrices (TE[i][j] = theta_i - theta_j)."""
    idx = [trts.index(t) for t in keep]
    if len(idx) < 2:
        return {t: float("nan") for t in keep}
    s = 1.0 if small == "good" else -1.0
    A, S = np.asarray(TE, float)[np.ix_(idx, idx)], np.asarray(se, float)[np.ix_(idx, idx)]
    with np.errstate(divide="ignore", invalid="ignore"):
        z = norm.cdf(s * (-A) / S)
    np.fill_diagonal(z, np.nan)
    m = np.nanmean(z, axis=1)
    return {trts[a]: float(v) for a, v in zip(idx, m)}


def top(d):
    return max(d, key=lambda k: (d[k], k)) if d else None


def wilson(k, n, z=1.959964):
    if n == 0:
        return [float("nan")] * 2
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [c - h, c + h]


def boot(df, f):
    vals = []
    n = len(df)
    for _ in range(B):
        x = df.iloc[rng.integers(0, n, n)]
        try:
            vals.append(f(x))
        except Exception:  # noqa: BLE001
            pass
    vals = [v for v in vals if v is not None and np.isfinite(v)]
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))] if vals else [None, None], len(vals)


def nagelkerke(y, X):
    X = sm.add_constant(np.asarray(X, float), has_constant="add")
    m = sm.Logit(np.asarray(y, float), X).fit(disp=0, maxiter=200)
    n = len(y)
    l1, l0 = m.llf, m.llnull
    cs = 1 - math.exp(2 * (l0 - l1) / n)
    return cs / (1 - math.exp(2 * l0 / n)), m


def auc(y, p):
    y, p = np.asarray(y), np.asarray(p)
    pos, neg = p[y == 1], p[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    return float(np.mean([(a > b) + 0.5 * (a == b) for a in pos for b in neg]))


def holdout_result(full, pre, small, common=False):
    """Flip and related quantities for one pre-update fit against the full fit."""
    TE, se = (full["TE_common"], full["seTE_common"]) if common else (full["TE"], full["seTE"])
    ftr = full["trts"]
    keep = [t for t in pre["trts"] if t in ftr]
    pre_ps = dict(zip(pre["trts"], pre["pscore_common" if common else "pscore"]))
    pre_ps = {t: pre_ps[t] for t in keep}
    full_sub = pscores(TE, se, ftr, keep, small)
    full_all = pscores(TE, se, ftr, ftr, small)
    pt, ft = top(pre_ps), top(full_sub)
    o = sorted(pre_ps.values(), reverse=True)
    r = dict(pre_top=pt, full_top=ft, flip=int(pt != ft), new_entrant_top=int(top(full_all) not in keep),
             gap=o[0] - o[1] if len(o) > 1 else float("nan"), n_trts_pre=len(keep),
             top2_changed=int(set(sorted(pre_ps, key=lambda k: -pre_ps[k])[:2]) != set(sorted(full_sub, key=lambda k: -full_sub[k])[:2])))
    if len(keep) >= 3:
        r["kendall"] = float(kendalltau([pre_ps[t] for t in keep], [full_sub[t] for t in keep]).statistic)
    if "pbest" in pre and not common:
        pb = dict(zip(pre["pbest_trts"], pre["pbest"]))
        r["pbest_top"] = float(pb.get(pt, float("nan")))
        r["tau2_pre"], r["I2_pre"], r["prop_direct_top2"] = pre.get("tau2"), pre.get("I2"), pre.get("prop_direct_top2")
        r["n_studies_pre"] = pre.get("n_studies")
        if pre.get("sucra") and full.get("sucra"):
            ps_ = dict(zip(pre["trts"], pre["sucra"])); fs_ = dict(zip(full["trts"], full["sucra"]))
            r["flip_sucra"] = int(top({t: ps_[t] for t in keep}) != top({t: fs_[t] for t in keep}))
    return r


def summarise(df, label):
    k, n = int(df.flip.sum()), len(df)
    out = dict(set=label, n=n, flips=k, flip_rate=k / n if n else None, flip_ci=wilson(k, n),
               new_entrant_top=int(df.new_entrant_top.sum()))
    if "pbest_top" in df and df.pbest_top.notna().any():
        d = df[df.pbest_top.notna()]
        f = lambda x: float(x.pbest_top.mean() - (1 - x.flip).mean())
        ci, nb = boot(d, f)
        out.update(mean_pbest=float(d.pbest_top.mean()), retention=float(1 - d.flip.mean()), overstatement=f(d), overstatement_ci=ci)
    return out


CONT = set()
JOBS = {}


def main():
    global CONT
    ss = pd.read_csv(RUN / "data" / "std_summary.csv", dtype={"record": str})
    CONT = set(ss[ss.type == "Continuous"].record)
    global JOBS
    JOBS = {j["record"]: {f["name"]: [str(x) for x in f["studies"]] for f in j["fits"]} for j in json.load(open(RUN / "data" / "jobs.json"))}
    hold = pd.read_csv(RUN / "data" / "holdouts.csv", dtype={"record": str}).set_index("record")
    dr = pd.read_csv(T / "direction.csv", dtype={"record": str}).set_index("record")
    fits = {}
    for line in open(RUN / "data" / "fits.jsonl"):
        r = json.loads(line)
        fits[r["record"]] = {f["name"]: f for f in r["fits"]}
    rows, randoms, notes = [], {}, {}
    for rec, F in fits.items():
        h = hold.loc[rec]
        small = dr.loc[rec, "small_values"]
        base = dict(record=rec, set=h["set"], confidence=dr.loc[rec, "confidence"], k=int(h["k"]), T10_share=float(h["T10_share"]))
        full = F.get("full", {})
        if full.get("error") or "TE" not in full:
            notes[rec] = "full fit failed"; rows.append({**base, "included": False, "reason": "full fit failed"}); continue
        if h["T10_share"] > 0.5:
            rows.append({**base, "included": False, "reason": "tranche > 50%"}); continue
        # participants in the withheld tranche (arm-level) or its share of studies (contrast-level)
        d = pd.read_csv(RUN / "data" / "std" / f"{rec}.csv", dtype={"study": str})
        res = {}
        for name in ("T10", "S1", "S2", "S3"):
            pre = F.get(name, {})
            if pre.get("error") or "trts" not in pre or len(pre.get("trts", [])) < 2:
                res[name] = None; continue
            res[name] = holdout_result(full, pre, small)
            res[name + "_common"] = holdout_result(full, pre, small, common=True)
        if res.get("T10") is None:
            rows.append({**base, "included": False, "reason": "pre-update fit failed"}); continue
        used = set(F["T10"].get("studies_used") or [])
        if "n" in d:
            nn = d.groupby("study").n.sum()
            wshare = float(nn[~nn.index.isin(used)].sum() / nn.sum())
        else:   # D4: contrast-level studies, counted by original study id (split labels "id_k" map back)
            used_ids = {str(u).split("_")[0] for u in used}
            wshare = float(1 - len(used_ids & set(d.study.astype(str))) / d.study.nunique())
        row = {**base, "included": True, "reason": "", "withheld_share": wshare, "type": "contrast" if "TE" in d else "arm",
               "continuous": int("y" in d or rec in CONT),
               "multiarm_split": bool(full.get("multiarm_split"))}
        for name in ("T10", "S1", "S2", "S3"):
            for suffix in ("", "_common"):
                rr = res.get(name + suffix)
                if rr:
                    for kk, vv in rr.items():
                        row[f"{name}{suffix}_{kk}"] = vv
        # negative control: random holdouts of the same size
        fl = []
        for name, pre in F.items():
            if name.startswith("R") and not pre.get("error") and len(pre.get("trts", [])) >= 2:
                fl.append(holdout_result(full, pre, small)["flip"])
        row["random_flip_prob"] = float(np.mean(fl)) if fl else float("nan")
        row["random_n"] = len(fl)
        # D4 (review issue 8): participants withheld by the random holdouts, to compare with the temporal tranche
        if "n" in d:
            nn_s = d.groupby("study").n.sum()
            shares = [float(nn_s[~nn_s.index.isin(set(JOBS[rec][name]))].sum() / nn_s.sum())
                      for name, pre in F.items() if name.startswith("R") and not pre.get("error")]
            row["random_withheld_share"] = float(np.mean(shares)) if shares else float("nan")
        rows.append(row)
    nr = pd.DataFrame(rows)
    nr.to_csv(T / "network_results.csv", index=False)
    inc = nr[nr.included]
    P = inc[inc.set == "primary"].copy()
    ALL = inc.copy()
    HI = inc[(inc.set == "primary") | (inc.confidence == "high")].copy()
    out = dict(networks_fitted=len(nr), excluded=nr[~nr.included].reason.value_counts().to_dict(),
               included_primary=len(P), included_iv=int((inc.set == "iv_sensitivity").sum()))

    def view(df, prefix):
        x = df[[c for c in df.columns if c.startswith(prefix + "_")] + ["record"]].copy()
        x.columns = [c[len(prefix) + 1:] if c.startswith(prefix + "_") else c for c in x.columns]
        return x.dropna(subset=["flip"])

    t10 = view(P, "T10")
    # H1
    h1 = summarise(t10, "primary")
    lo, hi = h1["flip_ci"]
    h1["verdict"] = "Supported" if (h1["flip_rate"] >= 0.30 and lo >= 0.25) else "Refuted" if hi < 0.30 else "Inconclusive"
    out["H1"] = h1
    # H2
    h2 = dict(mean_pbest=h1.get("mean_pbest"), retention=h1.get("retention"), overstatement=h1.get("overstatement"), ci=h1.get("overstatement_ci"))
    l2, u2 = h2["ci"]
    h2["verdict"] = "Supported" if (h2["overstatement"] >= 0.20 and l2 >= 0.15) else "Refuted" if u2 < 0.20 else "Inconclusive"
    out["H2"] = h2
    # H3
    m3 = t10.dropna(subset=["gap", "n_studies_pre"]).copy()
    m3["log_k"] = np.log(m3.n_studies_pre.astype(float))
    try:
        r2, mod = nagelkerke(m3.flip, m3[["gap", "log_k"]])
        ci3, nb3 = boot(m3, lambda x: nagelkerke(x.flip, x[["gap", "log_k"]])[0])
        out["H3"] = dict(n=len(m3), nagelkerke_r2=r2, ci=ci3, boot_ok=nb3, coef=dict(zip(["const", "gap", "log_k"], map(float, mod.params))),
                         auc=auc(m3.flip, mod.predict(sm.add_constant(m3[["gap", "log_k"]].astype(float), has_constant="add"))),
                         verdict="Supported" if ci3[1] is not None and ci3[1] < 0.50 else "Refuted" if ci3[0] is not None and ci3[0] >= 0.50 else "Inconclusive")
    except Exception as e:  # noqa: BLE001
        out["H3"] = dict(error=str(e))
    # negative control
    nc = P.dropna(subset=["random_flip_prob"]).copy()
    nc["d"] = nc["T10_flip"] - nc["random_flip_prob"]
    ci_nc, _ = boot(nc, lambda x: float(x.d.mean()))
    out["negative_control"] = dict(n=len(nc), temporal_flip_rate=float(nc["T10_flip"].mean()), random_flip_rate=float(nc.random_flip_prob.mean()),
                                   difference=float(nc.d.mean()), ci=ci_nc,
                                   withheld_participants_temporal=float(nc.withheld_share.mean()) if "withheld_share" in nc else None,
                                   withheld_participants_random=float(nc.random_withheld_share.mean()) if "random_withheld_share" in nc else None)
    # D4 (review issue 9): retention when a new entrant that becomes top counts as a loss
    out["retention_with_new_entrants"] = {nm: float(1 - ((view(P, nm).flip == 1) | (view(P, nm).new_entrant_top == 1)).mean()) for nm in ("T10", "S1", "S2", "S3")}
    # full predictor model
    fm = t10.merge(P[["record", "withheld_share", "type"]], on="record").dropna(subset=["gap", "n_studies_pre", "I2_pre", "prop_direct_top2"]).copy()
    fm["log_k"] = np.log(fm.n_studies_pre.astype(float))
    fm = fm.merge(P[["record", "continuous"]], on="record")
    try:
        cols = ["gap", "log_k", "n_trts_pre", "I2_pre", "prop_direct_top2", "withheld_share", "continuous"]
        r2f, modf = nagelkerke(fm.flip, fm[cols])
        out["full_model"] = dict(n=len(fm), nagelkerke_r2=r2f, auc=auc(fm.flip, modf.predict(sm.add_constant(fm[cols].astype(float), has_constant="add"))),
                                 coef=dict(zip(["const"] + cols, map(float, modf.params))), p=dict(zip(["const"] + cols, map(float, modf.pvalues))))
    except Exception as e:  # noqa: BLE001
        out["full_model"] = dict(error=str(e))
    # calibration curve
    cal = []
    for a, b in [(0, .2), (.2, .4), (.4, .6), (.6, .8), (.8, 1.0001)]:
        x = t10[(t10.pbest_top >= a) & (t10.pbest_top < b)]
        if len(x):
            ci, _ = boot(x, lambda y: float(1 - y.flip.mean()))
            cal.append(dict(bin=f"{a:.1f}-{min(b, 1):.1f}", n=len(x), mean_pbest=float(x.pbest_top.mean()), retention=float(1 - x.flip.mean()), retention_ci=ci))
    out["calibration"] = cal
    out["rank_agreement"] = dict(kendall_median=float(t10.kendall.median()), kendall_mean=float(t10.kendall.mean()),
                                 top2_changed=int(t10.top2_changed.sum()), n=len(t10))
    # secondary holdouts, common effect, SUCRA
    sec = {}
    for name in ("S1", "S2", "S3"):
        v = view(P, name)
        if len(v):
            sec[name] = summarise(v, name)
    for name in ("T10",):
        v = view(P, name + "_common")
        sec["T10_common_effect"] = dict(n=len(v), flips=int(v.flip.sum()), flip_rate=float(v.flip.mean()), flip_ci=wilson(int(v.flip.sum()), len(v)))
    if "flip_sucra" in t10:
        v = t10.dropna(subset=["flip_sucra"])
        sec["T10_sucra"] = dict(n=len(v), flips=int(v.flip_sucra.sum()), flip_rate=float(v.flip_sucra.mean()), flip_ci=wilson(int(v.flip_sucra.sum()), len(v)))
    out["secondary"] = sec
    # iv sensitivity
    out["iv_sensitivity"] = dict(with_iv=summarise(view(ALL, "T10"), "primary + iv"), with_iv_high_confidence=summarise(view(HI, "T10"), "primary + iv high"),
                                 multiarm_split_networks=int(inc.multiarm_split.sum()))
    out["descriptives"] = dict(tranche_share_median=float(P.T10_share.median()), withheld_participants_median=float(P.withheld_share.median()),
                               studies_median=float(P.k.median()), trts_median=float(t10.n_trts_pre.median()),
                               gap_median=float(t10.gap.median()), pbest_median=float(t10.pbest_top.median()))
    json.dump(out, open(T / "primary.json", "w"), indent=1, default=float)
    print(json.dumps({k: out[k] for k in ("included_primary", "H1", "H2", "H3", "negative_control")}, indent=1, default=float)[:3000])


if __name__ == "__main__":
    main()
