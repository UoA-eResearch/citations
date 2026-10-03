"""Reproduce Stockman's standard-ETAS target-event temporal log-likelihoods (S0) with the released parameters and the
truncated-history protocol, using an exact numba implementation; then evaluate the same parameters with the full
observed history (S1). Output: results/tables/s0_s1.csv"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit, prange

sys.path.insert(0, str(Path(__file__).resolve().parent))
import data as D  # noqa: E402


@njit(parallel=True, cache=True)
def target_ll(T, M, hist_T, hist_M, tgt_idx, prev_t, mu, k0, a, c, om, M0, fd):
    """For each target (time T[tgt_idx[n]]), log(fd*lam(t)) - fd*int_{prev_t[n]}^{t} lam, with lam from history events
    strictly before t (and Stockman's rule of excluding a history event at exactly t)."""
    out = np.zeros(len(tgt_idx))
    for n in prange(len(tgt_idx)):
        t = T[tgt_idx[n]]
        tj = prev_t[n]
        lam = mu
        integ = mu * (t - tj)
        for q in range(len(hist_T)):
            tq = hist_T[q]
            if tq >= t:
                break
            kk = k0 * np.exp(a * (hist_M[q] - M0))
            lam += kk * (om - 1) * c ** (om - 1) / (t - tq + c) ** om
            Ht = 1 - c ** (om - 1) / (t - tq + c) ** (om - 1)
            Hj = 1 - c ** (om - 1) / (tj - tq + c) ** (om - 1) if tj > tq else 0.0
            integ += kk * (Ht - Hj)
        out[n] = np.log(fd * lam) - fd * integ
    return out


def windows(T, M, time_step):
    """Stockman's target indices (i > time_step, M>=3) and the previous-target time (or T[0])."""
    idx, prev = [], []
    for i in range(1, len(T)):
        js = np.where(M[:i] >= D.M0PRED)[0]
        j = js[-1] if len(js) else 0
        if i > time_step and M[i] >= D.M0PRED:
            idx.append(i); prev.append(T[j])
    return np.array(idx), np.array(prev)


def main():
    rows = []
    for seq in D.SPLIT:
        d = D.split(seq)
        r, p = D.released(seq)
        T, M = d["T_test"], d["M_test"]
        idx, prev = windows(T, M, D.TIME_STEP)
        fd = np.exp(-p["beta"] * (D.M0PRED - d["cutoff"]))
        # S0: history = test array; Stockman's intensity excludes the event at exactly t (ties): emulate via strict <
        s0 = target_ll(T, M, T, M, idx, prev, p["mu"], p["k0"], p["a"], p["c"], p["omega"], p["M0"], fd)
        rel = r.ETAS_pointwise_like.to_numpy()
        s1 = target_ll(T, M, d["T_all"], d["M_all"], idx, prev, p["mu"], p["k0"], p["a"], p["c"], p["omega"], p["M0"], fd)
        n = min(len(rel), len(s0))
        rows.append(dict(seq=seq, n_targets=len(idx), n_released=len(rel), mad_s0_vs_released=float(np.mean(np.abs(s0[:n] - rel[:n]))),
                         max_ad=float(np.max(np.abs(s0[:n] - rel[:n]))), LL_S0_released=rel.mean(), LL_S0_repro=s0.mean(),
                         LL_S1_fullhistory=s1.mean(), LL_NPP_released=r.NN_pointwise_lik.mean()))
        np.save(D.RUN / "results" / "tables" / f"s1_pointwise_{seq}.npy", s1)
    out = pd.DataFrame(rows)
    out.to_csv(D.RUN / "results" / "tables" / "s0_s1.csv", index=False)
    print(out.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
