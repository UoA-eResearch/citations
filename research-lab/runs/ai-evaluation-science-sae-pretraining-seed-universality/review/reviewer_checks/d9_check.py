"""Reviewer check of D9 (code/token_identity.py): (1) recompute the token-identity / other match rates and the
non-token-source primary statistic from results/tables/token_purity_L*.npz and the released arrays with my own code
(matrix-form bootstrap as in recompute_stats.py); (2) per-layer non-token ratios with intervals; (3) a second purity
cut (0.8) and the token group's own cross/within ratio; (4) recompute purity from scratch for one SAE (p160m, layer 4,
seed 0) with sparsify's encoder and hidden_states, and compare with the stored purity array.
Usage: venv/bin/python review/reviewer_checks/d9_check.py"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch

RUN = Path(__file__).resolve().parents[2]
TAB = RUN / "results" / "tables"
OUT = Path(__file__).resolve().parent
FULL = ["p160m"] + [f"p160m-seed{i}" for i in range(1, 10)]
LAYERS = [4, 8]
res = {}

pur = {L: np.load(TAB / f"token_purity_L{L}.npz") for L in LAYERS}
arr = {L: np.load(RUN / "results" / f"match_arrays_L{L}.npz") for L in LAYERS}
pairs = {L: pd.read_csv(TAB / f"pairs_L{L}.csv") for L in LAYERS}


def group_rates_and_scores(L, cut):
    d = pairs[L]
    d = d[d.kind.isin(["within", "full"]) & d.a.isin(FULL) & d.b.isin(FULL)]
    agg = {}
    w_scores, x_scores = {}, {}
    for _, p in d.iterrows():
        sc = {}
        for side, m, s in (("a", p.a, p.sa), ("b", p.b, p.sb)):
            best = arr[L][f"pair{p.id}_{side}"].astype(np.float32)
            ok = np.isfinite(best)
            pu = pur[L][f"{m}_s{s}"]
            tid = pu >= cut
            for grp, sel in (("token", ok & tid), ("other", ok & ~tid)):
                a = agg.setdefault((p.kind, grp), [0, 0])
                a[0] += int(sel.sum())
                a[1] += int((best[sel] >= 0.7).sum())
            sc[side] = float((best[ok & ~tid] >= 0.7).mean())
        f = (sc["a"] + sc["b"]) / 2
        if p.kind == "within":
            w_scores.setdefault(p.a, []).append(f)
        else:
            x_scores.setdefault(frozenset((p.a, p.b)), []).append(f)
    rates = {f"{k}|{g}": dict(n=v[0], matched=v[1], rate=v[1] / v[0]) for (k, g), v in agg.items()}
    w = np.array([np.mean(w_scores[m]) for m in FULL])
    X = np.full((10, 10), np.nan)
    for k, v in x_scores.items():
        a, b = sorted(k, key=FULL.index)
        i, j = FULL.index(a), FULL.index(b)
        X[i, j] = X[j, i] = np.mean(v)
    return rates, w, X


def ratio(ws, Xs, idx=None):
    num = den = 0.0
    for w, X in zip(ws, Xs):
        if idx is None:
            den += w.mean()
            num += X[np.triu_indices(10, 1)].mean()
        else:
            den += w[idx].mean()
            ii, jj = np.triu_indices(len(idx), 1)
            a, b = idx[ii], idx[jj]
            keep = a != b
            num += X[a[keep], b[keep]].mean()
    return num / den


def primary(ws, Xs, seed=20261012, B=2000):
    R = ratio(ws, Xs)
    rng = np.random.default_rng(seed)
    bs = np.array([ratio(ws, Xs, rng.integers(0, 10, 10)) for _ in range(B)])
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return dict(R=float(R), lo=float(lo), hi=float(hi), verdict="Supported" if hi < 0.8 else "Refuted" if lo >= 0.8 else "Inconclusive",
                W=[float(w.mean()) for w in ws], X=[float(X[np.triu_indices(10, 1)].mean()) for X in Xs])


for cut in (0.5, 0.8):
    out = {}
    ws, Xs = [], []
    for L in LAYERS:
        rates, w, X = group_rates_and_scores(L, cut)
        ws.append(w)
        Xs.append(X)
        out[f"L{L}_rates"] = rates
        tot = sum(v["n"] for k, v in rates.items() if k.startswith("within"))
        out[f"L{L}_token_share"] = rates["within|token"]["n"] / tot
        out[f"L{L}_token_ratio"] = rates["full|token"]["rate"] / rates["within|token"]["rate"]
        out[f"L{L}_other_ratio"] = rates["full|other"]["rate"] / rates["within|other"]["rate"]
        out[f"L{L}_share_of_cross_matches_that_are_token"] = rates["full|token"]["matched"] / (rates["full|token"]["matched"] + rates["full|other"]["matched"])
        out[f"L{L}_nontoken_primary"] = primary([w], [X])
    out["pooled_nontoken_primary"] = primary(ws, Xs)
    res[f"cut{cut}"] = out
    print(f"=== purity cut {cut}")
    for L in LAYERS:
        print(f"L{L}: token share {out[f'L{L}_token_share']:.3f}; rates", {k: round(v['rate'], 3) for k, v in out[f'L{L}_rates'].items()},
              f"token ratio {out[f'L{L}_token_ratio']:.3f} other ratio {out[f'L{L}_other_ratio']:.3f} share of cross matches that are token {out[f'L{L}_share_of_cross_matches_that_are_token']:.3f}")
        print(f"   non-token primary L{L}: {out[f'L{L}_nontoken_primary']}")
    print("   pooled non-token primary:", out["pooled_nontoken_primary"])

# compare with the study's tables (cut 0.5)
ti = pd.read_csv(TAB / "token_identity.csv")
mine = res["cut0.5"]
maxdiff = 0
for _, r in ti.iterrows():
    v = mine[f"L{r.layer}_rates"][f"{r.kind}|{r.group}"]
    maxdiff = max(maxdiff, abs(v["rate"] - r.rate), abs(v["n"] - r.n), abs(v["matched"] - r.matched))
prim = json.load(open(TAB / "token_identity_primary.json"))
print("max difference vs token_identity.csv (rate/n/matched):", maxdiff)
print("study non-token primary:", prim["R"], prim["lower95"], prim["upper95"], "| mine:", mine["pooled_nontoken_primary"])
res["study_primary"] = prim
res["max_diff_vs_table"] = float(maxdiff)

# purity distribution
for L in LAYERS:
    p = np.concatenate([pur[L][f"{m}_s{s}"] for m in FULL for s in range(3)])
    p = p[np.isfinite(p)]
    print(f"L{L} purity quantiles (fired latents) 10/25/50/75/90%:", np.round(np.quantile(p, [.1, .25, .5, .75, .9]), 3), "share>=0.5", round(float((p >= 0.5).mean()), 3), "share>=0.8", round(float((p >= 0.8).mean()), 3), "share>=0.95", round(float((p >= 0.95).mean()), 3))

# from-scratch purity for one SAE
from sparsify import SparseCoder  # noqa: E402
from transformers import AutoModel  # noqa: E402

DEV = "cuda"
tokens = np.fromfile(RUN / "data" / "heldout_tokens.bin", dtype=np.uint16).reshape(-1, 2048)
m = AutoModel.from_pretrained(RUN / "data" / "raw" / "models" / "p160m", dtype=torch.bfloat16).to(DEV).eval()
sae = SparseCoder.load_from_disk(RUN / "data" / "sae" / "p160m" / "layers.4" / "seed0", device=DEV).float()
counts = {}
fired = torch.zeros(32768, dtype=torch.long, device=DEV)
top = torch.zeros(32768, dtype=torch.long, device=DEV)
pair_counts = torch.zeros(0, dtype=torch.long)
keys_all = []
with torch.no_grad():
    for b in range(0, len(tokens), 16):
        ids = torch.from_numpy(tokens[b:b + 16].astype(np.int64)).to(DEV)
        hs = m(ids, output_hidden_states=True).hidden_states[5]
        x = hs[:, 1:, :].reshape(-1, 768).float()
        _, idx, _ = sae.encode(x)
        tok = ids[:, 1:].reshape(-1)
        keys_all.append((idx.long() * 65536 + tok[:, None]).flatten().cpu())
keys = torch.cat(keys_all)
u, c = torch.unique(keys, return_counts=True)
lat = u // 65536
fired = torch.zeros(32768, dtype=torch.long).scatter_add_(0, lat, c)
top = torch.zeros(32768, dtype=torch.long).scatter_reduce_(0, lat, c, "amax", include_self=True)
mine_p = (top.double() / fired.clamp_min(1).double()).numpy()
mine_p[fired.numpy() == 0] = np.nan
stored = pur[4]["p160m_s0"]
ok = np.isfinite(stored) & np.isfinite(mine_p)
res["purity_recompute"] = dict(nan_pattern_identical=bool((np.isfinite(stored) == np.isfinite(mine_p)).all()),
                               max_abs_diff=float(np.abs(stored[ok] - mine_p[ok]).max()),
                               share_ge_0p5_stored=float((stored[ok] >= 0.5).mean()), share_ge_0p5_mine=float((mine_p[ok] >= 0.5).mean()),
                               fired_identical=bool((fired.numpy() == arr[4]["fired_p160m_s0"]).all()))
print("purity recompute p160m L4 s0:", res["purity_recompute"])
json.dump(res, open(OUT / "d9_check.json", "w"), indent=1, default=float)
print("written", OUT / "d9_check.json")
