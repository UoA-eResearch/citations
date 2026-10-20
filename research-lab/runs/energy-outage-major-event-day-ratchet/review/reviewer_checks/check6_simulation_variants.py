"""Reviewer check 6: is scenario B's 'leakage' a property of the rolling rule or of the simulation's body/tail definition?
Re-implements the mixture of code/simulate.py (same structure: P(zero), truncated log-normal body up to u, GPD tail above
u, xi capped at 0.9, 365 i.i.d. days, 11 years, detection = one-sided p<0.05 on ln(index+1) over years 6-11) and runs:
  base    : as preregistered (u = 95th percentile of non-zero 2015-2019 days), to reproduce the published rates and to record,
            per system, the share of tail days (count and SAIDI) that fall below the rolling and frozen thresholds in years
            1-5 vs 6-11, and the mean OLS slope of each index in B;
  tailMED : the tail starts at the state's own frozen 2.5-beta threshold (the actual MED threshold) with the GPD fitted
            to exceedances above it and the body fitted below it, so that 'storm' = 'would be an MED at baseline';
  xi05    : as base but xi capped at 0.5 (finite variance), to see how much the tail cap drives H3 and the leakage;
  freqonly / scaleonly : scenario B with only the tail frequency, or only the tail scale, growing.
NSYS systems per scenario. Writes check6_simulation_variants.json."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

HERE = Path(__file__).resolve().parent
RUN = HERE.parents[1]
T = RUN / "results" / "tables"
NSYS = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
YEARS, DAYS, SEED = 11, 365, 20261018


def thr(x):
    l = np.log(x[x > 0]); return np.exp(l.mean() + 2.5 * l.std(ddof=1)) if len(l) > 1 else np.inf


def fit(x, cut="q95", xicap=0.9):
    nz = x[x > 0]; p0 = 1 - len(nz) / len(x)
    u = np.quantile(nz, 0.95) if cut == "q95" else thr(x)
    body = np.log(nz[nz <= u]); exc = nz[nz > u] - u
    c, _, scale = stats.genpareto.fit(exc, floc=0)
    return dict(p0=p0, mu=body.mean(), sd=body.std(ddof=1), u=u, xi=min(c, xicap), xi_raw=c, scale=scale, ptail=float((nz > u).mean()))


def draw(p, n, rng, bm=1.0, fm=1.0, sm=1.0):
    z = rng.random(n) < p["p0"]
    tl = (~z) & (rng.random(n) < min(p["ptail"] * fm, 0.5)); bd = (~z) & (~tl)
    v = np.zeros(n); nb = bd.sum(); b = np.empty(0)
    while len(b) < nb:
        s = np.exp(rng.normal(p["mu"], p["sd"], 2 * nb + 10)); b = np.concatenate([b, s[s <= p["u"]]])
    v[bd] = b[:nb] * bm
    v[tl] = p["u"] + stats.genpareto.rvs(p["xi"], scale=p["scale"] * sm, size=tl.sum(), random_state=rng)
    return v, bd


def detect(series):
    y = np.log(np.asarray(series) + 1.0); x = np.arange(len(y), dtype=float); r = stats.linregress(x, y)
    return bool(r.slope > 0 and r.pvalue / 2 < 0.05), float(r.slope)


def run(params, scen, rng, nsys=NSYS):
    keys = ["all", "roll", "frozen", "q99", "oracle"]
    det = {k: [] for k in keys}; slope = {k: [] for k in keys}
    diag = dict(tail_days_below_roll_early=[], tail_days_below_roll_late=[], tail_saidi_share_roll_early=[], tail_saidi_share_roll_late=[],
                tail_days_below_frozen_late=[], tail_saidi_share_frozen_late=[], thr_ratio_last_first=[])
    for i in range(nsys):
        p = params[rng.integers(len(params))]
        vals, body = [], []
        for t in range(YEARS):
            bm = 1.03 ** t if scen == "A" else 1.0
            fm = 1.05 ** t if scen in ("B", "freqonly") else 1.0
            sm = 1.05 ** t if scen in ("B", "scaleonly") else 1.0
            v, b = draw(p, DAYS, rng, bm, fm, sm); vals.append(v); body.append(b)
        base = np.concatenate(vals[:5]); tf = thr(base); q99 = np.quantile(base, 0.99)
        idx = {k: [] for k in keys}; trs = []
        tb_r, ts_r, tb_f, ts_f = [], [], [], []
        for t in range(5, YEARS):
            v = vals[t]; tr = thr(np.concatenate(vals[t - 5:t])); trs.append(tr)
            idx["all"].append(v.sum()); idx["roll"].append(v[v <= tr].sum()); idx["frozen"].append(v[v <= tf].sum())
            idx["q99"].append(v[v <= q99].sum()); idx["oracle"].append(v[body[t]].sum())
            tail = ~body[t] & (v > 0)
            tb_r.append(((v <= tr) & tail).sum() / max(tail.sum(), 1)); ts_r.append(v[(v <= tr) & tail].sum() / max(v[v <= tr].sum(), 1e-9))
            tb_f.append(((v <= tf) & tail).sum() / max(tail.sum(), 1)); ts_f.append(v[(v <= tf) & tail].sum() / max(v[v <= tf].sum(), 1e-9))
        for k in keys:
            dd, sl = detect(idx[k]); det[k].append(dd); slope[k].append(sl)
        diag["tail_days_below_roll_early"].append(tb_r[0]); diag["tail_days_below_roll_late"].append(tb_r[-1])
        diag["tail_saidi_share_roll_early"].append(ts_r[0]); diag["tail_saidi_share_roll_late"].append(ts_r[-1])
        diag["tail_days_below_frozen_late"].append(tb_f[-1]); diag["tail_saidi_share_frozen_late"].append(ts_f[-1])
        diag["thr_ratio_last_first"].append(trs[-1] / trs[0])
    res = {k: dict(power=float(np.mean(det[k])), mean_slope_pct=float(100 * (np.exp(np.mean(slope[k])) - 1)),
                   median_slope_pct=float(100 * (np.exp(np.median(slope[k])) - 1))) for k in keys}
    res["diag"] = {k: float(np.mean(v)) for k, v in diag.items()}
    res["det"] = {k: np.array(det[k]) for k in keys}
    return res


def ratio_ci(a, o, rng):
    a, o = np.asarray(a, float), np.asarray(o, float); bs = []
    for _ in range(2000):
        ii = rng.integers(0, len(a), len(a)); bs.append(a[ii].mean() / max(o[ii].mean(), 1e-9))
    return [float(a.mean() / o.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]


d = pd.read_csv(RUN / "data" / "daily.csv"); d["year"] = d.date.str[:4].astype(int)
incl = json.load(open(T / "primary.json"))["included"]
series = {s: d[(d.st == s) & d.year.between(2015, 2019)].saidi.values for s in incl}
out = {}
configs = {"base": dict(cut="q95", xicap=0.9), "tailMED": dict(cut="med", xicap=0.9), "xi05": dict(cut="q95", xicap=0.5)}
for name, cfg in configs.items():
    params = [fit(series[s], **cfg) for s in incl]
    out[name] = dict(params_summary=dict(median_ptail=float(np.median([p["ptail"] for p in params])),
                                         median_u=float(np.median([p["u"] for p in params])),
                                         n_xi_capped=int(sum(p["xi_raw"] > cfg["xicap"] for p in params)),
                                         xi_raw=[round(p["xi_raw"], 3) for p in params],
                                         median_xi_used=float(np.median([p["xi"] for p in params]))))
    rng = np.random.default_rng(SEED)
    scens = ["A", "B", "C"] + (["freqonly", "scaleonly"] if name == "base" else [])
    for scen in scens:
        r = run(params, scen, rng)
        out[name][scen] = {k: v for k, v in r.items() if k != "det"}
        if scen == "A":
            out[name]["H3_ratio_roll_over_oracle"] = ratio_ci(r["det"]["roll"], r["det"]["oracle"], rng)
        print(name, scen, {k: round(r[k]["power"], 3) for k in ["all", "roll", "frozen", "q99", "oracle"]},
              "slopes%", {k: round(r[k]["mean_slope_pct"], 2) for k in ["roll", "frozen", "oracle"]}, r["diag"], flush=True)
json.dump(out, open(HERE / "check6_simulation_variants.json", "w"), indent=1, default=float)
print(json.dumps({k: v.get("H3_ratio_roll_over_oracle") for k, v in out.items()}))
