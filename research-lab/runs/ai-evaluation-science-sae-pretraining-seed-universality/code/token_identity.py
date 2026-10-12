"""D9 (post hoc, exploratory): are the shared features mostly token-identity latents? The lead's risk note said
activation matching across models may be inflated by token-identity features that every model has, and suggested
stratifying them out; the plan did not include that. This check:

  1. re-encodes H with the 30 SAEs of the 10 full-seed models at each layer (as match.encode_model) and records, per
     latent, its token purity: the share of its firings on H that fall on its single most frequent input token;
  2. calls a latent token-identity if its purity is at least 0.5;
  3. recomputes the primary statistic with the directional scores restricted to latents that are not token-identity
     (both as sources and as candidates is not possible from the stored best-match arrays, so candidates are unchanged:
     a non-token latent may still be matched by a token-identity latent of the other SAE), and reports within and
     cross match rates for token-identity and other latents separately.
Writes results/tables/token_purity_L{4,8}.npz, results/tables/token_identity.csv and token_identity_primary.json."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402
import match as M  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
FULL = A.FULL
PURE = 0.5


@torch.no_grad()
def purity(model, layer, tokens):
    res, _, n = M.encode_model(model, layer, tokens, {s: M.SAE(M.sae_dir(model, layer, s)) for s in M.SEEDS})
    tok = torch.from_numpy(tokens[:, 1:].reshape(-1).astype(np.int64))  # the input token at each kept position
    out = {}
    for s in M.SEEDS:
        lat = (res[s]["idx"].long() & 0xFFFF)  # (n, k)
        key = (lat * 65536 + tok[:, None]).flatten().to(M.DEV)
        u, c = torch.unique(key, return_counts=True)
        latent = (u // 65536).long()
        top = torch.zeros(M.NLAT, dtype=torch.long, device=M.DEV).scatter_reduce_(0, latent, c, "amax", include_self=True)
        fired = res[s]["fired"].to(M.DEV)
        p = (top.double() / fired.clamp_min(1).double()).cpu().numpy()
        p[fired.cpu().numpy() == 0] = np.nan
        out[s] = p
    del res
    torch.cuda.empty_cache()
    return out


def main():
    tokens = np.fromfile(RUN / "data" / "heldout_tokens.bin", dtype=np.uint16).reshape(-1, M.CTX)
    pur = {}
    for L in [4, 8]:
        f = TAB / f"token_purity_L{L}.npz"
        if f.exists():
            z = np.load(f)
            pur[L] = {(m, s): z[f"{m}_s{s}"] for m in FULL for s in M.SEEDS}
            continue
        pur[L] = {}
        for m in FULL:
            for s, p in purity(m, L, tokens).items():
                pur[L][(m, s)] = p
            print(f"L{L} purity {m}", flush=True)
        np.savez_compressed(f, **{f"{m}_s{s}": v for (m, s), v in pur[L].items()})
    rows, recomputed = [], {}
    for L in [4, 8]:
        d = pd.read_csv(TAB / f"pairs_L{L}.csv")
        d = d[d.kind.isin(["within", "full"]) & d.a.isin(FULL) & d.b.isin(FULL)].copy()
        fr = {"all": [], "non_token": []}
        for _, p in d.iterrows():
            z = np.load(RUN / "data" / "match" / f"L{L}" / f"pair_{p.id}.npz")
            sc = {}
            for side, m, s in (("a", p.a, p.sa), ("b", p.b, p.sb)):
                best = z[f"corr_{side}"].astype(np.float32)
                ok = np.isfinite(best)
                tid = pur[L][(m, s)] >= PURE
                for grp, sel in (("token", ok & tid), ("other", ok & ~tid)):
                    rows.append(dict(layer=L, kind=p.kind, group=grp, n=int(sel.sum()), matched=int((best[sel] >= 0.7).sum())))
                sc[side] = float((best[ok & ~tid] >= 0.7).mean())
            d.loc[_, "f0.7_nontoken"] = (sc["a"] + sc["b"]) / 2
        recomputed[L] = d
    g = pd.DataFrame(rows).groupby(["layer", "kind", "group"])[["n", "matched"]].sum()
    g["rate"] = g.matched / g.n
    g["share_of_latents"] = g.n / g.groupby(level=[0, 1]).n.transform("sum")
    g.to_csv(TAB / "token_identity.csv")
    print(g.round(3).to_string())
    prim = A.primary_block(recomputed, col="f0.7_nontoken")
    # per layer (added after the pooled result was first printed; see D9)
    prim["per_layer"] = {str(L): A.primary_block(recomputed, col="f0.7_nontoken", layers=[L]) for L in [4, 8]}
    json.dump(prim, open(TAB / "token_identity_primary.json", "w"), indent=1)
    print(json.dumps(prim, indent=1))


if __name__ == "__main__":
    main()
