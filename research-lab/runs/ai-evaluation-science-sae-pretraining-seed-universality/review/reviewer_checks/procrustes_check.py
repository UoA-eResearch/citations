"""Reviewer check: is the Procrustes fit dominated by outlier dimensions, and does it matter?

For the full-seed pair (p160m -> p160m-seed5) and one data-order pair (p160m -> p160m-data-seed1), at layers 4 and 8:
fit on sequences 0-127 of H, evaluate on 128-255 (as code/exploratory.py), position 0 dropped.
Maps compared:
  raw       orthogonal Procrustes on centred raw activations (the study's map);
  std       orthogonal Procrustes on per-dimension standardised activations, mapped back to B's raw scale
            (a linear, non-orthogonal map in raw coordinates);
  raw-noout orthogonal Procrustes fitted with the union of the two models' top-10 mean-square dimensions zeroed
            in both (then applied to the full vectors);
  lstsq     general least-squares linear map (ceiling for linear maps).
Reports: share of the Procrustes objective trace(R^T A^T B) carried by the top-10 dims; map FVU on held-out tokens;
B's seed-0 SAE FVU on the mapped A activations; share of A's decoder rows with rotated cosine >= 0.5 to B's.
Usage: venv/bin/python review/reviewer_checks/procrustes_check.py  (GPU, a few minutes)"""
import json
import sys
from pathlib import Path

import numpy as np
import torch
from sparsify import SparseCoder
from transformers import AutoModel

torch.backends.cuda.matmul.allow_tf32 = False
RUN = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
DEV = "cuda"
CTX = 2048
PAIRS = [("p160m", "p160m-seed5", "full"), ("p160m", "p160m-data-seed1", "data")]


@torch.no_grad()
def residual(model, layer, tokens, batch=16):
    m = AutoModel.from_pretrained(RUN / "data" / "raw" / "models" / model, dtype=torch.bfloat16).to(DEV).eval()
    xs = []
    for b in range(0, len(tokens), batch):
        hs = m(torch.from_numpy(tokens[b:b + batch].astype(np.int64)).to(DEV), output_hidden_states=True).hidden_states[layer + 1]
        xs.append(hs[:, 1:, :].reshape(-1, hs.shape[-1]).float())
    del m
    torch.cuda.empty_cache()
    return torch.cat(xs)


def fvu(pred, target):
    return float(((pred - target) ** 2).sum() / ((target - target.mean(0)) ** 2).sum())


@torch.no_grad()
def sae_fvu(sae, x, chunk=65536):
    err = 0.0
    for t in range(0, len(x), chunk):
        xx = x[t:t + chunk]
        acts, idx, _ = sae.encode(xx)
        err += float(((sae.decode(acts, idx) - xx) ** 2).sum())
    return err / float(((x - x.mean(0)) ** 2).sum())


def procrustes(a, b):
    U, S, Vt = torch.linalg.svd(a.T @ b)
    return U @ Vt, S


