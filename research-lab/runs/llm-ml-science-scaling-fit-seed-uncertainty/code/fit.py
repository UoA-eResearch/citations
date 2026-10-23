"""Chinchilla fits on single- and n-seed ladders, H1/H2 (plan sections 2-4) -> results/tables/primary.json,
ladders_single.csv, secondary.json.

Fit (Hoffmann et al.; Besiroglu et al.): parameters (a, b, e, alpha, beta) with A = exp(a), B = exp(b), E = exp(e);
log L_hat = LSE(a - alpha log N, b - beta log D, e); minimise sum Huber_delta(log L_hat - log L) by L-BFGS-B from a
fixed grid of starts (64 by default); keep the best.
"""
import itertools
import json
import os
import sys

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):   # one thread per worker process: tiny
    os.environ.setdefault(_v, "1")                                          # arrays, many workers (no oversubscription)
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import logsumexp

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"
SEED, NLAD, BOOT, BOOT_LAD = 20261024, 2000, 200, 500
SIZES = ["14m", "31m", "70m", "160m", "410m"]


def grid(n=64):
    if n == 64:                                             # 4 x 2 x 2 x 2 x 2 = 64 starts
        g = itertools.product([0, 5, 10, 15], [0, 10], [-1, 1], [0.2, 0.6], [0.2, 0.6])
    else:                                                   # 16-point grid (secondary 3)
        g = itertools.product([5], [0, 10], [-1, 1], [0.2, 0.6], [0.2, 0.6])
    return [np.array(x, float) for x in g]


def objective(p, lN, lD, lL, delta, space):
    """Huber loss and its analytic gradient (softmax weights of the log-sum-exp)."""
    a, b, e, al, be = p
    Tm = np.stack([a - al * lN, b - be * lD, np.full_like(lN, e)])
    pred = logsumexp(Tm, axis=0)
    w = np.exp(Tm - pred)
    dpred = np.stack([w[0], w[1], w[2], -w[0] * lN, -w[1] * lD])        # 5 x n
    if space == "log":
        r, dr = pred - lL, dpred
    else:
        ep = np.exp(pred)
        r, dr = ep - np.exp(lL), dpred * ep
    ar = np.abs(r)
    f = np.sum(np.where(ar <= delta, 0.5 * r ** 2, delta * (ar - 0.5 * delta)))
    psi = np.where(ar <= delta, r, delta * np.sign(r))
    return f, dr @ psi


def fit(N, D, L, delta=1e-3, starts=64, space="log"):
    lN, lD, lL = np.log(N), np.log(D), np.log(L)
    best = None
    for x0 in grid(starts):
        r = minimize(objective, x0, args=(lN, lD, lL, delta, space), method="L-BFGS-B", jac=True,
                     bounds=[(-5, 40), (-5, 40), (-3, 3), (0.0, 2.0), (0.0, 2.0)])
        if best is None or r.fun < best.fun:
            best = r
    return best.x


def predict(p, N, D):
    a, b, e, al, be = p
    return float(np.exp(logsumexp([a - al * np.log(N), b - be * np.log(D), e])))


def load():
    d = pd.read_csv(T / "losses.csv")
    lad = d[d["size"].isin(SIZES)].copy()
    tgt = d[~d["size"].isin(SIZES)].set_index("size")
    return lad, tgt


def ladder_points(lad, choice, n):
    """choice: per size, a tuple of n seeds; average their losses per checkpoint."""
    rows = []
    for size, seeds in zip(SIZES, choice):
        g = lad[(lad["size"] == size) & lad.seed.isin(seeds)].groupby("step").agg(N=("N", "first"), D=("D", "first"),
                                                                                   loss=("loss", "mean"))
        rows.append(g)
    g = pd.concat(rows)
    return g.N.to_numpy(float), g.D.to_numpy(float), g.loss.to_numpy(float)


