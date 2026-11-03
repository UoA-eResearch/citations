"""H1, H2 and the secondaries (plan sections 0 and 2).

Weights: 1 / C at a detection's (TESS-magnitude bin, log P_rot bin, log amplitude bin); a cell with fewer than 10
injections falls back to the cell pooled over magnitude; detections with C < 0.1 (or no usable cell) are dropped.
Logistic fits are weighted Bernoulli maximum likelihood. H1's Teff logistic has free floor, ceiling, midpoint and
scale; H2's period logistics have two parameters (midpoint and scale, decreasing in log P), so a midpoint is where
the fitted share is one half. Intervals: 2,000 bootstrap resamples of stars.

  analyse.py -> results/tables/primary.json, secondary.json
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
B, SEED = 2000, 20261103
RSUN_KM = 695700.0


def weights(st):
    C = pd.read_csv(T / "completeness.csv"); E = pd.read_csv(T / "completeness_edges.csv")
    PB, AB = E[E.edge == "P"].value.to_numpy(), E[E.edge == "A"].value.to_numpy(); TB = E[E.edge == "T"].value.to_numpy()
    pooled = C.groupby(["pb", "ab"]).apply(lambda g: pd.Series({"mean": np.average(g["mean"], weights=g["size"]), "size": g["size"].sum()}))
    cell = C.set_index(["tb", "pb", "ab"])
    tb = np.digitize(st.Tmag, TB) - 1; pb = np.digitize(st.p_rot, PB) - 1; ab = np.digitize(st.amp, AB) - 1
    c = []
    for t, p, a in zip(tb, pb, ab):
        v = np.nan
        if (t, p, a) in cell.index and cell.loc[(t, p, a), "size"] >= 10:
            v = cell.loc[(t, p, a), "mean"]
        elif (p, a) in pooled.index and pooled.loc[(p, a), "size"] >= 10:
            v = pooled.loc[(p, a), "mean"]
        c.append(v)
    return np.asarray(c, float)


def wshare(y, w):
    return float(np.sum(w * y) / np.sum(w)) if np.sum(w) > 0 else np.nan


def fit_teff(Tf, y, w):
    def nll(th):
        lo, hi, T0, lw = th
        p = np.clip(lo + (hi - lo) / (1 + np.exp((Tf - T0) / np.exp(lw))), 1e-6, 1 - 1e-6)
        return -np.sum(w * (y * np.log(p) + (1 - y) * np.log(1 - p)))
    best = None
    for T0 in (5500, 6200, 6800):
        r = minimize(nll, [0.1, 0.8, T0, np.log(150)], method="L-BFGS-B",
                     bounds=[(0, 1), (0, 1), (4000, 7500), (np.log(10), np.log(3000))])
        if best is None or r.fun < best.fun:
            best = r
    lo, hi, T0, lw = best.x
    return {"floor": lo, "ceiling": hi, "T0": T0, "width_10_90": 4.39 * np.exp(lw)}


def fit_mid(logP, y, w):
    def nll(th):
        m, ls = th
        p = np.clip(1 / (1 + np.exp((logP - m) / np.exp(ls))), 1e-6, 1 - 1e-6)
        return -np.sum(w * (y * np.log(p) + (1 - y) * np.log(1 - p)))
    r = minimize(nll, [np.log(5), np.log(0.3)], method="L-BFGS-B", bounds=[(np.log(0.1), np.log(300)), (np.log(0.01), np.log(5))])
    return float(np.exp(r.x[0]))


def main():
    st = pd.read_parquet(D / "stars.parquet")
    det = st[st.cls == "detected"].copy()
    det["C"] = weights(det); det = det[det.C >= 0.1]; det["w"] = 1 / det.C; det["y"] = det.sync.astype(float)
    rng = np.random.default_rng(SEED)
    out = {"detections_weighted": int(len(det)), "detections_dropped_low_C": int((st.cls == "detected").sum() - len(det))}

    # H1
    h = det[(det.period < 10) & det.teff.between(4000, 7500)]
    cool, hot = h.teff.between(4000, 6200, inclusive="left"), h.teff.between(6500, 7500, inclusive="left")
    est = {"f_cool": wshare(h.y[cool], h.w[cool]), "f_hot": wshare(h.y[hot], h.w[hot]), **fit_teff(h.teff.to_numpy(), h.y.to_numpy(), h.w.to_numpy())}
    bs = []
    for _ in range(B):
        k = rng.integers(0, len(h), len(h)); x = h.iloc[k]
        c, ht = x.teff.between(4000, 6200, inclusive="left"), x.teff.between(6500, 7500, inclusive="left")
        bs.append({"f_cool": wshare(x.y[c], x.w[c]), "f_hot": wshare(x.y[ht], x.w[ht]), **fit_teff(x.teff.to_numpy(), x.y.to_numpy(), x.w.to_numpy())})
    bs = pd.DataFrame(bs)
    ci = {k: [float(bs[k].quantile(0.025)), float(bs[k].quantile(0.975))] for k in est}
    sup = ci["f_cool"][0] > 0.70 and ci["f_hot"][1] < 0.30 and est["width_10_90"] < 400
    ref = ci["f_cool"][1] < 0.70 or ci["f_hot"][0] > 0.30 or ci["width_10_90"][0] > 400
    out["H1"] = {"n_cool": int(cool.sum()), "n_hot": int(hot.sum()), "n_fit": int(len(h)),
                 "estimate": {k: float(v) for k, v in est.items()}, "ci": ci,
                 "verdict": "Supported" if sup else "Refuted" if ref else "Inconclusive"}

    # H2
    allst = st[st.period.between(0.5, 30)].copy()
    allst["circ"] = ((allst.nss_solution_type == "SB1C") | (allst.eccentricity.fillna(1) < 0.05)).astype(float)
    bins = {"4000-5500": (4000, 5500), "5500-6200": (5500, 6200), "6200-7000": (6200, 7000)}
    h2, votes = {}, []
    for name, (a, b) in bins.items():
        ds = det[det.teff.between(a, b, inclusive="left") & det.period.between(0.5, 12)]
        cs = allst[allst.teff.between(a, b, inclusive="left")]
        ps, pc = fit_mid(np.log(ds.period.to_numpy()), ds.y.to_numpy(), ds.w.to_numpy()), fit_mid(np.log(cs.period.to_numpy()), cs.circ.to_numpy(), np.ones(len(cs)))
        lr = []
        for _ in range(B):
            x = ds.iloc[rng.integers(0, len(ds), len(ds))]; z = cs.iloc[rng.integers(0, len(cs), len(cs))]
            s_ = fit_mid(np.log(x.period.to_numpy()), x.y.to_numpy(), x.w.to_numpy()); c_ = fit_mid(np.log(z.period.to_numpy()), z.circ.to_numpy(), np.ones(len(z)))
            lr.append((s_, c_))
        lr = np.array(lr); pc_ci = [float(np.quantile(lr[:, 1], 0.025)), float(np.quantile(lr[:, 1], 0.975))]
        beyond = ps > 12
        if beyond:
            vote = "supports" if pc_ci[1] < 12 else "neither"; ratio_ci = None
        else:
            r = np.log(np.minimum(lr[:, 0], 12) / lr[:, 1]); ratio_ci = [float(np.quantile(r, 0.025)), float(np.quantile(r, 0.975))]
            vote = "supports" if ratio_ci[0] > 0 else "reverse" if ratio_ci[1] < 0 else "neither"
        votes.append(vote)
        h2[name] = {"n_sync_sample": int(len(ds)), "n_circ_sample": int(len(cs)), "P_sync50": "> 12 d" if beyond else float(ps),
                    "P_circ50": float(pc), "P_circ50_ci": pc_ci, "log_ratio_ci": ratio_ci, "vote": vote}
    out["H2"] = {"bins": h2, "verdict": "Refuted" if "reverse" in votes else "Supported" if votes.count("supports") >= 2 else "Inconclusive"}
    (T / "primary.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(json.dumps({"H1": out["H1"]["verdict"], "H2": out["H2"]["verdict"]}))

    # secondaries
    sec = {}
    lc = st[(st.n_sectors_lc > 0) & (st.period < 10)]
    for g, (a, b) in {"cool": (4000, 6200), "hot": (6500, 7500)}.items():
        x = lc[lc.teff.between(a, b, inclusive="left")]
        syn = int((x.sync_state == "synchronized").sum()); nod = int((x.cls == "no_detection").sum())
        sec[f"bounds_{g}"] = {"stars_with_lc": len(x), "synchronized": syn, "no_detection": nod,
                              "lower": syn / max(len(x), 1), "upper": (syn + nod) / max(len(x), 1), "classes": x.cls.value_counts().to_dict()}
        d = det[(det.period < 10) & det.teff.between(a, b, inclusive="left")]
        sec[f"unweighted_{g}"] = float(d.y.mean()) if len(d) else None
        n3 = d[d.dist_pc < 300]; sec[f"within_300pc_{g}"] = wshare(n3.y, n3.w) if len(n3) else None
        amb = x[x.cls.isin(["detected", "ellipsoidal_or_double_spot"])]
        sec[f"ellipsoidal_as_synchronized_{g}"] = float(((amb.cls == "ellipsoidal_or_double_spot") | (amb.sync_state == "synchronized")).mean()) if len(amb) else None
        R = x.radius_flame.fillna(x.radius_gspphot)
        v = x.assign(vs=2 * np.pi * R * RSUN_KM / (x.period * 86400)).dropna(subset=["vbroad", "vs"])
        sec[f"vbroad_{g}"] = {"n": len(v), "share_clearly_supersynchronous": float((v.vbroad > 1.5 * v.vs + 2 * v.vbroad_error.fillna(0)).mean()) if len(v) else None}
        sec[f"states_{g}"] = d.sync_state.value_counts().to_dict()
    cut = {}
    for a in range(4000, 7500, 500):
        cs = allst[allst.teff.between(a, a + 500, inclusive="left")]
        if len(cs) > 50:
            cut[f"{a}-{a + 500}"] = {"n": len(cs), "P_circ50": fit_mid(np.log(cs.period.to_numpy()), cs.circ.to_numpy(), np.ones(len(cs)))}
    sec["circularization_cutoff_by_teff"] = cut
    (T / "secondary.json").write_text(json.dumps(sec, indent=1, default=float) + "\n")
    print(json.dumps({k: v for k, v in sec.items() if k.startswith(("bounds", "unweighted", "vbroad"))}, default=float)[:1500])


if __name__ == "__main__":
    main()
