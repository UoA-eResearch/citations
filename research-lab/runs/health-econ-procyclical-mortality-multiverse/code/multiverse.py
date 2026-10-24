"""Specification multiverse (plan sections 2-5).

  multiverse.py test   synthetic checks: beta recovery, closed-form WCR against a brute-force bootstrap, size under the null
  multiverse.py run    H1, H2 and the pre-2011 drug contrast on data/interim/panel.parquet -> results/tables/

Wild cluster restricted bootstrap in closed form: with x1 residualised on the nuisance set N = [Z, x2] (weighted), and
restricted residuals e_r = M_N y, a draw v (one Rademacher sign per state) gives
  beta* = sum_g v_g S_g / D,   S_g = sum_{i in g} x1_i e_r,i,   D = x1'x1
  score*_g = v_g S_g - sum_h C_gh v_h - beta* T_g,   C_gh = sum_{i in g} x1_i [H (e_r 1_h)]_i,   T_g = sum_{i in g} x1_i^2
so each specification costs one QR of N plus G x G x B arithmetic.
"""
import itertools
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import linalg, stats  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
INT, TAB = RUN / "data" / "interim", RUN / "results" / "tables"
B_MAIN, B_JOINT, SEED = 9999, 500, 20261024
CONTROLS = ["sh_u5", "sh_65", "sh_85", "sh_black"]

H1_DIMS = {"outcome": ["log_crude", "log_aadr", "crude"], "treat": ["ur", "epop_neg"], "weight": ["pop", "none"],
           "trend": ["none", "linear", "quadratic"], "lag": ["contemp", "cumulative"],
           "window": ["1976-2017", "1976-1991", "1992-2005", "2006-2017", "1976-2019", "1976-2023"],
           "estimator": ["twfe", "fd", "divyear"], "controls": ["none", "demog"]}
H2_DIMS = {**{k: v for k, v in H1_DIMS.items() if k not in ("outcome", "window")},
           "outcome": ["log_drug", "drug"], "window": ["2011-2019", "2011-2023"]}
PRE_DIMS = {**H2_DIMS, "window": ["1999-2010"]}


def specs(dims):
    keys = list(dims)
    out = []
    for combo in itertools.product(*dims.values()):
        s = dict(zip(keys, combo))
        a, b = map(int, s["window"].split("-"))
        if s["outcome"] == "log_aadr" and b >= 2018:
            continue
        out.append(s)
    return out


def outcome(P, name):
    if name == "log_crude":
        return np.log(P.crude.to_numpy())
    if name == "log_aadr":
        return np.log(P.aadr.to_numpy())
    if name == "crude":
        return P.crude.to_numpy()
    if name == "log_drug":
        d = P.drug.to_numpy()
        return np.where(d > 0, np.log(d), np.log(d + 1)) - np.log(P["pop"].to_numpy()) + np.log(1e5) \
            if (d == 0).any() else np.log(d / P["pop"].to_numpy() * 1e5)
    if name == "drug":
        return P.drug_crude.to_numpy()
    raise KeyError(name)


