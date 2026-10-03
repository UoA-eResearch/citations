"""Temporal ETAS with detection models (plan.md section 3), fitted by maximum likelihood.

Intensity of the true process above m0, triggered by observed events:
    lam(t) = mu + sum_{k: t_k < t} K exp(alpha (m_k - m0)) (p-1) c^(p-1) (t - t_k + c)^(-p)
Observed-event density at (t, m): lam(t) * beta exp(-beta (m - m0)) * D(m, t)
  S2 (complete):   D = 1
  A  (ETAS-I):     D = exp(-Tb lam(t) exp(-beta (m - m0)))           observed rate (1 - exp(-Tb lam)) / Tb
  B  (mc(t)):      D = Phi((m - mc(t)) / sigma), sigma = 0.2,
                   mc(t) = max(m0, max_{j: m_j >= 4.5, t_j < t} m_j - G - H log10(t - t_j))   (t in hours)

Fast evaluation: the Omori kernel (tau + c)^(-p) is approximated by a non-negative sum of exponentials (SOE) fitted
per parameter set (max relative error checked), so lam(t) at any set of sorted times costs O(N J).
Integrals over time use Gauss-Legendre quadrature in u = log(t - t_k + c) on every inter-event interval.
"""
import math

import numpy as np
from numba import njit
from scipy.optimize import minimize, nnls
from scipy.special import ndtr

SIGMA_B = 0.2
M_LARGE = 4.5
J = 28
GL_X, GL_W = np.polynomial.legendre.leggauss(6)


# ---------------------------------------------------------------- sum-of-exponentials kernel approximation
def soe(c, p, tmax):
    """Weights w >= 0 and rates s with sum_j w_j exp(-s_j tau) ~ (tau + c)^(-p) for tau in [0, tmax]."""
    s = np.logspace(np.log10(0.05 / (tmax + c)), np.log10(20.0 / c), J)
    tau = np.concatenate([[0.0], np.logspace(np.log10(c * 1e-3), np.log10(tmax), 400)])
    g = (tau + c) ** (-p)
    A = np.exp(-np.outer(tau, s)) / g[:, None]
    w, _ = nnls(A, np.ones_like(tau), maxiter=5000)
    approx = (np.exp(-np.outer(tau, s)) @ w)
    return w, s, float(np.max(np.abs(approx / g - 1)))


# ---------------------------------------------------------------- core sweeps (numba)
@njit(cache=True)
def _lam_events(T, prod, w, s, mu, amp):
    """lam(t_i^-) at every event time (history strictly before t_i; ties excluded) and the SOE state after each event."""
    n, nj = len(T), len(s)
    lam = np.empty(n)
    S = np.zeros(nj)
    states = np.empty((n, nj))
    tprev = T[0]
    for i in range(n):
        dt = T[i] - tprev
        tot = 0.0
        for j in range(nj):
            S[j] *= math.exp(-s[j] * dt)
            tot += w[j] * S[j]
        lam[i] = mu + amp * tot
        for j in range(nj):
            S[j] += prod[i]
            states[i, j] = S[j]
        tprev = T[i]
    return lam, states


@njit(cache=True)
def _mc_at(t, T, M, big_idx, m0, G, H):
    mc = m0
    for q in range(len(big_idx)):
        k = big_idx[q]
        if T[k] >= t:
            break
        d = t - T[k]
        if d > 0:
            v = M[k] - G - H * math.log10(d)
            if v > mc:
                mc = v
    return mc


@njit(cache=True)
def _obs_frac_B(mc, m0, beta, msel):
    """int_{msel}^inf beta e^{-beta(m-m0)} Phi((m-mc)/sigma) dm  (msel >= m0)."""
    sg = 0.2
    z = (msel - mc) / sg
    a = 0.5 * math.erfc(-z / math.sqrt(2.0))                      # Phi(z)
    b = 0.5 * math.erfc(-(z + beta * sg) / math.sqrt(2.0))        # Phi(z + beta sigma)
    return math.exp(-beta * (msel - m0)) * (a + math.exp(-beta * (mc - msel) + 0.5 * beta * beta * sg * sg) * (1.0 - b)) \
        if True else 0.0