def one(args):
    lad, choice, n, Nt, Dt, kw = args
    N, D, L = ladder_points(lad, choice, n)
    p = fit(N, D, L, **kw)
    return predict(p, Nt, Dt), p


def draws(rng, n, k, seeds_by_size):
    return [tuple(tuple(rng.choice(seeds_by_size[s], n, replace=False)) for s in SIZES) for _ in range(k)]


def width(v):
    return float(np.percentile(v, 95) - np.percentile(v, 5))


def run_draws(lad, n, k, Nt, Dt, rng, seeds_by_size, kw=None, pool=None):
    ch = draws(rng, n, k, seeds_by_size)
    res = list(pool.map(one, [(lad, c, n, Nt, Dt, kw or {}) for c in ch], chunksize=8))
    return np.array([r[0] for r in res]), np.array([r[1] for r in res]), ch


def main():
    lad, tgt = load()
    Nt, Dt = float(tgt.loc["2.8b", "N"]), float(tgt.loc["2.8b", "D"])
    seeds_by_size = {s: sorted(lad[lad["size"] == s].seed.unique()) for s in SIZES}
    rng = np.random.default_rng(SEED)
    out = {"target": {k: {"N": float(tgt.loc[k, "N"]), "loss": float(tgt.loc[k, "loss"])} for k in tgt.index}}
    with ProcessPoolExecutor(20) as pool:
        pred, par = {}, {}
        for n in (1, 2, 3, 5):
            pred[n], par[n], ch = run_draws(lad, n, NLAD, Nt, Dt, rng, seeds_by_size, pool=pool)
            if n == 1:
                pd.DataFrame({"seeds": ["-".join(map(str, sum(c, ()))) for c in ch], "pred_2p8b": pred[1],
                              "alpha": par[1][:, 3], "beta": par[1][:, 4], "E": np.exp(par[1][:, 2])}).to_csv(
                    T / "ladders_single.csv", index=False)
        W = {n: width(pred[n]) for n in pred}
        # bootstrap over seeds within size
        rb = np.random.default_rng(SEED + 1)
        bw1, bw3 = [], []
        for _ in range(BOOT):
            bs = {s: list(rb.choice(seeds_by_size[s], len(seeds_by_size[s]), replace=True)) for s in SIZES}
            # resampled seeds may repeat; map duplicates to distinct pseudo-seeds for n-seed draws
            sub = []
            for s in SIZES:
                for k, sd in enumerate(bs[s]):
                    x = lad[(lad["size"] == s) & (lad.seed == sd)].copy()
                    x["seed"] = 100 + k
                    sub.append(x)
            lb = pd.concat(sub)
            sbs = {s: list(range(100, 100 + len(bs[s]))) for s in SIZES}
            p1, _, _ = run_draws(lb, 1, BOOT_LAD, Nt, Dt, rb, sbs, pool=pool)
            p3, _, _ = run_draws(lb, 3, BOOT_LAD, Nt, Dt, rb, sbs, pool=pool)
            bw1.append(width(p1)); bw3.append(width(p3))
        bw1, bw3 = np.array(bw1), np.array(bw3)
        shrink = 1 - bw3 / bw1
        q = lambda v: [round(float(np.percentile(v, 2.5)), 5), round(float(np.percentile(v, 97.5)), 5)]
        out.update({"W": {str(n): round(w, 5) for n, w in W.items()}, "W1_ci": q(bw1), "W3_ci": q(bw3),
                    "shrinkage_1_3": round(1 - W[3] / W[1], 4), "shrinkage_ci": q(shrink)})
        out["H1"] = "Supported" if out["W1_ci"][0] > 0.05 else "Refuted" if out["W1_ci"][1] < 0.05 else "Inconclusive"
        out["H2"] = "Supported" if out["shrinkage_ci"][0] >= 0.5 else "Refuted" if out["shrinkage_ci"][1] < 0.5 else "Inconclusive"
        # secondary 1-2: accuracy and exponents
        actual = float(tgt.loc["2.8b", "loss"])
        out["accuracy_2p8b"] = {str(n): {"median_error": round(float(np.median(pred[n] - actual)), 5),
                                         "mean_abs_error": round(float(np.mean(np.abs(pred[n] - actual))), 5),
                                         "p5": round(float(np.percentile(pred[n], 5)), 5), "p95": round(float(np.percentile(pred[n], 95)), 5)}
                                for n in pred}
        for k in ("1b", "1.4b"):
            Nk = float(tgt.loc[k, "N"])
            pk = np.array(list(pool.map(predict_from_params, [(p, Nk, Dt) for p in par[1]], chunksize=50)))
            out[f"accuracy_{k}_single"] = {"median_error": round(float(np.median(pk - float(tgt.loc[k, "loss"]))), 5),
                                           "width": round(width(pk), 5)}
        out["exponents_single"] = {"alpha": [round(float(np.percentile(par[1][:, 3], q_)), 4) for q_ in (5, 50, 95)],
                                   "beta": [round(float(np.percentile(par[1][:, 4], q_)), 4) for q_ in (5, 50, 95)]}
        # secondary 3: procedure x seed decomposition (300 single-seed ladders x 5 procedures)
        procs = {"base": {}, "delta1e-4": {"delta": 1e-4}, "delta1e-2": {"delta": 1e-2}, "grid16": {"starts": 16},
                 "linear": {"space": "linear"}}
        ch = draws(np.random.default_rng(SEED + 2), 1, 300, seeds_by_size)
        M = np.array([[r[0] for r in pool.map(one, [(lad, c, 1, Nt, Dt, kw) for c in ch], chunksize=8)] for kw in procs.values()])
        grand = M.mean()
        ss_seed = M.shape[0] * np.sum((M.mean(0) - grand) ** 2)
        ss_proc = M.shape[1] * np.sum((M.mean(1) - grand) ** 2)
        ss_tot = np.sum((M - grand) ** 2)
        out["procedure_vs_seed"] = {"share_seed": round(float(ss_seed / ss_tot), 4), "share_procedure": round(float(ss_proc / ss_tot), 4),
                                    "share_interaction": round(float(1 - (ss_seed + ss_proc) / ss_tot), 4),
                                    "width_by_procedure": {k: round(width(M[i]), 5) for i, k in enumerate(procs)}}
    # secondary 4: final checkpoints only, N-only law
    fin = lad[lad.step == lad.step.max()]
    rngf = np.random.default_rng(SEED + 3)
    pf = []
    for _ in range(NLAD):
        pts = [fin[(fin["size"] == s) & (fin.seed == rngf.choice(seeds_by_size[s]))].iloc[0] for s in SIZES]
        N = np.array([p.N for p in pts], float); L = np.array([p.loss for p in pts], float)
        r = minimize(lambda q: np.sum((np.log(np.exp(q[0]) + np.exp(q[1] - q[2] * np.log(N))) - np.log(L)) ** 2),
                     [0.5, 3.0, 0.3], method="L-BFGS-B", bounds=[(-3, 3), (-5, 40), (0, 2)])
        pf.append(float(np.exp(r.x[0]) + np.exp(r.x[1] - r.x[2] * np.log(Nt))))
    out["final_only_N_law"] = {"W1": round(width(np.array(pf)), 5), "median_error": round(float(np.median(np.array(pf) - actual)), 5)}
    # secondary 5: eval noise vs seed noise
    sd = lad[lad.step == lad.step.max()].groupby("size").loss.std().to_dict()
    out["seed_sd_final_by_size"] = {k: round(float(v), 5) for k, v in sd.items()}
    ev = T / "eval_noise.json"
    if ev.exists():
        out["eval_noise"] = json.loads(ev.read_text())
    (T / "primary.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


def predict_from_params(args):
    p, N, D = args
    return predict(p, N, D)


if __name__ == "__main__":
    main()