def design(P, s):
    """Return y, x1, x2 (or None), N (nuisance), w, cluster codes for one specification (unweighted arrays)."""
    a, b = map(int, s["window"].split("-"))
    P = P.sort_values(["state", "year"]).copy()
    P["y"] = outcome(P, s["outcome"])
    P["u"] = P[s["treat"]]
    g = P.groupby("state")
    P["u_l1"] = g.u.shift(1)
    P["y_l1"] = g.y.shift(1)
    P["pop_l1"] = g["pop"].shift(1)
    for c in CONTROLS:
        P[c + "_l1"] = g[c].shift(1)
    P["u_l2"] = g.u.shift(2)
    fd = s["estimator"] == "fd"
    lag = s["lag"] == "cumulative"
    first = a + (1 if (fd or lag) else 0)
    D = P[(P.year >= first) & (P.year <= b)].copy()
    if fd:
        y = (D.y - D.y_l1).to_numpy()
        x1 = (D.u - D.u_l1).to_numpy()
        x2 = ((D.u_l1 - D.u_l2) - (D.u - D.u_l1)).to_numpy() if lag else None
        ctrl = np.column_stack([(D[c] - D[c + "_l1"]).to_numpy() for c in CONTROLS]) if s["controls"] == "demog" else None
        w = ((D["pop"] + D.pop_l1) / 2).to_numpy()
    else:
        y = D.y.to_numpy()
        x1 = D.u.to_numpy()
        x2 = (D.u_l1 - D.u).to_numpy() if lag else None
        ctrl = D[CONTROLS].to_numpy() if s["controls"] == "demog" else None
        w = D["pop"].to_numpy()
    if s["weight"] == "none":
        w = np.ones_like(w)
    st = pd.Categorical(D.state).codes
    yr = D.year.to_numpy()
    t = (yr - yr.min()).astype(float)
    S = np.eye(st.max() + 1)[st]
    cols = []
    if s["estimator"] == "divyear":
        dy = pd.Categorical(D.division.astype(str) + "_" + D.year.astype(str)).codes
        cols.append(np.eye(dy.max() + 1)[dy])
    else:
        yc = pd.Categorical(yr).codes
        cols.append(np.eye(yc.max() + 1)[yc])
    if fd:
        if s["trend"] in ("linear", "quadratic"):
            cols.append(S)
        if s["trend"] == "quadratic":
            cols.append(S * t[:, None])
    else:
        cols.append(S)
        if s["trend"] in ("linear", "quadratic"):
            cols.append(S * t[:, None])
        if s["trend"] == "quadratic":
            cols.append(S * (t ** 2)[:, None])
    if ctrl is not None:
        cols.append(ctrl)
    if x2 is not None:
        cols.append(x2[:, None])
    N = np.column_stack(cols)
    ok = np.isfinite(y) & np.isfinite(x1) & np.isfinite(N).all(1) & np.isfinite(w)
    return y[ok], x1[ok], N[ok], w[ok], st[ok]


def estimate(y, x1, N, w, cl, V, VJ):
    """WLS beta on x1 with nuisance N; CR1 SE; WCR p from draws V (G x B); null t* from VJ (G x BJ)."""
    sw = np.sqrt(w)
    yw, xw, Nw = y * sw, x1 * sw, N * sw[:, None]
    Q, R, _ = linalg.qr(Nw, mode="economic", pivoting=True)
    d = np.abs(np.diag(R))
    r = int((d > d[0] * 1e-10).sum())
    Q = Q[:, :r]
    proj = lambda M: M - Q @ (Q.T @ M)
    yt, xt = proj(yw), proj(xw)
    Dn = xt @ xt
    beta = (xt @ yt) / Dn
    e = yt - xt * beta
    G = cl.max() + 1
    n = len(y)
    c = G / (G - 1) * (n - 1) / (n - r - 1)
    onehot = np.zeros((n, G))
    onehot[np.arange(n), cl] = 1.0
    sc = onehot.T @ (xt * e)
    se = np.sqrt(c * (sc @ sc)) / Dn
    tstat = beta / se
    p_cr1 = 2 * stats.t.sf(abs(tstat), G - 1)
    er = yt                                                    # restricted residuals under beta = 0
    Sg = onehot.T @ (xt * er)
    Tg = onehot.T @ (xt * xt)
    E = onehot * er[:, None]                                   # n x G: e_r restricted to each cluster
    A = Q @ (Q.T @ E)                                          # H (e_r 1_h)
    C = onehot.T @ (xt[:, None] * A)                           # G x G

    def tstar(VV):
        bstar = (Sg @ VV) / Dn
        scs = Sg[:, None] * VV - C @ VV - Tg[:, None] * bstar[None, :]
        return bstar / (np.sqrt(c * (scs ** 2).sum(0)) / Dn)

    p_wcr = float(np.mean(np.abs(tstar(V)) >= abs(tstat)))
    tj = tstar(VJ) if VJ is not None else None
    return {"beta": float(beta), "se": float(se), "t": float(tstat), "p_cr1": float(p_cr1), "p_wcr": p_wcr,
            "n": int(n), "k": int(r + 1), "G": int(G)}, tj