@njit(cache=True)
def _integral(T, states, w, s, mu, amp, c, t_start, t_end, model, Tb, beta, m0, msel, M, big_idx, G, H, glx, glw):
    """int_{t_start}^{t_end} of the observed rate of events with m >= msel.
    model 0: lam e^{-beta(msel-m0)};  1 (A): (1 - exp(-Tb lam e^{-beta(msel-m0)}))/Tb;  2 (B): lam * obs_frac_B."""
    n, nj = len(T), len(s)
    sel = math.exp(-beta * (msel - m0))
    total = 0.0
    # interval before the first event inside [t_start, t_end]: lam = state of last event before t_start
    for i in range(n):
        a_ = T[i]
        b_ = T[i + 1] if i + 1 < n else t_end
        lo = max(a_, t_start)
        hi = min(b_, t_end)
        if hi <= lo:
            if a_ >= t_end:
                break
            continue
        # quadrature in u = log(t - a_ + c)
        u0 = math.log(lo - a_ + c)
        u1 = math.log(hi - a_ + c)
        half = 0.5 * (u1 - u0)
        mid = 0.5 * (u1 + u0)
        acc = 0.0
        for q in range(len(glx)):
            u = mid + half * glx[q]
            tt = math.exp(u) - c + a_
            dtt = tt - a_
            tot = 0.0
            for j in range(nj):
                tot += w[j] * states[i, j] * math.exp(-s[j] * dtt)
            lam = mu + amp * tot
            if model == 0:
                r = lam * sel
            elif model == 1:
                x = Tb * lam * sel
                r = -math.expm1(-x) / Tb if x > 1e-12 else lam * sel
            else:
                mc = _mc_at(tt, T, M, big_idx, m0, G, H)
                r = lam * _obs_frac_B(mc, m0, beta, msel)
            acc += glw[q] * r * (dtt + c)            # dt = (t - a + c) du
        total += half * acc
    return total


# ---------------------------------------------------------------- parameter handling
NAMES = {"S2": ["mu", "K", "alpha", "c", "p"], "A": ["mu", "K", "alpha", "c", "p", "Tb", "beta"],
         "B": ["mu", "K", "alpha", "c", "p", "G", "H", "beta"]}


def unpack(x, model):
    d = dict(mu=math.exp(x[0]), K=math.exp(x[1]), alpha=math.exp(x[2]), c=math.exp(x[3]), p=1 + math.exp(x[4]))
    if model == "A":
        d.update(Tb=math.exp(x[5]), beta=math.exp(x[6]))
    if model == "B":
        d.update(G=x[5], H=math.exp(x[6]), beta=math.exp(x[7]))
    return d


def pack(d, model):
    x = [math.log(d["mu"]), math.log(d["K"]), math.log(d["alpha"]), math.log(d["c"]), math.log(d["p"] - 1)]
    if model == "A":
        x += [math.log(d["Tb"]), math.log(d["beta"])]
    if model == "B":
        x += [d["G"], math.log(d["H"]), math.log(d["beta"])]
    return np.array(x)


def big_index(M):
    return np.where(M >= M_LARGE)[0].astype(np.int64)


def train_ll(d, model, T, M, m0, beta=None):
    """Log-likelihood of observed events (index >= 1) in [T0, T_end] with full magnitude density."""
    tmax = T[-1] - T[0] + 1.0
    w, s, err = soe(d["c"], d["p"], tmax)
    amp = (d["p"] - 1) * d["c"] ** (d["p"] - 1)
    prod = d["K"] * np.exp(d["alpha"] * (M - m0))
    lam, states = _lam_events(T, prod, w, s, d["mu"], amp)
    b = d.get("beta", beta)
    lam_i = lam[1:]
    mi = M[1:]
    ll = np.sum(np.log(lam_i)) + np.sum(np.log(b) - b * (mi - m0))
    bi = big_index(M)
    if model == "S2":
        # exact integral
        integ = d["mu"] * (T[-1] - T[0]) + np.sum(prod * (1 - d["c"] ** (d["p"] - 1) / (T[-1] - T + d["c"]) ** (d["p"] - 1)))
    elif model == "A":
        ll += np.sum(-d["Tb"] * lam_i * np.exp(-b * (mi - m0)))
        integ = _integral(T, states, w, s, d["mu"], amp, d["c"], T[0], T[-1], 1, d["Tb"], b, m0, m0, M, bi, 0.0, 0.0, GL_X, GL_W)
    else:
        mcs = np.array([_mc_at(t, T, M, bi, m0, d["G"], d["H"]) for t in T[1:]])
        ll += np.sum(np.log(np.clip(ndtr((mi - mcs) / SIGMA_B), 1e-300, None)))
        integ = _integral(T, states, w, s, d["mu"], amp, d["c"], T[0], T[-1], 2, 0.0, b, m0, m0, M, bi, d["G"], d["H"], GL_X, GL_W)
    return ll - integ, err


