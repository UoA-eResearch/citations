"""D5 (post hoc, exploratory; written after the primary and secondary results were seen). Two questions raised by the
decoder-geometry result (plan 7.5):

  (a) Outlier dimensions. Raw decoder cosine is zero across full seeds but not across the seed-0 lineage, even
      between a weight-seed and a data-seed variant, which share neither initialisation nor data order. Do the models
      share privileged residual coordinates? Per model and layer: the top-10 residual dimensions by mean square, and
      their share of the total.
  (b) McCann's reconstruction claim. Does an SAE trained on model B reconstruct model A's residual stream, raw, after
      an orthogonal Procrustes rotation, and after a general least-squares linear map? Also: how well does each map
      predict B's residual stream from A's on the same tokens?

Maps are fitted on sequences 0-127 of H and evaluated on sequences 128-255 (position 0 dropped, as everywhere).
SAE: B's seed-0 SAE. Pairs: every cross-model pair of the design (one direction, a -> b).
Writes results/tables/exploratory_outliers.csv and results/tables/exploratory_reconstruction.csv."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from transformers import AutoModel

sys.path.insert(0, str(Path(__file__).resolve().parent))
import match as M  # noqa: E402
from pairs import MODELS, design  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
FIT, EVAL = slice(0, 128), slice(128, 256)


@torch.no_grad()
def residual(model, layer, tokens, batch=16):
    m = AutoModel.from_pretrained(RUN / "data" / "raw" / "models" / model, dtype=torch.bfloat16).to(M.DEV).eval()
    grab = {}
    h = m.layers[layer].register_forward_hook(lambda mod, inp, out: grab.__setitem__("x", out[0] if isinstance(out, tuple) else out))
    xs = []
    for b in range(0, len(tokens), batch):
        m(torch.from_numpy(tokens[b:b + batch].astype(np.int64)).to(M.DEV))
        xs.append(grab["x"][:, 1:, :].reshape(-1, grab["x"].shape[-1]).float().cpu())
    h.remove()
    del m
    torch.cuda.empty_cache()
    return torch.cat(xs)


def fvu(pred, target):
    return float(((pred - target) ** 2).sum() / ((target - target.mean(0)) ** 2).sum())


@torch.no_grad()
def sae_fvu(sae, x, chunk=65536):
    err = 0.0
    for t in range(0, len(x), chunk):
        xx = x[t:t + chunk].to(M.DEV)
        err += float(((sae.decode(*sae.encode(xx)) - xx) ** 2).sum())
    return err / float(((x - x.mean(0)) ** 2).sum())


@torch.no_grad()
def main():
    tokens = np.fromfile(RUN / "data" / "heldout_tokens.bin", dtype=np.uint16).reshape(-1, M.CTX)[:256]
    n_fit = (FIT.stop - FIT.start) * (M.CTX - 1)
    pairs = [p for p in design() if p["kind"] != "within"]
    model_pairs = sorted({(p["a"], p["b"], p["kind"]) for p in pairs})
    out_rows, rec_rows = [], []
    for L in [4, 8]:
        X = {m: residual(m, L, tokens).to(torch.bfloat16) for m in MODELS}
        for m, x in X.items():
            ms = (x[n_fit:].float() ** 2).mean(0)
            top = torch.argsort(ms, descending=True)[:10]
            out_rows.append(dict(layer=L, model=m, top10_dims=" ".join(str(int(i)) for i in top),
                                 top10_share=float(ms[top].sum() / ms.sum()), top1_share=float(ms[top[0]] / ms.sum())))
        for a, b, kind in model_pairs:
            xa, xb = X[a].float(), X[b].float()
            fa, fb, ea, eb = xa[:n_fit].to(M.DEV), xb[:n_fit].to(M.DEV), xa[n_fit:].to(M.DEV), xb[n_fit:].to(M.DEV)
            mua, mub = fa.mean(0), fb.mean(0)
            U, _, Vt = torch.linalg.svd((fa - mua).T @ (fb - mub))
            Rot = U @ Vt
            Wl = torch.linalg.lstsq(torch.cat([fa, torch.ones(len(fa), 1, device=M.DEV)], 1), fb).solution
            orth = (ea - mua) @ Rot + mub
            lin = torch.cat([ea, torch.ones(len(ea), 1, device=M.DEV)], 1) @ Wl
            sae = M.SAE(M.sae_dir(b, L, 0))
            rec_rows.append(dict(layer=L, kind=kind, a=a, b=b,
                                 map_fvu_orth=fvu(orth, eb), map_fvu_lin=fvu(lin, eb),
                                 sae_fvu_own=sae_fvu(sae, eb), sae_fvu_raw=sae_fvu(sae, ea),
                                 sae_fvu_orth=sae_fvu(sae, orth), sae_fvu_lin=sae_fvu(sae, lin)))
            del fa, fb, ea, eb, orth, lin, sae
            torch.cuda.empty_cache()
        print(f"L{L} done", flush=True)
        del X
    tab = RUN / "results" / "tables"
    pd.DataFrame(out_rows).to_csv(tab / "exploratory_outliers.csv", index=False)
    d = pd.DataFrame(rec_rows)
    d.to_csv(tab / "exploratory_reconstruction.csv", index=False)
    print(d.groupby(["layer", "kind"])[[c for c in d.columns if c.startswith(("map", "sae"))]].mean().round(3).to_string())


if __name__ == "__main__":
    main()