def draws(G, B, seed):
    return np.random.default_rng(seed).choice([-1.0, 1.0], size=(G, B))


# ---------------------------------------------------------------- tests
def brute_wcr(y, x1, N, w, cl, V):
    sw = np.sqrt(w)
    yw, xw, Nw = y * sw, x1 * sw, N * sw[:, None]
    X = np.column_stack([xw, Nw])
    fit_r = Nw @ np.linalg.lstsq(Nw, yw, rcond=None)[0]
    er = yw - fit_r
    G = cl.max() + 1
    n = len(y)
    r = np.linalg.matrix_rank(Nw)
    c = G / (G - 1) * (n - 1) / (n - r - 1)

    def t_of(yy):
        coef = np.linalg.lstsq(X, yy, rcond=None)[0]
        e = yy - X @ coef
        Nx = Nw @ np.linalg.lstsq(Nw, xw, rcond=None)[0]
        xt = xw - Nx
        sc = np.bincount(cl, weights=xt * e, minlength=G)
        return coef[0] / (np.sqrt(c * (sc @ sc)) / (xt @ xt))

    t0 = t_of(yw)
    ts = np.array([t_of(fit_r + V[cl, b] * er) for b in range(V.shape[1])])
    return t0, float(np.mean(np.abs(ts) >= abs(t0)))


def synth(beta, seed, G=51, T=30):
    rng = np.random.default_rng(seed)
    st = np.repeat(np.arange(G), T)
    yr = np.tile(np.arange(T), G)
    u = 5 + rng.normal(0, 1, G)[st] + rng.normal(0, 1.5, T)[yr] + np.cumsum(rng.normal(0, 0.5, (G, T)), 1).ravel()
    eps_state = rng.normal(0, 0.02, (G, 1)) * np.ones((1, T))
    ar = np.zeros((G, T))
    for k in range(1, T):
        ar[:, k] = 0.6 * ar[:, k - 1] + rng.normal(0, 0.01, G)
    y = 6.5 + rng.normal(0, 0.1, G)[st] + 0.01 * rng.normal(0, 1, T)[yr] + beta * u + ar.ravel() + eps_state.ravel()
    return pd.DataFrame({"state": [f"S{s:02d}" for s in st], "year": 1990 + yr, "ur": u, "epop_neg": -u,
                         "crude": np.exp(y), "aadr": np.exp(y), "pop": rng.integers(5e5, 3e7, G)[st].astype(float),
                         "drug": np.exp(y - 4) * rng.integers(5e5, 3e7, G)[st] / 1e5, "drug_crude": np.exp(y - 4),
                         "sh_u5": rng.uniform(.05, .08, G * T), "sh_65": rng.uniform(.1, .2, G * T),
                         "sh_85": rng.uniform(.01, .03, G * T), "sh_black": rng.uniform(.01, .3, G * T),
                         "division": (np.arange(G) % 9)[st] + 1})


