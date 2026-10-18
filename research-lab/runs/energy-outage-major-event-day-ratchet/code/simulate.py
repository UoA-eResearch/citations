"""Monte Carlo of normalisation policies (plan section 4; H3). Daily severity per simulated system is a mixture fitted to
an included state's 2015-2019 daily SAIDI: P(zero day); a log-normal body for non-zero days up to the state's 95th
percentile of non-zero days (u); a generalised Pareto tail for exceedances above u (5% of non-zero days).
Scenarios (2,000 systems each, 11 years of 365 days): A body x 1.03^t, tail unchanged; B tail probability and excess
scale x 1.05^t, body unchanged; C no trend. Indices for years 6-11 (thresholds need 5 prior years): all events;
MED-excluded under rolling 2.5 beta, frozen (years 1-5) 2.5 beta, and the years-1-5 99th percentile; the oracle sums
body days only. Detection: one-sided p < 0.05 for a positive OLS slope of ln(index + 1) on year over years 6-11.
Writes results/tables/simulation.json."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"
NSYS, YEARS, DAYS, SEED = 2000, 11, 365, 20261018


def fit_state(x):
    nz = x[x > 0]
    p0 = 1 - len(nz) / len(x)
    u = np.quantile(nz, 0.95)
    body = np.log(nz[nz <= u])
    exc = nz[nz > u] - u
    c, loc, scale = stats.genpareto.fit(exc, floc=0)
    return dict(p0=p0, mu=body.mean(), sd=body.std(ddof=1), u=u, xi=min(c, 0.9), scale=scale)


def draw(p, n, rng, body_mult=1.0, tail_mult=1.0):
    """One year of daily severity; returns (values, is_body)."""
    z = rng.random(n) < p["p0"]
    tailp = min(0.05 * tail_mult, 0.5)
    tl = (~z) & (rng.random(n) < tailp)
    bd = (~z) & (~tl)
    v = np.zeros(n)
    # body: log-normal truncated at u (rejection), then scaled
    nb = bd.sum(); b = np.empty(0)
    while len(b) < nb:
        s = np.exp(rng.normal(p["mu"], p["sd"], 2 * nb + 10)); b = np.concatenate([b, s[s <= p["u"]]])
    v[bd] = b[:nb] * body_mult
    v[tl] = p["u"] + stats.genpareto.rvs(p["xi"], scale=p["scale"] * tail_mult, size=tl.sum(), random_state=rng)
    return v, bd


def thr(x):
    l = np.log(x[x > 0]); return np.exp(l.mean() + 2.5 * l.std(ddof=1)) if len(l) > 1 else np.inf


def detect(series):
    y = np.log(np.asarray(series) + 1.0); x = np.arange(len(y), dtype=float)
    r = stats.linregress(x, y)
    return r.slope > 0 and r.pvalue / 2 < 0.05


def first_detect(series):
    for k in range(3, len(series) + 1):
        if detect(series[:k]):
            return k
    return np.nan


def run(params, scen, rng):
    keys = ["all", "roll", "frozen", "q99", "oracle"]
    det = {k: [] for k in keys}; yrs = {k: [] for k in keys}
    for i in range(NSYS):
        p = params[rng.integers(len(params))]
        vals, body = [], []
        for t in range(YEARS):
            bm = 1.03 ** t if scen == "A" else 1.0; tm = 1.05 ** t if scen == "B" else 1.0
            v, b = draw(p, DAYS, rng, bm, tm); vals.append(v); body.append(b)
        base = np.concatenate(vals[:5]); tf = thr(base); q99 = np.quantile(base, 0.99)
        idx = {k: [] for k in keys}
        for t in range(5, YEARS):
            v = vals[t]; tr = thr(np.concatenate(vals[t - 5:t]))
            idx["all"].append(v.sum()); idx["roll"].append(v[v <= tr].sum()); idx["frozen"].append(v[v <= tf].sum())
            idx["q99"].append(v[v <= q99].sum()); idx["oracle"].append(v[body[t]].sum())
        for k in keys:
            det[k].append(detect(idx[k])); yrs[k].append(first_detect(idx[k]))
    return det, yrs


def wilson(k, n, z=1.959964):
    p = k / n; c = (p + z * z / (2 * n)) / (1 + z * z / n); h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [float(c - h), float(c + h)]


def main():
    d = pd.read_csv(RUN / "data" / "daily.csv"); d["year"] = d.date.str[:4].astype(int)
    incl = json.load(open(T / "primary.json"))["included"]
    params = [fit_state(d[(d.st == s) & d.year.between(2015, 2019)].saidi.values) for s in incl]
    rng = np.random.default_rng(SEED)
    out = dict(params={s: p for s, p in zip(incl, params)})
    for scen in ("A", "B", "C"):
        det, yrs = run(params, scen, rng)
        out[scen] = {k: dict(power=float(np.mean(v)), ci=wilson(int(np.sum(v)), len(v)),
                             median_years_to_detect=float(np.nanmedian(yrs[k])) if np.isfinite(yrs[k]).any() else None)
                     for k, v in det.items()}
        if scen == "A":
            a, o = np.array(det["roll"], float), np.array(det["oracle"], float)
            bs = []
            for _ in range(2000):
                ii = rng.integers(0, NSYS, NSYS); bs.append(a[ii].mean() / max(o[ii].mean(), 1e-9))
            ratio = a.mean() / o.mean()
            lo, hi = float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))
            out["H3"] = dict(power_roll=float(a.mean()), power_oracle=float(o.mean()), ratio=float(ratio), ci=[lo, hi],
                             verdict="Supported" if hi < 0.5 else "Refuted" if lo >= 0.5 else "Inconclusive")
        print(scen, {k: round(v["power"], 3) for k, v in out[scen].items()}, flush=True)
    json.dump(out, open(T / "simulation.json", "w"), indent=1, default=float)
    print(json.dumps(out["H3"], indent=1))


if __name__ == "__main__":
    main()
