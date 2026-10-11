"""Power and MDE for the preregistered rule (plan section 7). Simulates item-clustered binomial outcomes and applies the
exact decision rule: pooled rate ratio originals/twins with 0.5 added to each numerator, item-cluster percentile
bootstrap. Scenario: twin (analog-defect) rate r_i ~ Beta(mean r, concentration 2) per item and model; on originals, a
fraction f of items is memorised and copies the defect at rate c = 0.5, the rest at r_i. No outcome data are used."""
import sys
import numpy as np

rng = np.random.default_rng(20261012)
M, N, B = 3, 16, 400


def beta(mean, k, size):
    return rng.beta(mean * k, (1 - mean) * k, size)


def rr(xo, xt, no, nt):
    return ((xo + 0.5) / no) / ((xt + 0.5) / nt)


def sim(I, r, f, c=0.5, sims=300):
    sup = ref = 0
    for _ in range(sims):
        rt = beta(r, 2, (I, M))
        ro = rt.copy()
        mem = rng.random(I) < f
        ro[mem] = c
        xo = rng.binomial(N, ro).sum(1)
        xt = rng.binomial(N, rt).sum(1)
        no = nt = I * M * N
        est = rr(xo.sum(), xt.sum(), no, nt)
        idx = rng.integers(0, I, (B, I))
        bs = rr(xo[idx].sum(1), xt[idx].sum(1), no, nt)
        lo, hi = np.percentile(bs, [2.5, 97.5])
        sup += (est >= 3) and (lo > 1.5)
        ref += hi < 3
    return sup / sims, ref / sims


if __name__ == "__main__":
    print("I r f trueRR P(Supported) P(Refuted)")
    for I in (60, 100, 150):
        for r in (0.03, 0.05, 0.10):
            for f in (0.0, 0.05, 0.10, 0.20, 0.30):
                true = (f * 0.5 + (1 - f) * r) / r
                s, rf = sim(I, r, f)
                print(I, r, f, round(true, 2), round(s, 2), round(rf, 2), flush=True)
