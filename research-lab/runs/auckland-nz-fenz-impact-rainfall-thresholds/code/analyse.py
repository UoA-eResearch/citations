"""H1 and secondaries (plan sections 0 and 3). Committed before it was run on the test year.

Logistic regression by L-BFGS with an analytic gradient. Rain enters as a natural cubic spline with 4 df (interior
knots at the 25/50/75% quantiles of the covariate's positive training values, boundary knots at 0 and its 99.9%
training quantile, linear beyond). Shared terms: log(1 + 72-h antecedent rain), month and region (deviation coding,
so a region left out in cross-validation gets the average effect), weekend, suburb activity.

The plan's S >= 1.05 is evaluated as (LL0 - LL_R) >= 1.05 (LL0 - LL_D), the same condition when the depth model has
positive skill, and defined when it has none.

  analyse.py -> results/tables/primary.json, secondary.json, onset.csv, auckland_curve.csv
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

RUN = Path(__file__).resolve().parents[1]
HL = RUN.parent / "auckland-nz-hirds-out-of-sample-exceedance-audit"
D, T = RUN / "data", RUN / "results" / "tables"
SEED, B = 20261028, 2000


def ns_basis(x, knots):
    k = np.asarray(knots, float); K = len(k)
    d = lambda j: (np.clip(x - k[j], 0, None) ** 3 - np.clip(x - k[-1], 0, None) ** 3) / (k[-1] - k[j])
    return np.column_stack([x] + [d(j) - d(K - 2) for j in range(K - 2)])


def knots_for(x_train):
    pos = x_train[x_train > 0]
    return [0.0, *np.quantile(pos, [0.25, 0.5, 0.75]), float(np.quantile(x_train, 0.999))]


def deviation(codes, levels):
    """Deviation coding: one column per level except the last; the last level is -1 everywhere; unseen levels are 0."""
    M = np.zeros((len(codes), len(levels) - 1))
    for j, lv in enumerate(levels[:-1]):
        M[:, j] = (codes == lv)
    M[codes == levels[-1], :] = -1
    return M


class Design:
    def __init__(self, P_train, rain_col, regions):
        self.rain_col, self.regions = rain_col, regions
        self.knots = knots_for(P_train[rain_col].to_numpy()) if rain_col else None
        X = self.raw(P_train)
        self.mu, self.sd = X.mean(0), X.std(0) + 1e-12

    def raw(self, P):
        cols = [np.log1p(P.ante72.to_numpy())[:, None], P.weekend.to_numpy()[:, None].astype(float),
                P.activity.to_numpy()[:, None], deviation(P.month.to_numpy(), list(range(1, 13))),
                deviation(P.region.to_numpy(), self.regions)]
        if self.rain_col:
            cols.insert(0, ns_basis(P[self.rain_col].to_numpy(), self.knots))
        return np.hstack(cols)

    def X(self, P):
        return np.hstack([np.ones((len(P), 1)), (self.raw(P) - self.mu) / self.sd])


def fit(X, y):
    def f(b):
        z = X @ b
        ll = np.logaddexp(0, z) - y * z
        p = 1 / (1 + np.exp(-z))
        return ll.mean() + 1e-8 * (b[1:] @ b[1:]), X.T @ (p - y) / len(y) + np.r_[0, 2e-8 * b[1:]]
    b0 = np.zeros(X.shape[1]); b0[0] = np.log(y.mean() / (1 - y.mean()))
    r = minimize(f, b0, jac=True, method="L-BFGS-B", options={"maxiter": 2000})
    return r.x


def logloss(X, b, y):
    z = X @ b
    return np.logaddexp(0, z) - y * z


def prep(P, outcome="flood"):
    P = P.copy()
    P["y"] = (P[outcome] > 0).astype(float)
    P["month"] = P.day.dt.month; P["weekend"] = P.day.dt.dayofweek >= 5
    P["ld6"], P["lr6"] = np.log1p(P.d6), np.log1p(P.d6 / P.M6)
    P["ld1"], P["lr1"] = np.log1p(P.d1), np.log1p(P.d1 / P.M1)
    P["ld24"], P["lr24"] = np.log1p(P.d24), np.log1p(P.d24 / P.M24)
    return P


def compare(P, dcol, rcol, rng, regions=None, with_boot=True):
    tr, te = P[~P.test], P[P.test]
    regions = regions or sorted(P.region.unique())
    out, ll = {}, {}
    for name, col in (("base", None), ("D", dcol), ("R", rcol)):
        des = Design(tr, col, regions)
        b = fit(des.X(tr), tr.y.to_numpy())
        ll[name] = logloss(des.X(te), b, te.y.to_numpy())
        out[f"LL_{name}"] = round(float(ll[name].mean()), 7)
    diff = ll["D"] - ll["R"]
    out["D_LL"] = float(diff.mean())
    out["skill_D"], out["skill_R"] = out["LL_base"] - out["LL_D"], out["LL_base"] - out["LL_R"]
    out["S_condition"] = bool(out["skill_R"] >= 1.05 * out["skill_D"])
    out["S"] = round(out["skill_R"] / out["skill_D"], 3) if out["skill_D"] > 0 else None
    if with_boot:
        day = te.day.to_numpy()
        g = pd.DataFrame({"day": day, "d": diff}).groupby("day").d.agg(["sum", "size"])
        s, n = g["sum"].to_numpy(), g["size"].to_numpy()
        bs = []
        for _ in range(B):
            k = rng.integers(0, len(s), len(s))
            bs.append(s[k].sum() / n[k].sum())
        out["D_LL_ci"] = [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
    out["test_suburb_days"], out["test_floods"] = int(len(te)), int(te.y.sum())
    return out


def loro(P, dcol, rcol):
    regions = sorted(P.region.unique())
    counts = P.groupby("region").y.sum()
    res = {}
    for g in [r for r in regions if counts.get(r, 0) >= 20 and r]:
        tr = P[~P.test & (P.region != g)]; te = P[P.test & (P.region == g)]
        lls = {}
        for name, col in (("D", dcol), ("R", rcol)):
            des = Design(tr, col, [r for r in regions if r != g])
            b = fit(des.X(tr), tr.y.to_numpy())
            lls[name] = float(logloss(des.X(te), b, te.y.to_numpy()).mean())
        res[g] = {"LL_D": round(lls["D"], 7), "LL_R": round(lls["R"], 7), "R_wins": lls["R"] < lls["D"],
                  "test_floods": int(te.y.sum()), "floods_all_years": int(counts[g])}
    wins = sum(v["R_wins"] for v in res.values())
    return {"regions": res, "wins": wins, "n": len(res), "majority": wins > len(res) / 2}


def verdict(o, lo):
    lo_ci, hi_ci = o["D_LL_ci"]
    if o["D_LL"] > 0 and lo_ci > 0 and o["S_condition"] and lo["majority"]:
        return "Supported"
    if hi_ci < 0 or (lo_ci <= 0 <= hi_ci and o["skill_R"] < o["skill_D"] and lo["wins"] < lo["n"] / 2):   # plan: S < 1
        return "Refuted"
    return "Inconclusive"


def main():
    P0 = pd.read_parquet(D / "panel.parquet")
    P = prep(P0)
    rng = np.random.default_rng(SEED)
    o = compare(P, "ld6", "lr6", rng)
    lo = loro(P, "ld6", "lr6")
    o["H1"] = verdict(o, lo)
    o["loro"] = lo
    (T / "primary.json").write_text(json.dumps(o, indent=1, default=str) + "\n")
    print(json.dumps({k: v for k, v in o.items() if k != "loro"}, indent=1, default=str)); print("LORO wins", lo["wins"], "/", lo["n"])

    sec = {}
    for h in (1, 24):
        sec[f"{h}h"] = compare(P, f"ld{h}", f"lr{h}", np.random.default_rng(SEED + h))
    # AEP form: log ARI from each gauge's HIRDS 6-h curve where d6 >= its 1.58-year depth, joined to log(1 + r) below
    H = pd.read_parquet(HL / "data" / "hirds_depths.parquet")
    H = H[(H.table == "historical") & (H.duration_h == 6)].sort_values(["file", "ari"])
    curves = {f: (g.mm.to_numpy(), np.log(g.ari.to_numpy())) for f, g in H.groupby("file")}
    z = P.lr6.to_numpy().copy()
    for f, idx in P.groupby("gauge").indices.items():
        dep, lari = curves[f]
        d = P.d6.to_numpy()[idx]
        hi = d >= dep[0]
        join = np.log1p(dep[0] / P.M6.to_numpy()[idx][0])
        z[idx[hi]] = join + (np.interp(d[hi], dep, lari, right=np.nan) - lari[0])
        over = hi & np.isnan(z[idx])
        z[idx[over]] = join + (lari[-1] - lari[0]) + (d[over] - dep[-1]) / dep[-1]      # beyond 250 years: linear in depth
    P["laep"] = z
    sec["aep_form"] = compare(P, "ld6", "laep", np.random.default_rng(SEED + 3))
    for v in ("v1", "v2"):
        sec[f"outcome_{v}"] = compare(prep(P0, v), "ld6", "lr6", np.random.default_rng(SEED + 10 + len(v)))
    Q = P[P.d6_q.notna()].copy(); Q["ld6"], Q["lr6"] = np.log1p(Q.d6_q), np.log1p(Q.d6_q / Q.M6_q)
    sec["quality_Q"] = compare(Q, "ld6", "lr6", np.random.default_rng(SEED + 20))
    sec["within_5km"] = compare(P[P.gauge_km <= 5], "ld6", "lr6", np.random.default_rng(SEED + 21))
    I = P.copy(); I["ld6"], I["lr6"] = np.log1p(I.d6_idw), np.log1p(I.r6_idw)
    sec["idw_3_gauges"] = compare(I, "ld6", "lr6", np.random.default_rng(SEED + 22))
    (T / "secondary.json").write_text(json.dumps(sec, indent=1, default=str) + "\n")
    print(json.dumps({k: (v["D_LL"], v.get("D_LL_ci"), v["S"], v["S_condition"]) for k, v in sec.items()}, indent=0, default=str))

    # onset thresholds and the Auckland curve (training fits of D and R)
    tr = P[~P.test]; regions = sorted(P.region.unique())
    rows, curve = [], []
    for name, col, grid in (("R", "lr6", np.log1p(np.linspace(0, 4, 161))), ("D", "ld6", np.log1p(np.linspace(0, 250, 251)))):
        des = Design(tr, col, regions); b = fit(des.X(tr), tr.y.to_numpy())
        for g in [r for r in regions if r]:
            sub = tr[tr.region == g].sample(min(20000, int((tr.region == g).sum())), random_state=1)
            ps = []
            for x in grid:
                s2 = sub.copy(); s2[col] = x
                ps.append(float((1 / (1 + np.exp(-(des.X(s2) @ b)))).mean()))
            ps = np.array(ps); base = ps[0]
            hit = np.flatnonzero(ps >= 10 * base)
            onset = float(np.expm1(grid[hit[0]])) if len(hit) else None
            rows.append((g, name, base, onset))
            if g == "Auckland Region":
                curve += [(name, float(np.expm1(x)), p) for x, p in zip(grid, ps)]
    pd.DataFrame(rows, columns=["region", "model", "p_dry", "onset_10x"]).to_csv(T / "onset.csv", index=False)
    akl = P[(P.region == "Auckland Region") & (P.day == "2023-01-27")]
    pd.DataFrame(curve, columns=["model", "x", "p"]).to_csv(T / "auckland_curve.csv", index=False)
    (T / "auckland_2023_01_27.json").write_text(json.dumps({
        "suburbs": int(len(akl)), "with_callout": int(akl.y.sum()), "median_d6": float(akl.d6.median()),
        "median_r6": float((akl.d6 / akl.M6).median()), "max_d6": float(akl.d6.max())}, indent=1) + "\n")
    print("onset and Auckland curve written")


if __name__ == "__main__":
    main()