def test():
    out = {}
    s = {"outcome": "log_crude", "treat": "ur", "weight": "pop", "trend": "linear", "lag": "cumulative", "window": "1990-2019",
         "estimator": "twfe", "controls": "demog"}
    P = synth(-0.004, 1)
    y, x1, N, w, cl = design(P, s)
    V = draws(cl.max() + 1, 199, 7)
    r, _ = estimate(y, x1, N, w, cl, V, None)
    t0, pb = brute_wcr(y, x1, N, w, cl, V)
    out["closed_vs_brute"] = {"t_closed": round(r["t"], 6), "t_brute": round(float(t0), 6), "p_closed": r["p_wcr"], "p_brute": pb}
    assert abs(r["t"] - t0) < 1e-6 and abs(r["p_wcr"] - pb) < 1e-9, out
    for est in ("fd", "divyear"):
        s2 = {**s, "estimator": est, "trend": "quadratic"}
        y, x1, N, w, cl = design(P, s2)
        r2, _ = estimate(y, x1, N, w, cl, V, None)
        t0, pb = brute_wcr(y, x1, N, w, cl, V)
        assert abs(r2["t"] - t0) < 1e-6 and abs(r2["p_wcr"] - pb) < 1e-9, (est, r2, t0, pb)
    # recovery and size
    rej_cr1, rej_wcr, bias = [], [], []
    Vm = draws(51, 999, 8)
    for k in range(200):
        Pk = synth(0.0 if k % 2 else -0.004, 100 + k)
        sk = {**s, "lag": "contemp", "trend": "none", "controls": "none"}
        r, _ = estimate(*design(Pk, sk), Vm, None)
        if k % 2:
            rej_cr1.append(r["p_cr1"] < 0.05); rej_wcr.append(r["p_wcr"] < 0.05)
        else:
            bias.append(r["beta"] + 0.004)
    out["null_rejection_cr1"] = round(float(np.mean(rej_cr1)), 3)
    out["null_rejection_wcr"] = round(float(np.mean(rej_wcr)), 3)
    out["recovery_mean_error"] = round(float(np.mean(bias)), 6)
    (TAB / "synthetic_test.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


# ---------------------------------------------------------------- run
def _work(args):
    P, s, V, VJ = args
    r, tj = estimate(*design(P, s), V, VJ)
    return {**s, **r}, (tj if tj is not None else None)


def run_family(P, dims, label, V, VJ, workers):
    sp = specs(dims)
    with ProcessPoolExecutor(workers, mp_context=__import__("multiprocessing").get_context("spawn")) as ex:
        res = list(ex.map(_work, [(P, s, V, VJ) for s in sp], chunksize=16))
    df = pd.DataFrame([r for r, _ in res])
    df.to_csv(TAB / f"specs_{label}.csv", index=False)
    tj = np.vstack([t for _, t in res]) if VJ is not None else None
    return df, tj, len(list(itertools.product(*dims.values())))


def decompose(df, P, dims, sign):
    sd = {}
    for (o, wdw) in df[["outcome", "window"]].drop_duplicates().itertuples(index=False):
        a, b = map(int, wdw.split("-"))
        sd[(o, wdw)] = float(np.nanstd(outcome(P[(P.year >= a) & (P.year <= b)], o)))
    z = df.beta / [sd[(o, w)] for o, w in zip(df.outcome, df.window)]
    hit = (np.sign(df.beta) == sign) & (df.p_wcr < 0.05)
    by = {d: {opt: round(float(hit[df[d] == opt].mean()), 4) for opt in dims[d]} for d in dims}
    X = pd.get_dummies(df[list(dims)], drop_first=True).astype(float)
    full = np.linalg.lstsq(np.column_stack([np.ones(len(X)), X]), z, rcond=None)
    r2 = lambda M: 1 - np.sum((z - M @ np.linalg.lstsq(M, z, rcond=None)[0]) ** 2) / np.sum((z - z.mean()) ** 2)
    R2 = r2(np.column_stack([np.ones(len(X)), X]))
    drop = {}
    for d in dims:
        keep = [c for c in X.columns if not c.startswith(d + "_")]
        drop[d] = round(float(R2 - r2(np.column_stack([np.ones(len(X)), X[keep]]))), 4)
    return {"share_by_option": by, "r2_main_effects": round(float(R2), 4), "r2_drop_by_dimension": drop}


def run():
    P = pd.read_parquet(INT / "panel.parquet")
    P = P[P.year >= 1975]
    workers = int(os.environ.get("WORKERS", "8"))
    G = P.state.nunique()
    V, VJ = draws(G, B_MAIN, SEED), draws(G, B_JOINT, SEED + 1)
    crit = stats.t.ppf(0.975, G - 1)
    out = {"B": B_MAIN, "B_joint": B_JOINT, "G": G}
    h1, tj1, n_all1 = run_family(P, H1_DIMS, "h1", V, VJ, workers)
    neg_sig = (h1.beta < 0) & (h1.p_wcr < 0.05)
    S1 = float(neg_sig.mean())
    out["H1"] = {"specs": int(len(h1)), "combinations": n_all1, "excluded": n_all1 - int(len(h1)),
                 "S1_wcr": round(S1, 4), "S1_cr1": round(float(((h1.beta < 0) & (h1.p_cr1 < 0.05)).mean()), 4),
                 "share_negative": round(float((h1.beta < 0).mean()), 4),
                 "share_positive_significant_wcr": round(float(((h1.beta > 0) & (h1.p_wcr < 0.05)).mean()), 4),
                 "verdict": "Supported" if S1 < 0.40 else "Refuted" if S1 > 0.60 else "Inconclusive"}
    null_share = (tj1 < -crit).mean(0)
    obs_cr1 = float(((h1.beta < 0) & (h1.p_cr1 < 0.05)).mean())
    out["H1"]["joint_test"] = {"observed_S1_cr1": round(obs_cr1, 4), "null_median": round(float(np.median(null_share)), 4),
                               "null_p95": round(float(np.percentile(null_share, 95)), 4),
                               "p_value": round(float(np.mean(null_share >= obs_cr1)), 4)}
    out["H1"]["decomposition"] = decompose(h1, P, H1_DIMS, -1)
    canon = h1[(h1.outcome == "log_crude") & (h1.treat == "ur") & (h1.weight == "pop") & (h1.trend == "none") &
               (h1.lag == "contemp") & (h1.estimator == "twfe") & (h1.controls == "demog")]
    out["canonical_by_window"] = {r.window: {"beta": round(r.beta, 5), "ci95_cr1": [round(r.beta - crit * r.se, 5), round(r.beta + crit * r.se, 5)],
                                             "p_cr1": round(r.p_cr1, 4), "p_wcr": round(r.p_wcr, 4)} for r in canon.itertuples()}
    h2, _, n_all2 = run_family(P, H2_DIMS, "h2", V, None, workers)
    pos_sig = (h2.beta > 0) & (h2.p_wcr < 0.05)
    S2 = float(pos_sig.mean())
    out["H2"] = {"specs": int(len(h2)), "combinations": n_all2, "S2_wcr": round(S2, 4),
                 "S2_cr1": round(float(((h2.beta > 0) & (h2.p_cr1 < 0.05)).mean()), 4),
                 "share_positive": round(float((h2.beta > 0).mean()), 4),
                 "share_negative_significant_wcr": round(float(((h2.beta < 0) & (h2.p_wcr < 0.05)).mean()), 4),
                 "verdict": "Supported" if S2 > 0.60 else "Refuted" if S2 < 0.40 else "Inconclusive",
                 "decomposition": decompose(h2, P, H2_DIMS, 1)}
    pre, _, _ = run_family(P, PRE_DIMS, "drug_pre2011", V, None, workers)
    out["drug_pre2011"] = {"specs": int(len(pre)), "share_positive_significant_wcr": round(float(((pre.beta > 0) & (pre.p_wcr < 0.05)).mean()), 4),
                           "share_negative_significant_wcr": round(float(((pre.beta < 0) & (pre.p_wcr < 0.05)).mean()), 4)}
    out["zero_drug_cells"] = int((P[P.year >= 1999].drug == 0).sum())
    (TAB / "primary.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: out[k] for k in ("H1", "H2", "drug_pre2011")}, indent=1, default=str)[:4000])


if __name__ == "__main__":
    {"test": test, "run": run}[sys.argv[1]]()