def fit(model, T, M, m0, starts, maxiter=400):
    beta_hat = 1.0 / np.mean(M - m0)
    mu_max = 10.0 * len(T) / (T[-1] - T[0])   # background cannot exceed 10x the mean observed rate
    best = None
    for st in starts:
        x0 = pack(st, model)

        def nll(x):
            try:
                d = unpack(x, model)
                if (d["c"] > 50 or d["p"] > 4 or d["p"] < 1.0001 or d["alpha"] > 5 or d["K"] > 1e5 or d["mu"] > mu_max
                        or d.get("Tb", 0) > 1.0 or d.get("beta", 1) > 10):
                    return 1e12
                v, _ = train_ll(d, model, T, M, m0, beta=beta_hat)
                return -v if np.isfinite(v) else 1e12
            except (FloatingPointError, ValueError, OverflowError, ZeroDivisionError):
                return 1e12
        r = minimize(nll, x0, method="Nelder-Mead", options=dict(maxiter=maxiter * len(x0), xatol=1e-4, fatol=1e-3, adaptive=True))
        r2 = minimize(nll, r.x, method="L-BFGS-B", options=dict(maxiter=200))
        rr = r2 if r2.fun <= r.fun else r
        if best is None or rr.fun < best.fun:
            best = rr
    d = unpack(best.x, model)
    if model == "S2":
        d["beta"] = beta_hat
    ll, err = train_ll(d, model, T, M, m0, beta=beta_hat)
    d.update(train_ll=ll, train_ll_per_event=ll / (len(T) - 1), soe_max_rel_err=err, n_train=len(T))
    return d


# ---------------------------------------------------------------- test-period target-event log-likelihood
@njit(cache=True)
def _lam_exact(t, T, M, mu, K, alpha, c, p, m0):
    lam = mu
    amp = (p - 1) * c ** (p - 1)
    for q in range(len(T)):
        if T[q] >= t:
            break
        lam += K * math.exp(alpha * (M[q] - m0)) * amp / (t - T[q] + c) ** p
    return lam


def target_ll(d, model, T_all, M_all, tgt_times, prev_times, m0, msel=3.0):
    """Per-target log(lam_sel(t_i)) - int_{t_prev}^{t_i} lam_sel, full observed history, model-specific observed rate
    of events with m >= msel. lam at target times is exact; integrals use the SOE sweep (S2 also has an exact form)."""
    b = d["beta"]
    sel = math.exp(-b * (msel - m0))
    tmax = T_all[-1] - T_all[0] + 1.0
    w, s, err = soe(d["c"], d["p"], tmax)
    amp = (d["p"] - 1) * d["c"] ** (d["p"] - 1)
    prod = d["K"] * np.exp(d["alpha"] * (M_all - m0))
    _, states = _lam_events(T_all, prod, w, s, d["mu"], amp)
    bi = big_index(M_all)
    out = np.empty(len(tgt_times))
    for n, (t, tp) in enumerate(zip(tgt_times, prev_times)):
        lam = _lam_exact(t, T_all, M_all, d["mu"], d["K"], d["alpha"], d["c"], d["p"], m0)
        if model == "S2":
            r = lam * sel
            mdl, Tb, G, H = 0, 0.0, 0.0, 0.0
        elif model == "A":
            x = d["Tb"] * lam * sel
            r = -math.expm1(-x) / d["Tb"] if x > 1e-12 else lam * sel
            mdl, Tb, G, H = 1, d["Tb"], 0.0, 0.0
        else:
            mc = _mc_at(t, T_all, M_all, bi, m0, d["G"], d["H"])
            r = lam * _obs_frac_B(mc, m0, b, msel)
            mdl, Tb, G, H = 2, 0.0, d["G"], d["H"]
        integ = _integral(T_all, states, w, s, d["mu"], amp, d["c"], tp, t, mdl, Tb, b, m0, msel, M_all, bi, G, H, GL_X, GL_W)
        out[n] = math.log(max(r, 1e-300)) - integ
    return out, err


