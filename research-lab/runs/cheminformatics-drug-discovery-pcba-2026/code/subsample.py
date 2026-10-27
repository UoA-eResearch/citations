"""D3: cap inactives per target so the panel is computable, and check that the cap does not move EF1%.

Both benchmarks have targets of 100k-500k compounds (LIT's median is 246k), which 5 methods x 5 folds cannot fit on
a shared CPU box. All actives are kept; inactives are subsampled uniformly to CAP per target (seed 20261027). EF1%
is a ranking ratio, and for hit rates at or below 1% its ceiling stays 100, so the cap should not move it.

  subsample.py build  -> data/new_sub.parquet, data/lit_sub.parquet, data/smiles_unique.parquet
  subsample.py check  -> results/tables/subsample_check.json (NN EF1% on the full set vs the cap, 3 large targets)
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
SEED, CAP, MIN_ACT = 20261027, 50000, 150


def cap_target(g, rng):
    """At most CAP compounds, preserving the hit rate (so EF1%'s ceiling, min(100, 1/rate), is unchanged).

    Proportional subsampling of both classes keeps the rate exactly. When that would leave fewer than MIN_ACT
    actives, all actives are kept and the inactives capped instead; the rate then rises, but only for targets whose
    rate stays below 1%, where the ceiling is 100 either way.
    """
    act, ina = g[g.label == 1], g[g.label == 0]
    if len(g) <= CAP:
        return g
    frac = CAP / len(g)
    if len(act) * frac >= MIN_ACT:
        keep_a = int(round(len(act) * frac)); keep_i = CAP - keep_a
    else:
        keep_a, keep_i = len(act), min(len(ina), CAP)
    a2 = act.iloc[np.sort(rng.choice(len(act), min(keep_a, len(act)), replace=False))]
    i2 = ina.iloc[np.sort(rng.choice(len(ina), min(keep_i, len(ina)), replace=False))]
    return pd.concat([a2, i2])


def build():
    rows = []
    rng = np.random.default_rng(SEED)
    new = pd.read_parquet(D / "new.parquet")
    out = pd.concat([cap_target(g, rng) for _, g in new.groupby("target", sort=True)], ignore_index=True)
    out.to_parquet(D / "new_sub.parquet")
    rows.append(("new", len(new), len(out), new.target.nunique()))
    lit = pd.read_parquet(D / "lit.parquet")
    keep = []
    for (t, sp), g in lit.groupby(["target", "split"], sort=True):   # cap each split separately, so the published
        keep.append(cap_target(g.drop_duplicates("smiles"), rng))    # training/validation sets stay disjoint sets
    out2 = pd.concat(keep, ignore_index=True)
    out2.to_parquet(D / "lit_sub.parquet")
    rows.append(("lit", len(lit), len(out2), lit.target.nunique()))
    uniq = pd.DataFrame({"smiles": pd.unique(pd.concat([out.smiles, out2.smiles]))})
    uniq.to_parquet(D / "smiles_unique.parquet")
    print(pd.DataFrame(rows, columns=["benchmark", "rows_before", "rows_after", "targets"]).to_string(index=False))
    print("unique SMILES to embed:", len(uniq))


def ef(y, s, frac=0.01):
    k = max(1, int(round(frac * len(y))))
    order = np.argsort(-s, kind="stable")
    r = y.mean()
    return float((y[order[:k]].sum() / k) / r) if r > 0 else np.nan


def check():
    """NN (max Tanimoto to training actives) on a random 80/20 split, full set vs cap, for three large targets."""
    sys.path.insert(0, str(RUN / "code"))
    from folds import fingerprints
    new = pd.read_parquet(D / "new.parquet")
    big = new.groupby("target").size().sort_values(ascending=False).head(3).index
    out = []
    for t in big:
        g = new[new.target == t].reset_index(drop=True)
        rng = np.random.default_rng(SEED)
        X = fingerprints(g.smiles.tolist()).astype(np.float32)
        y = g.label.to_numpy()
        te = rng.random(len(g)) < 0.2
        act_tr = np.flatnonzero((~te) & (y == 1))
        cnt = X.sum(1)

        def nn_ef(mask):
            idx = np.flatnonzero(te & mask)
            best = np.full(len(idx), -1.0)
            for s in range(0, len(idx), 4096):
                b = idx[s:s + 4096]
                inter = X[b] @ X[act_tr].T
                best[s:s + len(b)] = (inter / (cnt[b][:, None] + cnt[act_tr][None, :] - inter + 1e-9)).max(1)
            return ef(y[idx], best), len(idx), float(y[idx].mean())
        full = nn_ef(np.ones(len(g), bool))
        sub = cap_target(g.assign(_i=np.arange(len(g))), np.random.default_rng(SEED))
        keep = np.zeros(len(g), bool); keep[sub._i.to_numpy()] = True
        cap = nn_ef(keep)
        out.append({"target": t, "compounds": int(len(g)), "ef1_full": round(full[0], 2), "n_eval_full": full[1],
                    "hit_rate_full": round(full[2], 5), "ef1_capped": round(cap[0], 2), "n_eval_capped": cap[1],
                    "hit_rate_capped": round(cap[2], 5)})
        print(out[-1], flush=True)
    (T / "subsample_check.json").write_text(json.dumps({"cap": CAP, "seed": SEED, "targets": out}, indent=1))


if __name__ == "__main__":
    {"build": build, "check": check}[sys.argv[1]]()
