"""D7 (post hoc, exploratory): do latents that replicate across SAE seeds of one model also replicate across
pretraining seeds? For every SAE (m, s) of the 10 full-seed models, and each of its assessable latents:
  - within count: in how many of its two within pairs (with the model's other two SAE seeds) its best correlation is
    >= 0.7 (0, 1 or 2);
  - cross rate: the share of its full pairs (one per other full-seed model) in which its best correlation is >= 0.7.
Reports the mean cross rate by within count, per layer. Uses the stored per-latent arrays only.
Writes results/tables/exploratory_conditional.csv."""
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
FULL = ["p160m"] + [f"p160m-seed{i}" for i in range(1, 10)]


def sides(pairs, L, m, s, kind):
    """Best-correlation arrays of SAE (m, s) in every pair of `kind` that contains it."""
    out = []
    for _, p in pairs[(pairs.kind == kind)].iterrows():
        z = None
        if p.a == m and p.sa == s:
            z = "corr_a"
        elif p.b == m and p.sb == s:
            z = "corr_b"
        if z:
            out.append(np.load(RUN / "data" / "match" / f"L{L}" / f"pair_{p.id}.npz")[z].astype(np.float32))
    return out


def main():
    rows = []
    for L in [4, 8]:
        pairs = pd.read_csv(RUN / "results" / "tables" / f"pairs_L{L}.csv")
        for m in FULL:
            for s in range(3):
                w, x = sides(pairs, L, m, s, "within"), sides(pairs, L, m, s, "full")
                assert len(w) == 2 and len(x) == 9, (m, s, len(w), len(x))
                ok = np.isfinite(w[0])
                wc = sum((a >= 0.7) for a in w)
                xr = np.mean([(a >= 0.7) for a in x], axis=0)
                for c in range(3):
                    sel = ok & (wc == c)
                    rows.append(dict(layer=L, model=m, seed=s, within_count=c, n=int(sel.sum()),
                                     cross_rate=float(xr[sel].mean()) if sel.any() else np.nan))
    d = pd.DataFrame(rows)
    d.to_csv(RUN / "results" / "tables" / "exploratory_conditional.csv", index=False)
    g = d.groupby(["layer", "within_count"]).apply(lambda t: pd.Series(dict(
        latents=t.n.sum(), share=t.n.sum(), cross_rate=np.average(t.cross_rate, weights=t.n))), include_groups=False)
    g["share"] = g.latents / g.groupby(level=0).latents.transform("sum")
    print(g.round(3).to_string())


if __name__ == "__main__":
    main()
