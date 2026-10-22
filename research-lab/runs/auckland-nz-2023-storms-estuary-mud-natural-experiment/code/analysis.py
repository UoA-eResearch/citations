"""H1, H2 and the secondary analyses (plan sections 3-4). Run only after results/tables/exposure.csv is committed.

Panel: mud content per site and year, 2010-2024, for the 56 frozen sites.
- H1: site and year fixed effects; top- and bottom-tercile sites; beta on Top x 1[2023], gamma on Top x 1[2024].
- H2: all sites; delta on E x 1[2023] and eta on E x 1[2024]; delta reported per IQR of E.
- Inference: wild cluster restricted bootstrap by harbour (Webb six-point weights, B = 9,999, seed 20261023), CR1
  t statistics; the 95% interval by test inversion (bisection on the imposed null). CR2 (Bell-McCaffrey) standard
  errors with t(G-1) intervals alongside.

Writes results/tables/primary.json and results/tables/event_study.csv.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"
B, SEED = 9999, 20261023
WEBB = np.array([-np.sqrt(1.5), -1.0, -np.sqrt(0.5), np.sqrt(0.5), 1.0, np.sqrt(1.5)])


def load(indicator="Mud_content", drop_year_only=False):
    d = pd.read_excel(RUN / "data" / "raw" / "lawa_estuary_2025v2.xlsx", sheet_name="Data")
    d = d[(d["Council/Agency"] == "Auckland Council") & (d.Indicator == indicator)].copy()
    dt = pd.to_datetime(d["Date sampled (YYYY/MM/DD)"])
    d["year"] = dt.dt.year
    if drop_year_only:
        d = d[~((dt.dt.month == 1) & (dt.dt.day == 1))]
    d["y"] = pd.to_numeric(d["Indicator value"], errors="coerce")
    d = d.rename(columns={"LAWA Site ID": "site_id"})[["site_id", "year", "y"]].dropna()
    s = pd.read_csv(T / "sites.csv")[["site_id", "estuary"]]
    e = pd.read_csv(T / "exposure.csv")
    d = d[(d.year >= 2010) & (d.year <= 2024)].merge(s, on="site_id").merge(e, on="site_id")
    return d


def design(d, terms):
    """Site and year dummies (first of each dropped) plus the named treatment columns, in that order last."""
    X = pd.concat([pd.get_dummies(d.site_id, prefix="s", drop_first=False, dtype=float),
                   pd.get_dummies(d.year, prefix="y", drop_first=True, dtype=float),
                   d[terms].astype(float)], axis=1)
    return X.to_numpy(), list(X.columns)


def ols(X, Y):
    XtX_inv = np.linalg.pinv(X.T @ X)
    return XtX_inv, XtX_inv @ X.T @ Y


def cr1_se(X, XtX_inv, U, groups, j):
    """CR1 standard error of coefficient j for each column of residual matrix U (n x m)."""
    G = len(np.unique(groups))
    n, k = X.shape
    a = XtX_inv[j] @ X.T                                        # row j of (X'X)^-1 X'
    s = np.zeros(U.shape[1])
    for g in np.unique(groups):
        m = groups == g
        s += (a[m] @ U[m]) ** 2
    c = G / (G - 1) * (n - 1) / (n - k)
    return np.sqrt(c * s)


def cr2_se(X, XtX_inv, u, groups, j):
    a = XtX_inv[j] @ X.T
    v = 0.0
    for g in np.unique(groups):
        m = groups == g
        Xg = X[m]
        Hgg = Xg @ XtX_inv @ Xg.T
        w, Q = np.linalg.eigh(np.eye(m.sum()) - Hgg)
        A = Q @ np.diag(1 / np.sqrt(np.clip(w, 1e-12, None))) @ Q.T
        v += (a[m] @ A @ u[m]) ** 2
    return float(np.sqrt(v))


def wild_p(X, y, groups, j, b0, W):
    """Wild cluster restricted bootstrap p-value for H0: beta_j = b0 (CR1 t statistics)."""
    XtX_inv, b = ols(X, y)
    t_obs = (b[j] - b0) / cr1_se(X, XtX_inv, (y - X @ b)[:, None], groups, j)[0]
    Xr = np.delete(X, j, axis=1)
    yr = y - b0 * X[:, j]
    _, br = ols(Xr, yr)
    fit_r, ur = Xr @ br + b0 * X[:, j], yr - Xr @ br
    gidx = pd.factorize(groups)[0]
    Ys = fit_r[:, None] + ur[:, None] * W[gidx]
    Bs = XtX_inv @ X.T @ Ys
    Us = Ys - X @ Bs
    ts = (Bs[j] - b0) / cr1_se(X, XtX_inv, Us, groups, j)
    return float(np.mean(np.abs(ts) >= abs(t_obs)))


def wild_ci(X, y, groups, j, W, alpha=0.05):
    XtX_inv, b = ols(X, y)
    se = cr1_se(X, XtX_inv, (y - X @ b)[:, None], groups, j)[0]

    def bound(sign):
        lo, hi = b[j], b[j] + sign * 20 * se                    # p(lo) > alpha, p(hi) < alpha
        while wild_p(X, y, groups, j, hi, W) >= alpha:
            hi = b[j] + 2 * (hi - b[j])
        for _ in range(30):
            mid = (lo + hi) / 2
            if wild_p(X, y, groups, j, mid, W) >= alpha:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2
    return [round(float(bound(-1)), 3), round(float(bound(+1)), 3)]


def fit(d, terms, j_terms, W):
    X, names = design(d, terms)
    y = d.y.to_numpy(float)
    groups = d.estuary.to_numpy()
    XtX_inv, b = ols(X, y)
    u = y - X @ b
    G = len(np.unique(groups))
    from scipy import stats
    out = {"n_obs": int(len(d)), "sites": int(d.site_id.nunique()), "harbours": int(G)}
    for t in j_terms:
        j = names.index(t)
        se2 = cr2_se(X, XtX_inv, u, groups, j)
        tc = stats.t.ppf(0.975, G - 1)
        out[t] = {"estimate": round(float(b[j]), 3), "wild_ci": wild_ci(X, y, groups, j, W),
                  "wild_p_zero": round(wild_p(X, y, groups, j, 0.0, W), 4),
                  "cr2_se": round(se2, 3), "cr2_ci": [round(float(b[j] - tc * se2), 3), round(float(b[j] + tc * se2), 3)]}
    return out


def weights(G):
    rng = np.random.default_rng(SEED)
    return rng.choice(WEBB, size=(G, B))


def h1(d, W, ecol="E_route_5", tcol="tercile"):
    x = d[d[tcol].isin(["top", "bottom"])].copy()
    x["top"] = (x[tcol] == "top").astype(float)
    x["top_2023"] = x.top * (x.year == 2023)
    x["top_2024"] = x.top * (x.year == 2024)
    return fit(x, ["top_2023", "top_2024"], ["top_2023", "top_2024"], W)


def h2(d, W, ecol="E_route_5"):
    x = d[d[ecol].notna()].copy()
    x["E_2023"] = x[ecol] * (x.year == 2023)
    x["E_2024"] = x[ecol] * (x.year == 2024)
    return fit(x, ["E_2023", "E_2024"], ["E_2023", "E_2024"], W)


def verdict_h1(r):
    lo, hi = r["top_2023"]["wild_ci"]
    est = r["top_2023"]["estimate"]
    return "Supported" if (est >= 4 and lo > 0) else "Refuted" if hi < 4 else "Inconclusive"


def verdict_h2(r, iqr):
    lo, hi = [v * iqr for v in r["E_2023"]["wild_ci"]]
    return "Supported" if lo > 0 else "Refuted" if hi < 1 else "Inconclusive"


def terciles(e):
    o = e.rank(method="first")
    n = e.notna().sum()
    t = pd.cut(o, [0, n / 3, 2 * n / 3, n], labels=["bottom", "middle", "top"]).astype(str)
    return t.where(e.notna(), "none")


def main():
    d = load()
    G = d.estuary.nunique()
    W = weights(G)
    ex = pd.read_csv(T / "exposure.csv")
    iqr = float(ex.E_route_5.quantile(0.75) - ex.E_route_5.quantile(0.25))
    out = {"panel": {"rows": int(len(d)), "sites": int(d.site_id.nunique()), "harbours": int(G),
                     "years": [int(d.year.min()), int(d.year.max())]}}
    r1 = h1(d, W)
    out["H1"] = {**r1, "verdict": verdict_h1(r1)}
    r2 = h2(d, W)
    out["H2"] = {**r2, "E_iqr": round(iqr, 5),
                 "delta_per_iqr": round(r2["E_2023"]["estimate"] * iqr, 3),
                 "delta_per_iqr_wild_ci": [round(v * iqr, 3) for v in r2["E_2023"]["wild_ci"]],
                 "eta_per_iqr": round(r2["E_2024"]["estimate"] * iqr, 3),
                 "eta_per_iqr_wild_ci": [round(v * iqr, 3) for v in r2["E_2024"]["wild_ci"]],
                 "verdict": verdict_h2(r2, iqr)}
    # event study (descriptive): top minus bottom of site-demeaned mud, by year, relative to each site's 2010-2022 mean
    base = d[d.year <= 2022].groupby("site_id").y.mean()
    z = d.assign(dev=d.y - d.site_id.map(base))
    es = z[z.tercile.isin(["top", "bottom"])].groupby(["year", "tercile"]).dev.mean().unstack()
    es["top_minus_bottom"] = es["top"] - es["bottom"]
    es.round(3).to_csv(T / "event_study.csv")
    # placebos: pseudo-event years on pre-2023 data
    pl = {}
    pre = d[d.year <= 2022]
    for P in range(2015, 2022):
        x = pre[pre.tercile.isin(["top", "bottom"])].copy()
        x["top_P"] = (x.tercile == "top").astype(float) * (x.year == P)
        X, names = design(x, ["top_P"])
        _, b = ols(X, x.y.to_numpy(float))
        pl[P] = round(float(b[names.index("top_P")]), 3)
    out["placebo_beta"] = pl
    out["placebo_abs_ge_beta_share"] = round(float(np.mean([abs(v) >= abs(out["H1"]["top_2023"]["estimate"])
                                                            for v in pl.values()])), 3)
    # leave one harbour out
    loo = {}
    for h in sorted(d.estuary.unique()):
        x = d[d.estuary != h]
        Wx = weights(x.estuary.nunique())
        a = h1(x, Wx) if x[x.tercile == "top"].estuary.nunique() and x[x.tercile == "bottom"].estuary.nunique() else None
        X, names = design(x.assign(E_2023=x.E_route_5 * (x.year == 2023), E_2024=x.E_route_5 * (x.year == 2024)),
                          ["E_2023", "E_2024"])
        _, b = ols(X, x.y.to_numpy(float))
        loo[h] = {"beta": a["top_2023"]["estimate"] if a else None,
                  "delta_per_iqr": round(float(b[names.index("E_2023")] * iqr), 3)}
    out["leave_one_harbour_out"] = loo
    # exposure definitions
    sens = {}
    for col in ("E_route_2", "E_route_10", "E_radius_2", "E_radius_5", "E_radius_10"):
        x = d.copy()
        x["t2"] = terciles(x.drop_duplicates("site_id").set_index("site_id")[col]).reindex(x.site_id).to_numpy()
        a = h1(x, W, tcol="t2")
        b2 = h2(x, W, ecol=col)
        iq = float(ex[col].quantile(0.75) - ex[col].quantile(0.25))
        sens[col] = {"beta": a["top_2023"]["estimate"], "beta_wild_ci": a["top_2023"]["wild_ci"],
                     "delta_per_iqr": round(b2["E_2023"]["estimate"] * iq, 3),
                     "delta_per_iqr_wild_ci": [round(v * iq, 3) for v in b2["E_2023"]["wild_ci"]]}
    out["exposure_definitions"] = sens
    # year-only rows dropped
    dy = load(drop_year_only=True)
    a = h1(dy, weights(dy.estuary.nunique()))
    out["drop_year_only_rows"] = {"rows": int(len(dy)), "beta": a["top_2023"]["estimate"], "beta_wild_ci": a["top_2023"]["wild_ci"]}
    # other outcomes
    oth = {}
    for ind in ("Macrofauna", "Copper", "Zinc", "Lead"):
        x = load(ind)
        n_top = int(((x.year == 2023) & (x.tercile == "top")).sum())
        n_bot = int(((x.year == 2023) & (x.tercile == "bottom")).sum())
        if x.empty or n_top < 3 or n_bot < 3:          # D4: otherwise the 2023 contrast is not estimable
            oth[ind] = {"rows": int(len(x)), "rows_2023": int((x.year == 2023).sum()), "rows_2023_top": n_top,
                        "rows_2023_bottom": n_bot, "note": "not estimable: fewer than 3 top and 3 bottom rows in 2023"}
            continue
        Wx = weights(x.estuary.nunique())
        a = h1(x, Wx)
        oth[ind] = {"rows": int(len(x)), "rows_2023": int((x.year == 2023).sum()),
                    "beta_2023": a["top_2023"]["estimate"], "beta_2023_wild_ci": a["top_2023"]["wild_ci"],
                    "gamma_2024": a["top_2024"]["estimate"], "gamma_2024_wild_ci": a["top_2024"]["wild_ci"]}
    out["other_outcomes"] = oth
    json.dump(out, open(T / "primary.json", "w"), indent=1)
    print(json.dumps({k: out[k] for k in ("panel", "H1", "H2")}, indent=1))


if __name__ == "__main__":
    main()
