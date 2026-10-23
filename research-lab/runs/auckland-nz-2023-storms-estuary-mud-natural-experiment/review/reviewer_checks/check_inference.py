"""Reviewer check 2: the wild cluster restricted bootstrap, the H2 wild-vs-CR2 gap, leverage, and verdict dependence.

Independent re-implementation of the restricted wild cluster bootstrap (not calling the study's wild_p), plus the
study's own functions for a determinism check. Writes stdout -> check_inference.out.
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

RUN = Path("/mnt/citations/research-lab/runs/auckland-nz-2023-storms-estuary-mud-natural-experiment")
T = RUN / "results" / "tables"
sys.path.insert(0, str(RUN / "code"))
import analysis as A  # noqa: E402

WEBB = np.array([-np.sqrt(1.5), -1.0, -np.sqrt(0.5), np.sqrt(0.5), 1.0, np.sqrt(1.5)])


def cr1(X, XtX_inv, U, gidx, j, G):
    """CR1 SE of coefficient j for each column of U (n x m) -- independent implementation via per-cluster sums."""
    n, k = X.shape
    a = XtX_inv[j] @ X.T
    S = np.zeros((G, U.shape[1]))
    np.add.at(S, gidx, a[:, None] * U)          # sum_g (a_g' u_g)
    return np.sqrt(G / (G - 1) * (n - 1) / (n - k) * (S ** 2).sum(0))


def wild_p_indep(X, y, gidx, j, b0, W):
    """Restricted wild cluster bootstrap p for H0: b_j = b0; Webb weights W (G x B)."""
    G = W.shape[0]
    XtX_inv = np.linalg.pinv(X.T @ X)
    b = XtX_inv @ X.T @ y
    t_obs = (b[j] - b0) / cr1(X, XtX_inv, (y - X @ b)[:, None], gidx, j, G)[0]
    Xr = np.delete(X, j, 1)
    yr = y - b0 * X[:, j]
    br = np.linalg.pinv(Xr.T @ Xr) @ Xr.T @ yr
    ur = yr - Xr @ br
    fit = Xr @ br + b0 * X[:, j]
    Ys = fit[:, None] + ur[:, None] * W[gidx]
    Bs = XtX_inv @ X.T @ Ys
    ts = (Bs[j] - b0) / cr1(X, XtX_inv, Ys - X @ Bs, gidx, j, G)
    return float(np.mean(np.abs(ts) >= abs(t_obs))), float(b[j])


def grid_ci(X, y, gidx, j, W, grid):
    ps = np.array([wild_p_indep(X, y, gidx, j, g, W)[0] for g in grid])
    inside = grid[ps >= 0.05]
    return (inside.min(), inside.max()) if len(inside) else (np.nan, np.nan), ps


def cr2(X, XtX_inv, u, gidx, j, G):
    a = XtX_inv[j] @ X.T
    v = 0.0
    for g in range(G):
        m = gidx == g
        Hgg = X[m] @ XtX_inv @ X[m].T
        w, Q = np.linalg.eigh(np.eye(m.sum()) - Hgg)
        Ahalf = Q @ np.diag(1 / np.sqrt(np.clip(w, 1e-12, None))) @ Q.T
        v += (a[m] @ Ahalf @ u[m]) ** 2
    return float(np.sqrt(v))


def cv3(X, y, gidx, j, G):
    """Jackknife (leave-one-cluster-out) cluster-robust SE, CV3 of MacKinnon, Nielsen & Webb."""
    b = np.linalg.pinv(X.T @ X) @ X.T @ y
    bs = []
    for g in range(G):
        m = gidx != g
        bs.append((np.linalg.pinv(X[m].T @ X[m]) @ X[m].T @ y[m])[j])
    bs = np.array(bs)
    return float(np.sqrt((G - 1) / G * ((bs - bs.mean()) ** 2).sum())), bs


def setup_h1(d, tcol="tercile"):
    x = d[d[tcol].isin(["top", "bottom"])].copy()
    x["top"] = (x[tcol] == "top").astype(float)
    x["top_2023"] = x.top * (x.year == 2023)
    x["top_2024"] = x.top * (x.year == 2024)
    X, names = A.design(x, ["top_2023", "top_2024"])
    return x, X, names


def setup_h2(d, ecol="E_route_5"):
    x = d.copy()
    x["E_2023"] = x[ecol] * (x.year == 2023)
    x["E_2024"] = x[ecol] * (x.year == 2024)
    X, names = A.design(x, ["E_2023", "E_2024"])
    return x, X, names


def main():
    t0 = time.time()
    d = A.load()
    ex = pd.read_csv(T / "exposure.csv")
    iqr = float(ex.E_route_5.quantile(0.75) - ex.E_route_5.quantile(0.25))
    print("IQR of E_route_5:", iqr, "; range/IQR =", round((ex.E_route_5.max() - ex.E_route_5.min()) / iqr, 1))

    print("\n== A. study's own functions: determinism of wild_p at 0 (primary.json: H1 0.2813, H2 0.3647) ==")
    W13 = A.weights(d.estuary.nunique())
    x1, X1, n1 = setup_h1(d)
    y1, g1 = x1.y.to_numpy(float), x1.estuary.to_numpy()
    j1 = n1.index("top_2023")
    print("H1 wild_p(0) study code:", A.wild_p(X1, y1, g1, j1, 0.0, W13))
    x2, X2, n2 = setup_h2(d)
    y2, g2 = x2.y.to_numpy(float), x2.estuary.to_numpy()
    j2 = n2.index("E_2023")
    print("H2 wild_p(0) study code:", A.wild_p(X2, y2, g2, j2, 0.0, W13))
    print("Webb weights in study code:", np.round(A.WEBB, 4), "; W shape", W13.shape, "; unique values used:", np.unique(W13).size)

    print("\n== B. independent restricted wild cluster bootstrap (new seed, B = 4999) ==")
    rng = np.random.default_rng(777)
    gi1 = pd.factorize(g1)[0]; G1 = gi1.max() + 1
    gi2 = pd.factorize(g2)[0]; G2 = gi2.max() + 1
    Wi1 = rng.choice(WEBB, size=(G1, 4999))
    Wi2 = rng.choice(WEBB, size=(G2, 4999))
    p1, b1 = wild_p_indep(X1, y1, gi1, j1, 0.0, Wi1)
    p2, b2 = wild_p_indep(X2, y2, gi2, j2, 0.0, Wi2)
    print(f"H1: beta = {b1:.3f}, p(0) = {p1:.3f}   (study 1.932, 0.2813)")
    print(f"H2: delta = {b2:.1f} per unit E -> {b2 * iqr:.3f} per IQR, p(0) = {p2:.3f}   (study -0.209, 0.3647)")
    grid1 = np.round(np.arange(-4.0, 8.01, 0.25), 3)
    (lo1, hi1), ps1 = grid_ci(X1, y1, gi1, j1, Wi1, grid1)
    print(f"H1 grid 95% CI (0.25 pp grid): [{lo1}, {hi1}]  (study wild_ci -2.331, 5.666)")
    print("   p-curve:", " ".join(f"{g:+.2f}:{p:.2f}" for g, p in zip(grid1, ps1) if abs(g % 1.0) < 1e-9))
    grid2 = np.round(np.arange(-6.0, 6.01, 0.25), 3) / iqr          # per-IQR grid -> per unit E
    (lo2, hi2), ps2 = grid_ci(X2, y2, gi2, j2, Wi2, grid2)
    print(f"H2 grid 95% CI per IQR: [{lo2 * iqr:.2f}, {hi2 * iqr:.2f}]  (study -3.062, 3.195)")
    print("   p-curve (per IQR):", " ".join(f"{g * iqr:+.2f}:{p:.2f}" for g, p in zip(grid2, ps2) if abs((g * iqr) % 1.0) < 1e-6))
    print(f"[{time.time() - t0:.0f} s]")

    print("\n== C. CR2 and CV3 (jackknife) reference intervals ==")
    for name, X, y, gi, G, j, scale in (("H1 top_2023", X1, y1, gi1, G1, j1, 1.0), ("H2 E_2023 per IQR", X2, y2, gi2, G2, j2, iqr)):
        XtX_inv = np.linalg.pinv(X.T @ X)
        b = XtX_inv @ X.T @ y
        u = y - X @ b
        se2 = cr2(X, XtX_inv, u, gi, j, G)
        se1 = cr1(X, XtX_inv, u[:, None], gi, j, G)[0]
        se3, bs = cv3(X, y, gi, j, G)
        tc = stats.t.ppf(0.975, G - 1)
        print(f"{name}: est {b[j] * scale:+.3f}; CR1 se {se1 * scale:.3f}; CR2 se {se2 * scale:.3f} -> [{(b[j] - tc * se2) * scale:+.2f}, {(b[j] + tc * se2) * scale:+.2f}];"
              f" CV3 se {se3 * scale:.3f} -> [{(b[j] - tc * se3) * scale:+.2f}, {(b[j] + tc * se3) * scale:+.2f}]")
        print("   leave-one-cluster-out estimates:", np.round(bs * scale, 2))

    print("\n== D. H2 leverage: where does the identifying variation in E x 2023 come from? ==")
    # FWL: partial site and year dummies (and E_2024) out of E_2023
    others = [i for i in range(X2.shape[1]) if i != j2]
    Z = X2[:, others]
    e_t = X2[:, j2] - Z @ (np.linalg.pinv(Z.T @ Z) @ Z.T @ X2[:, j2])
    ss = pd.Series(e_t ** 2, index=x2.index)
    by_h = ss.groupby(x2.estuary).sum() / ss.sum()
    print("share of partialled-out SS by harbour:", by_h.sort_values(ascending=False).round(3).head(5).to_dict())
    by_s = ss.groupby(x2.site_id).sum() / ss.sum()
    nm = pd.read_csv(T / "sites.csv").set_index("site_id").site_name
    print("share by site (top 5):", {nm[k]: round(v, 3) for k, v in by_s.sort_values(ascending=False).head(5).items()})
    # Carter-Schnepel-Steigerwald effective number of clusters for the E_2023 coefficient
    XtX_inv = np.linalg.pinv(X2.T @ X2)
    a = XtX_inv[j2] @ X2.T
    gam = np.array([(a[gi2 == g] ** 2).sum() for g in range(G2)])
    gam = gam / gam.mean()
    G_star = G2 / (1 + ((gam - 1) ** 2).mean())
    print(f"effective number of clusters G* (CSS 2017, homoskedastic): {G_star:.1f} of {G2}")
    a1 = np.linalg.pinv(X1.T @ X1)[j1] @ X1.T
    gam1 = np.array([(a1[gi1 == g] ** 2).sum() for g in range(G1)]); gam1 /= gam1.mean()
    print(f"H1 G*: {G1 / (1 + ((gam1 - 1) ** 2).mean()):.1f} of {G1}")

    print("\n== E. H2 without the high-leverage sites (report: dropping the Airport gives -0.18, CR2 +/-0.75) ==")
    for label, drop in (("drop Auckland Airport", ["LAWA-103146"]), ("drop Airport and Clarks Beach", ["LAWA-103146", "LAWA-103148"])):
        dd = d[~d.site_id.isin(drop)]
        xx, XX, nn = setup_h2(dd)
        yy, gg = xx.y.to_numpy(float), xx.estuary.to_numpy()
        gii = pd.factorize(gg)[0]; GG = gii.max() + 1
        jj = nn.index("E_2023")
        Wd = rng.choice(WEBB, size=(GG, 4999))
        p, b = wild_p_indep(XX, yy, gii, jj, 0.0, Wd)
        XtX_inv = np.linalg.pinv(XX.T @ XX); bb = XtX_inv @ XX.T @ yy; uu = yy - XX @ bb
        se2 = cr2(XX, XtX_inv, uu, gii, jj, GG)
        tc = stats.t.ppf(0.975, GG - 1)
        iqr_d = float(xx.drop_duplicates("site_id").E_route_5.quantile(0.75) - xx.drop_duplicates("site_id").E_route_5.quantile(0.25))
        gridd = np.round(np.arange(-6.0, 6.01, 0.25), 3) / iqr
        (lo, hi), _ = grid_ci(XX, yy, gii, jj, Wd, gridd)
        print(f"{label}: delta per full-sample IQR {b * iqr:+.3f} (per own IQR {b * iqr_d:+.3f}); wild p(0) {p:.3f}; wild grid CI [{lo * iqr:+.2f}, {hi * iqr:+.2f}];"
              f" CR2 +/- {tc * se2 * iqr:.2f}; harbours {GG}")

    print("\n== F. exploratory: H2 with rank and log exposure (reviewer-side; not preregistered) ==")
    for label, col in (("rank(E)/56", lambda e: e.rank() / 56), ("log10(E)", np.log10)):
        dd = d.copy()
        em = dd.drop_duplicates("site_id").set_index("site_id").E_route_5
        dd["E_t"] = dd.site_id.map(col(em))
        xx, XX, nn = setup_h2(dd, ecol="E_t")
        yy, gg = xx.y.to_numpy(float), xx.estuary.to_numpy()
        gii = pd.factorize(gg)[0]; GG = gii.max() + 1
        jj = nn.index("E_2023")
        sc = float(col(em).quantile(0.75) - col(em).quantile(0.25))
        Wd = rng.choice(WEBB, size=(GG, 4999))
        p, b = wild_p_indep(XX, yy, gii, jj, 0.0, Wd)
        gridd = np.round(np.arange(-8.0, 8.01, 0.25), 3) / sc
        (lo, hi), _ = grid_ci(XX, yy, gii, jj, Wd, gridd)
        print(f"{label}: delta per IQR {b * sc:+.3f}; wild p(0) {p:.3f}; wild grid CI [{lo * sc:+.2f}, {hi * sc:+.2f}]")

    print("\n== G. verdicts by interval ==")
    print("H1 rule: Supported if est>=4 & lo>0; Refuted if hi<4. Wild hi 5.67, CR2 hi 5.55 -> Inconclusive under both.")
    print("H2 rule: Supported if lo>0; Refuted if hi<1 (per IQR). Wild hi 3.20 -> Inconclusive; CR2 hi 0.15 -> Refuted.")
    print(f"[{time.time() - t0:.0f} s total]")


if __name__ == "__main__":
    main()
