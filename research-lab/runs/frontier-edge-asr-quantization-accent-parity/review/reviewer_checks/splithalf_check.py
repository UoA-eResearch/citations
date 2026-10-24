"""Confirmation pass: reconcile the split-half selection-bias estimates.

review.md (recompute.py): 20 within-speaker balanced splits, both directions, reports in-sample minus out-of-sample.
robustness.py (D4): 20 Bernoulli(0.5) splits, one direction, reports out-of-sample minus in-sample.
Here both schemes are run with many replicates on the per-utterance table, both directions, point estimates only,
reporting in-sample minus out-of-sample with its standard error.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
df = pd.read_csv(HERE / "utt_errors_small.csv", keep_default_na=False)
conds = sorted(df.cond.unique())
base = df[df.cond == "fp16"].sort_values(["shard", "row"]).reset_index(drop=True)
U = len(base)
spk = sorted(base.speaker.unique())
S = len(spk)
spk_i = {s: i for i, s in enumerate(spk)}
u_spk = base.speaker.map(spk_i).to_numpy()
sgroup = base.groupby("speaker").group.first().reindex(spk)
named = sorted(g for g in sgroup.unique() if g != "other")
G = np.stack([(sgroup == g).to_numpy(float) for g in named], axis=1)
nref = base.nref.to_numpy(float)
targets = {"rtn_w4": ["rtn_w4"], "gptq_w4_us": [f"gptq_w4_us_s{s}" for s in range(3)], "gptq_w3_us": [f"gptq_w3_us_s{s}" for s in range(3)],
           "gptq_w3_balanced": [f"gptq_w3_balanced_s{s}" for s in range(3)], "gptq_w3_worst": [f"gptq_w3_worst_s{s}" for s in range(3)]}
need = ["fp16"] + [c for cs in targets.values() for c in cs]
ERR = {c: df[df.cond == c].sort_values(["shard", "row"]).err.to_numpy(float) for c in need}


def sums(x, mask):
    return np.bincount(u_spk[mask], x[mask], minlength=S)


def select(mask):
    w = (sums(ERR["fp16"], mask) @ G) / (sums(nref, mask) @ G)
    o = np.argsort(w)
    return o[:3], o[-3:]


def penalties(mask, groups):
    best3, worst3 = groups
    N = sums(nref, mask) @ G
    def gap(c):
        E = sums(ERR[c], mask) @ G
        return E[worst3].sum() / N[worst3].sum() - E[best3].sum() / N[best3].sum()
    g0 = gap("fp16")
    return {k: np.mean([gap(c) - g0 for c in cs]) for k, cs in targets.items()}


def run(scheme, reps, seed, both_directions=True):
    rng = np.random.default_rng(seed)
    rec = {k: [] for k in targets}
    for _ in range(reps):
        if scheme == "within_speaker":
            half = np.zeros(U, bool)
            for s in range(S):
                ids = np.where(u_spk == s)[0]
                rng.shuffle(ids)
                half[ids[: len(ids) // 2]] = True
        else:
            half = rng.random(U) < 0.5
        for sel, ev in ([(half, ~half), (~half, half)] if both_directions else [(half, ~half)]):
            out = penalties(ev, select(sel))      # groups chosen on the other half
            inn = penalties(ev, select(ev))       # groups chosen on the evaluation half itself
            for k in targets:
                rec[k].append(inn[k] - out[k])
    return {k: {"in_minus_out_mean_pp": round(100 * float(np.mean(v)), 2), "se_pp": round(100 * float(np.std(v, ddof=1) / np.sqrt(len(v))), 2),
                "sd_pp": round(100 * float(np.std(v, ddof=1)), 2), "n": len(v)} for k, v in rec.items()}


res = {"within_speaker_both_dirs_300": run("within_speaker", 300, 11),
       "bernoulli_both_dirs_300": run("bernoulli", 300, 12),
       "bernoulli_one_dir_20_like_D4": run("bernoulli", 20, 20261024, both_directions=False),
       "within_speaker_both_dirs_20_like_review": run("within_speaker", 20, 7)}
for name, r in res.items():
    print(f"=== {name} ===")
    for k, v in r.items():
        print(f"  {k:18s} in-out {v['in_minus_out_mean_pp']:+5.2f} pp  se {v['se_pp']:.2f}  sd {v['sd_pp']:.2f}  n={v['n']}")
(HERE / "splithalf_check.json").write_text(json.dumps(res, indent=1))