@torch.no_grad()
def main():
    tokens = np.fromfile(RUN / "data" / "heldout_tokens.bin", dtype=np.uint16).reshape(-1, CTX)[:256]
    n_fit = 128 * (CTX - 1)
    out = {}
    for L in [4, 8]:
        for a_name, b_name, kind in PAIRS:
            xa, xb = residual(a_name, L, tokens), residual(b_name, L, tokens)
            fa, fb, ea, eb = xa[:n_fit], xb[:n_fit], xa[n_fit:], xb[n_fit:]
            mua, mub = fa.mean(0), fb.mean(0)
            sda, sdb = fa.std(0), fb.std(0)
            sae = SparseCoder.load_from_disk(RUN / "data" / "sae" / b_name / f"layers.{L}" / "seed0", device=DEV).float()
            Wb = sae.W_dec.detach().float()
            Wb = Wb / Wb.norm(dim=1, keepdim=True)
            sae_a = SparseCoder.load_from_disk(RUN / "data" / "sae" / a_name / f"layers.{L}" / "seed1", device=DEV).float()
            Wa = sae_a.W_dec.detach().float()
            Wa = Wa / Wa.norm(dim=1, keepdim=True)
            del sae_a
            r = dict(layer=L, kind=kind, a=a_name, b=b_name, sae_fvu_own_B=sae_fvu(sae, eb))
            # variance concentration and the share of the Procrustes objective carried by the top-10 dims
            ms_a, ms_b = (fa - mua).pow(2).mean(0), (fb - mub).pow(2).mean(0)
            top_a, top_b = ms_a.topk(10).indices, ms_b.topk(10).indices
            r["top10_var_share"] = [float(ms_a[top_a].sum() / ms_a.sum()), float(ms_b[top_b].sum() / ms_b.sum())]
            R, S = procrustes(fa - mua, fb - mub)
            M = (fa - mua).T @ (fb - mub)
            obj_total = float(S.sum())
            # contribution of rows (A's top dims) and columns (B's top dims) of M to trace(R^T M) = sum_ij R_ij M_ij
            contrib = R * M
            r["objective_share_top10_rows_or_cols"] = float((contrib[top_a].sum() + contrib[:, top_b].sum() - contrib[top_a][:, top_b].sum()) / obj_total)
            maps = {}
            maps["raw"] = (ea - mua) @ R + mub
            # standardised Procrustes
            Rs, _ = procrustes((fa - mua) / sda, (fb - mub) / sdb)
            maps["std"] = ((ea - mua) / sda @ Rs) * sdb + mub
            # Procrustes with the union of top-10 dims zeroed during the fit
            drop = torch.unique(torch.cat([top_a, top_b]))
            fa2, fb2 = (fa - mua).clone(), (fb - mub).clone()
            fa2[:, drop] = 0
            fb2[:, drop] = 0
            Rn, _ = procrustes(fa2, fb2)
            maps["raw-noout"] = (ea - mua) @ Rn + mub
            # least squares
            Wl = torch.linalg.lstsq(torch.cat([fa, torch.ones(len(fa), 1, device=DEV)], 1), fb).solution
            maps["lstsq"] = torch.cat([ea, torch.ones(len(ea), 1, device=DEV)], 1) @ Wl
            for k, pred in maps.items():
                r[f"map_fvu_{k}"] = fvu(pred, eb)
                r[f"sae_fvu_{k}"] = sae_fvu(sae, pred)
            # map FVU restricted to the non-outlier dimensions (how good is the rotation off the outlier axes?)
            keep = torch.ones(ea.shape[1], dtype=torch.bool, device=DEV)
            keep[drop] = False
            r["map_fvu_raw_nonoutlier_dims"] = fvu(maps["raw"][:, keep], eb[:, keep])
            r["map_fvu_raw_outlier_dims"] = fvu(maps["raw"][:, ~keep], eb[:, ~keep])
            r["map_fvu_lstsq_nonoutlier_dims"] = fvu(maps["lstsq"][:, keep], eb[:, keep])
            # rotated decoder cosine, A's seed-1 decoder rows into B's basis, for raw / std / no-outlier rotations
            for k, Rm in (("raw", R), ("raw-noout", Rn)):
                rot = torch.cat([((Wa[i:i + 4096] @ Rm) @ Wb.T).max(1).values for i in range(0, len(Wa), 4096)])
                r[f"rcos0.5_{k}"] = float((rot >= 0.5).float().mean())
            Lin = Wl[:-1]  # raw-space linear map for decoder directions (not orthogonal; normalise after mapping)
            Wa_lin = Wa @ Lin
            Wa_lin = Wa_lin / Wa_lin.norm(dim=1, keepdim=True)
            rot = torch.cat([(Wa_lin[i:i + 4096] @ Wb.T).max(1).values for i in range(0, len(Wa), 4096)])
            r["rcos0.5_lstsq_map"] = float((rot >= 0.5).float().mean())
            r["rotation_frob_from_I"] = float((R - torch.eye(R.shape[0], device=DEV)).norm())
            r["haar_sqrt_2d"] = float(np.sqrt(2 * R.shape[0]))
            out[f"L{L}|{kind}"] = r
            print(json.dumps(r), flush=True)
            del xa, xb, fa, fb, ea, eb, maps, sae
            torch.cuda.empty_cache()
    json.dump(out, open(OUT / "procrustes_check.json", "w"), indent=1)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