# ---------------------------------------------------------------- simulation (validation): only observed events trigger
@njit(cache=True)
def simulate(mu, K, alpha, c, p, beta, m0, Tend, model, Tb, G, H, seed, mains_t, mains_m):
    """Ogata thinning. Candidate events from lam(t); each candidate gets a GR magnitude and is kept with probability
    D(m, t) (model 1: A, 2: B, 0: none). Only kept events trigger. Optional imposed mainshocks (always observed)."""
    np.random.seed(seed)
    Ts = np.empty(2000000)
    Ms = np.empty(2000000)
    n = 0
    t = 0.0
    amp = (p - 1) * c ** (p - 1)
    nm = 0
    while t < Tend and n < 1999990:
        # intensity upper bound at t+ (lam decreasing between events)
        lam_up = mu
        for q in range(n):
            lam_up += K * math.exp(alpha * (Ms[q] - m0)) * amp / (t - Ts[q] + c) ** p
        t_next_main = mains_t[nm] if nm < len(mains_t) else 1e18
        dt = np.random.exponential(1.0 / lam_up)
        if t + dt >= t_next_main:
            t = t_next_main
            Ts[n] = t; Ms[n] = mains_m[nm]; n += 1; nm += 1
            continue
        t += dt
        if t >= Tend:
            break
        lam = mu
        for q in range(n):
            lam += K * math.exp(alpha * (Ms[q] - m0)) * amp / (t - Ts[q] + c) ** p
        if np.random.random() * lam_up > lam:
            continue
        m = m0 + np.random.exponential(1.0 / beta)
        keep = True
        if model == 1:
            keep = np.random.random() < math.exp(-Tb * lam * math.exp(-beta * (m - m0)))
        elif model == 2:
            mc = m0
            for q in range(n):
                if Ms[q] >= 4.5 and Ts[q] < t:
                    v = Ms[q] - G - H * math.log10(t - Ts[q])
                    if v > mc:
                        mc = v
            z = (m - mc) / 0.2
            keep = np.random.random() < 0.5 * math.erfc(-z / math.sqrt(2.0))
        if keep:
            Ts[n] = t; Ms[n] = m; n += 1
    return Ts[:n], Ms[:n]


def standard_errors(d, model, T, M, m0, h=1e-3):
    """Delta-method SEs from a finite-difference Hessian of the log-likelihood in the transformed (log) space."""
    beta_hat = d.get("beta")
    x0 = pack(d, model)
    k = len(x0)

    def f(x):
        return train_ll(unpack(x, model), model, T, M, m0, beta=beta_hat)[0]
    Hm = np.zeros((k, k))
    f0 = f(x0)
    for i in range(k):
        for j in range(i, k):
            ei, ej = np.eye(k)[i] * h, np.eye(k)[j] * h
            v = (f(x0 + ei + ej) - f(x0 + ei - ej) - f(x0 - ei + ej) + f(x0 - ei - ej)) / (4 * h * h)
            Hm[i, j] = Hm[j, i] = v
    cov = np.linalg.pinv(-Hm)
    se_x = np.sqrt(np.clip(np.diag(cov), 0, None))
    out = {}
    for i, name in enumerate(NAMES[model]):
        val = d[name]
        if name == "G":
            out[name] = se_x[i]
        elif name == "p":
            out[name] = (val - 1) * se_x[i]
        else:
            out[name] = val * se_x[i]
    return out
