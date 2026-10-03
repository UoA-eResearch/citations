"""Fit S2, A and B on a configuration's training period and evaluate test-period target-event temporal log-likelihoods
with the full observed history (plan.md sections 3-4). Configurations: AVN Visso/Norcia/Campotosto (hours) and
Stockman's synthetic incomplete catalog (days).
Usage: run_config.py <Visso|Norcia|Campotosto|synthetic> [cutoff]
Outputs: results/fits/<config>_<cutoff>.json, results/pointwise/<config>_<cutoff>.parquet
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import data as D  # noqa: E402
import etas_lib as E  # noqa: E402
from s0_check import windows  # noqa: E402

RUN = D.RUN


def load(cfg, cutoff):
    if cfg == "synthetic":
        c = pd.read_csv(D.NPP / "Catalogs" / "synthetic_incomplete_catalog.csv")
        c["time"] = pd.to_datetime(c["time"])
        c = c.sort_values("time")
        T = ((c.time - c.time.iloc[0]) / pd.Timedelta(days=1)).to_numpy(float)
        M = c.magnitude.to_numpy(float)
        keep = M >= cutoff
        T, M = T[keep], M[keep]
        up = 4000.0
        tr = T < up
        T_te = np.append(T[tr][-D.TIME_STEP + 1:], T[~tr])
        M_te = np.append(M[tr][-D.TIME_STEP + 1:], M[~tr])
        r = pd.read_csv(D.NPP / "Results" / f"incomplete_simulated_resultsMcut-{cutoff}_M0pred:3.0.csv")
        p = pd.read_csv(D.NPP / "ETAS_parameters" / f"simulated_paramsMcut-{cutoff}_incomplete.csv", header=None, index_col=0)[1]
        params = {k: float(v) for k, v in p.items() if k != "train_time"}
        return dict(T_all=T, M_all=M, T_train=T[tr], M_train=M[tr], T_test=T_te, M_test=M_te, cutoff=cutoff,
                    block=1.0, unit="days"), r, params
    d = D.split(cfg, cutoff)
    r, params = D.released(cfg, cutoff)
    d.update(block=24.0, unit="hours")
    return d, r, params


def starts(params, unit, n, span, extra=()):
    """D2: released parameters clipped into the bounds, a spread of generic starts (c 1e-4..1 h, alpha 1.5..3.3,
    Tb 0.003..0.03 h, p 1.1..1.5), and the optima of earlier fits (`extra`, e.g. the other sequences' A fits)."""
    hours = unit == "hours"
    tf = 1.0 if hours else 1 / 24.0                     # time-unit factor
    rate = n / span
    base = dict(mu=min(params["mu"], 5 * rate), K=float(np.clip(params["k0"], 0.01, 1.0)), alpha=float(np.clip(params["a"], 0.3, 2.5)),
                c=float(np.clip(params["c"], 1e-3, 5.0)), p=float(np.clip(params["omega"], 1.05, 2.5)),
                Tb=0.005 * tf, G=3.5 if hours else 4.5, H=0.75, beta=2.3)
    out = [base]
    grid = [(1e-4, 3.3, 0.006, 1.1, 0.05), (1e-4, 2.5, 0.02, 1.2, 0.1), (0.01, 3.0, 0.003, 1.15, 0.05), (0.01, 1.5, 0.01, 1.3, 0.3),
            (0.3, 2.5, 0.006, 1.3, 0.1), (1.0, 2.0, 0.03, 1.5, 0.3), (1e-3, 3.3, 0.01, 1.1, 0.03), (0.1, 3.0, 0.02, 1.2, 0.08)]
    for c, a, tb, p, k in grid:
        out.append(dict(mu=0.3 * rate, K=k, alpha=a, c=c * tf, p=p, Tb=tb * tf, G=base["G"], H=0.75, beta=3.0 if a > 2 else 2.4))
    for e in extra:
        out.append({k: e[k] for k in ("mu", "K", "alpha", "c", "p", "Tb", "G", "H", "beta") if k in e} | {k: v for k, v in base.items() if k not in e})
    return out


def main(cfg, cutoff=None):
    cutoff = float(cutoff) if cutoff else (2.0 if cfg == "synthetic" else D.CUTOFF[cfg])
    d, r, params = load(cfg, cutoff)
    m0 = cutoff
    T, M = d["T_test"], d["M_test"]
    idx, prev = windows(T, M, D.TIME_STEP)
    tgt_t = T[idx]
    assert len(idx) == len(r), (len(idx), len(r))
    out = dict(config=cfg, cutoff=cutoff, n_train=len(d["T_train"]), n_targets=len(idx), unit=d["unit"])
    pw = pd.DataFrame({"t": tgt_t, "S0": r.ETAS_pointwise_like.to_numpy(), "NPP": r.NN_pointwise_lik.to_numpy()})
    extra = []
    if d["unit"] == "hours":   # optima of the first-round primary A fits of all three sequences (results/fits_round1)
        for f in sorted((RUN / "results" / "fits_round1").glob("*_1.[23].json")):
            j = json.load(open(f))
            for mdl in ("A", "B"):
                extra.append(j[mdl])
    st = starts(params, d["unit"], len(d["T_train"]), d["T_train"][-1] - d["T_train"][0], extra)
    for model in ("S2", "A", "B"):
        t0 = time.time()
        f = E.fit(model, d["T_train"], d["M_train"], m0, st)
        ll, err = E.target_ll(f, model, d["T_all"], d["M_all"], tgt_t, prev, m0)
        pw[model] = ll
        out[model] = {k: (float(v) if np.isscalar(v) else [float(x) for x in v]) for k, v in f.items()} | dict(test_ll=float(ll.mean()), seconds=round(time.time() - t0, 1),
                                                              test_soe_err=float(err))
        print(cfg, model, {k: round(float(v), 4) for k, v in f.items() if k in E.NAMES[model] + ["train_ll_per_event"]},
              "test", round(float(ll.mean()), 4), f"{time.time() - t0:.0f}s", flush=True)
    (RUN / "results" / "fits").mkdir(parents=True, exist_ok=True)
    (RUN / "results" / "pointwise").mkdir(parents=True, exist_ok=True)
    tag = f"{cfg}_{cutoff}"
    json.dump(out, open(RUN / "results" / "fits" / f"{tag}.json", "w"), indent=1)
    pw["block"] = np.floor(pw.t / d["block"]).astype(int)
    pw.to_parquet(RUN / "results" / "pointwise" / f"{tag}.parquet")


if __name__ == "__main__":
    main(*sys.argv[1:])
