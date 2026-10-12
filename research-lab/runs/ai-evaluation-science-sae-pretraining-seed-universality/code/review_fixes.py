"""D8 (analyses requested by the independent review; post hoc, exploratory; no verdict depends on them).

  (a) Firing-frequency terciles with the within row restricted to the 10 full-seed models (review issue 13; plan 7.4's
      version in secondary.json pools all 16 models in the within row).
  (b) D7's conditional replication stratified by the source latent's firing-frequency tercile (review issue 11).
  (c) Outlier dimensions: in how many of the seven lineage models' layer-4 and layer-8 top-10 lists each dimension
      appears, and whether any full seed's list overlaps the lineage's (review issue 9).
  (d) The Procrustes maps of exploratory.py (fitted on sequences 0-127 of H): ||R - I||_F against the Haar prediction
      sqrt(2 * 768), and det(R), for every cross-model pair of the design (review issue 8).
Writes results/tables/review_*.csv."""
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import match as M  # noqa: E402
from exploratory import FIT, residual  # noqa: E402
from pairs import MODELS, design  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
FULL = ["p160m"] + [f"p160m-seed{i}" for i in range(1, 10)]
LINEAGE = ["p160m"] + [f"p160m-weight-seed{i}" for i in range(1, 4)] + [f"p160m-data-seed{i}" for i in range(1, 4)]


def terciles(L, model, seed, best):
    fired = np.load(RUN / "data" / "match" / f"L{L}" / f"fired_{model}_s{seed}.npy")
    ok = np.isfinite(best)
    q = np.quantile(fired[ok], [1 / 3, 2 / 3])  # as in analysis.by_frequency
    return ok, np.digitize(fired, q)


def freq_full_only():
    rows = []
    for L in [4, 8]:
        d = pd.read_csv(TAB / f"pairs_L{L}.csv")
        d = d[d.kind.isin(["within", "full"]) & d.a.isin(FULL) & d.b.isin(FULL)]
        for _, p in d.iterrows():
            z = np.load(RUN / "data" / "match" / f"L{L}" / f"pair_{p.id}.npz")
            for model, seed, key in ((p.a, p.sa, "corr_a"), (p.b, p.sb, "corr_b")):
                best = z[key].astype(np.float32)
                ok, t = terciles(L, model, seed, best)
                for k in range(3):
                    sel = ok & (t == k)
                    rows.append(dict(layer=L, kind=p.kind, tercile=k, n=int(sel.sum()), matched=int((best[sel] >= 0.7).sum())))
    g = pd.DataFrame(rows).groupby(["layer", "kind", "tercile"])[["n", "matched"]].sum()
    g["rate"] = g.matched / g.n
    g.to_csv(TAB / "review_frequency_full_seeds.csv")
    return g


def conditional_by_tercile():
    rows = []
    for L in [4, 8]:
        d = pd.read_csv(TAB / f"pairs_L{L}.csv")
        for m in FULL:
            for s in range(3):
                w, x = [], []
                for _, p in d[d.kind.isin(["within", "full"])].iterrows():
                    key = "corr_a" if (p.a == m and p.sa == s) else "corr_b" if (p.b == m and p.sb == s) else None
                    if key:
                        arr = np.load(RUN / "data" / "match" / f"L{L}" / f"pair_{p.id}.npz")[key].astype(np.float32)
                        (w if p.kind == "within" else x).append(arr)
                assert len(w) == 2 and len(x) == 9
                ok, t = terciles(L, m, s, w[0])
                wc = sum(a >= 0.7 for a in w)
                xr = np.mean([a >= 0.7 for a in x], axis=0)
                for k in range(3):
                    for c in range(3):
                        sel = ok & (t == k) & (wc == c)
                        rows.append(dict(layer=L, tercile=k, within_count=c, n=int(sel.sum()), cross_sum=float(xr[sel].sum())))
    g = pd.DataFrame(rows).groupby(["layer", "tercile", "within_count"])[["n", "cross_sum"]].sum()
    g["cross_rate"] = g.cross_sum / g.n
    g["share_in_tercile"] = g.n / g.groupby(level=[0, 1]).n.transform("sum")
    g.to_csv(TAB / "review_conditional_by_tercile.csv")
    return g


def outliers():
    o = pd.read_csv(TAB / "exploratory_outliers.csv")
    rows = []
    for L in [4, 8]:
        lin = o[(o.layer == L) & o.model.isin(LINEAGE)]
        c = Counter(int(x) for s in lin.top10_dims for x in s.split())
        lin_union = set(c)
        for dim, n in c.most_common(6):
            rows.append(dict(layer=L, what="lineage dim", dim=dim, in_lineage_top10=n))
        for _, r in o[(o.layer == L) & o.model.isin(FULL[1:])].iterrows():
            rows.append(dict(layer=L, what="full seed overlap with lineage union", dim=r.model,
                             in_lineage_top10=len(set(int(x) for x in r.top10_dims.split()) & lin_union)))
    d = pd.DataFrame(rows)
    d.to_csv(TAB / "review_outliers.csv", index=False)
    return d


@torch.no_grad()
def rotations():
    tokens = np.fromfile(RUN / "data" / "heldout_tokens.bin", dtype=np.uint16).reshape(-1, M.CTX)[FIT]
    model_pairs = sorted({(p["a"], p["b"], p["kind"]) for p in design() if p["kind"] != "within"})
    rows = []
    for L in [4, 8]:
        X = {m: residual(m, L, tokens).to(torch.bfloat16) for m in MODELS}
        for a, b, kind in model_pairs:
            fa, fb = X[a].float().to(M.DEV), X[b].float().to(M.DEV)
            U, _, Vt = torch.linalg.svd((fa - fa.mean(0)).T @ (fb - fb.mean(0)))
            R = (U @ Vt).double()
            rows.append(dict(layer=L, kind=kind, a=a, b=b, frob_from_I=float((R - torch.eye(768, device=M.DEV, dtype=R.dtype)).norm()),
                             det=float(torch.linalg.det(R))))
        del X
        torch.cuda.empty_cache()
    d = pd.DataFrame(rows)
    d.to_csv(TAB / "review_rotations.csv", index=False)
    return d


def main():
    print(freq_full_only().round(3).to_string())
    print(conditional_by_tercile().round(3).to_string())
    print(outliers().to_string())
    r = rotations()
    print("Haar sqrt(2*768) =", round(float(np.sqrt(2 * 768)), 2))
    print(r.groupby(["layer", "kind"]).agg(frob_mean=("frob_from_I", "mean"), frob_min=("frob_from_I", "min"),
                                            frob_max=("frob_from_I", "max"), det_neg=("det", lambda v: int((v < 0).sum())),
                                            n=("det", "size")).round(2).to_string())


if __name__ == "__main__":
    main()
