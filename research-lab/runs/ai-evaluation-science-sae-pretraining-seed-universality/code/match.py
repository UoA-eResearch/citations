"""Plan sections 4-5: encode the held-out set H with every SAE, then match latents between SAE pairs by activation
correlation.

For one layer L:
  1. For each model, run H (data/heldout_tokens.bin) through the model (bf16, as in training), take the residual
     stream output of block L (sparsify hookpoint `layers.L`), drop position 0 of every sequence, and encode it with
     each of the model's SAEs (seeds 0-2). Keep the top-k indices and values on the CPU. Also record, per SAE: firing
     counts, sums and sums of squares of each latent's activation, the fraction of variance unexplained (FVU) and
     dead latents. A subset of the residual stream (the first PROC_TOK tokens) is kept for the Procrustes alignment
     (secondary analysis).
  2. For each pair of SAEs (A, B) in the pair list, accumulate the cross-moment C_ij = sum_t a_i(t) b_j(t) exactly
     (sparse: k x k products per token, index_add_ in fp32), form the Pearson correlation of every latent pair over the
     N tokens of H, and record for every assessable latent (>= MIN_FIRE activations on H) of A its best correlation
     with an assessable latent of B, and vice versa. Decoder-cosine maxima are recorded too, raw and after an
     orthogonal Procrustes rotation of A's residual basis onto B's.

Output per layer: data/match/L{L}/pair_<id>.npz (per-latent best values) and results/tables/pairs_L{L}.csv (one row per
pair: match fractions at r >= 0.5 / 0.7 / 0.9 in each direction, assessable counts, decoder-cosine fractions) and
results/tables/sae_quality_L{L}.csv (FVU, dead fraction, assessable latents per SAE).
Usage: match.py <layer> [pairs_file]   (pairs default: the full design from pairs.py)"""
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from safetensors.torch import load_file
from transformers import AutoModel

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pairs import MODELS, SEEDS, design  # noqa: E402

CTX, K, NLAT = 2048, 32, 32768
MIN_FIRE, THRESHOLDS = 20, (0.5, 0.7, 0.9)
PROC_TOK = 262_144
DEV = "cuda"


class SAE:
    """sparsify TopK SAE (encoder Linear + bias, TopK on ReLU, decoder rows W_dec, b_dec subtracted before encoding)."""

    def __init__(self, path):
        cfg = json.loads((path / "cfg.json").read_text())
        w = load_file(path / "sae.safetensors", device=DEV)
        self.k = cfg["k"]
        self.W_enc, self.b_enc = w["encoder.weight"].float(), w["encoder.bias"].float()
        self.W_dec, self.b_dec = w["W_dec"].float(), w["b_dec"].float()

    def encode(self, x):
        pre = torch.relu((x - self.b_dec) @ self.W_enc.T + self.b_enc)
        v, i = pre.topk(self.k, dim=-1, sorted=False)
        return i, v

    def decode(self, i, v):
        return (v.unsqueeze(-1) * self.W_dec[i]).sum(-2) + self.b_dec


SAE_ROOT = Path(os.environ.get("SAE_ROOT", RUN / "data" / "sae"))  # dry runs: SAE_ROOT=data/sae_pilot
TAG = os.environ.get("MATCH_TAG", "")  # dry runs write *_<tag> files, never the study's tables
N_SEQ = int(os.environ.get("N_SEQ", 0)) or None  # dry runs: fewer sequences of H


def sae_dir(model, layer, seed):
    return SAE_ROOT / model / f"layers.{layer}" / f"seed{seed}"


@torch.no_grad()
def encode_model(model, layer, tokens, saes, batch=16):
    """Encode H with each SAE in `saes` (name -> SAE) on `model`'s block-`layer` output."""
    m = AutoModel.from_pretrained(RUN / "data" / "raw" / "models" / model, dtype=torch.bfloat16).to(DEV).eval()
    grab = {}
    # the same hookpoint as sparsify (`layers.L`): the output of block L
    h = m.layers[layer].register_forward_hook(lambda mod, inp, out: grab.__setitem__("x", out[0] if isinstance(out, tuple) else out))
    out = {s: dict(idx=[], val=[]) for s in saes}
    err = {s: 0.0 for s in saes}
    fired = {s: torch.zeros(NLAT, device=DEV, dtype=torch.long) for s in saes}
    sx = torch.zeros(m.config.hidden_size, device=DEV, dtype=torch.float64)
    sxx, n_tok, keep, n_keep = 0.0, 0, [], 0
    for b in range(0, len(tokens), batch):
        ids = torch.from_numpy(tokens[b:b + batch].astype(np.int64)).to(DEV)
        m(ids)
        x = grab["x"][:, 1:, :].reshape(-1, grab["x"].shape[-1]).float()  # drop position 0
        sx += x.double().sum(0)
        sxx += float((x.double() ** 2).sum())
        n_tok += len(x)
        if n_keep < PROC_TOK:
            keep.append(x[: PROC_TOK - n_keep].to(torch.bfloat16).cpu())
            n_keep += len(keep[-1])
        for s, sae in saes.items():
            i, v = sae.encode(x)
            out[s]["idx"].append(i.to(torch.int16).cpu())  # 32,768 latents: stored as int16, read back via & 0xFFFF
            out[s]["val"].append(v.to(torch.float32).cpu())
            err[s] += float(((sae.decode(i, v) - x) ** 2).sum())
            fired[s] += torch.bincount(i.flatten(), minlength=NLAT)
    h.remove()
    tot = sxx - float((sx ** 2).sum()) / n_tok  # total sum of squares about the mean
    res = {}
    for s in saes:
        idx = torch.cat(out[s]["idx"])
        val = torch.cat(out[s]["val"])
        il = idx.long() & 0xFFFF
        S = torch.zeros(NLAT, dtype=torch.float64).index_add_(0, il.flatten(), val.flatten().double())
        SS = torch.zeros(NLAT, dtype=torch.float64).index_add_(0, il.flatten(), val.flatten().double() ** 2)
        res[s] = dict(idx=idx, val=val, S=S, SS=SS, fired=fired[s].cpu(), fvu=err[s] / tot, W_dec=saes[s].W_dec.cpu())
    del m
    torch.cuda.empty_cache()
    return res, torch.cat(keep), n_tok


@torch.no_grad()
def corr_best(A, B, n_tok, chunk=32768):
    """Best Pearson correlation of each assessable latent of A with any assessable latent of B, and vice versa."""
    C = torch.zeros(NLAT * NLAT, device=DEV, dtype=torch.float32)
    for t in range(0, n_tok, chunk):
        ia = (A["idx"][t:t + chunk].to(DEV).long() & 0xFFFF)
        ib = (B["idx"][t:t + chunk].to(DEV).long() & 0xFFFF)
        va, vb = A["val"][t:t + chunk].to(DEV), B["val"][t:t + chunk].to(DEV)
        flat = (ia.unsqueeze(2) * NLAT + ib.unsqueeze(1)).flatten()
        C.index_add_(0, flat, (va.unsqueeze(2) * vb.unsqueeze(1)).flatten())
    C = C.view(NLAT, NLAT)
    mu_a, mu_b = (A["S"] / n_tok).to(DEV), (B["S"] / n_tok).to(DEV)
    sd_a = (A["SS"] / n_tok - (A["S"] / n_tok) ** 2).clamp_min(0).sqrt().to(DEV)
    sd_b = (B["SS"] / n_tok - (B["S"] / n_tok) ** 2).clamp_min(0).sqrt().to(DEV)
    ok_a, ok_b = (A["fired"] >= MIN_FIRE).to(DEV), (B["fired"] >= MIN_FIRE).to(DEV)
    best_a = torch.full((NLAT,), float("nan"), device=DEV, dtype=torch.float64)
    best_b = torch.full((NLAT,), -2.0, device=DEV, dtype=torch.float64)
    for r0 in range(0, NLAT, 4096):  # rows in blocks to bound memory
        cov = C[r0:r0 + 4096].double() / n_tok - mu_a[r0:r0 + 4096, None] * mu_b[None, :]
        r = cov / (sd_a[r0:r0 + 4096, None] * sd_b[None, :]).clamp_min(1e-12)
        r[:, ~ok_b] = -2.0
        r[~ok_a[r0:r0 + 4096]] = -2.0
        best_a[r0:r0 + 4096] = r.max(1).values
        best_b = torch.maximum(best_b, r.max(0).values)
    best_a[~ok_a] = float("nan")
    best_b[~ok_b] = float("nan")
    del C
    torch.cuda.empty_cache()
    return best_a.float().cpu().numpy(), best_b.float().cpu().numpy()


@torch.no_grad()
def dec_cos_best(Wa, Wb, Rot=None):
    """Max |cosine| between each decoder row of A (optionally rotated into B's basis) and B's decoder rows."""
    a = Wa.to(DEV)
    if Rot is not None:
        a = a @ Rot.to(DEV)
    a = a / a.norm(dim=1, keepdim=True)
    b = Wb.to(DEV) / Wb.to(DEV).norm(dim=1, keepdim=True)
    best_a = torch.cat([(a[r:r + 4096] @ b.T).max(1).values for r in range(0, NLAT, 4096)])
    best_b = torch.cat([(b[r:r + 4096] @ a.T).max(1).values for r in range(0, NLAT, 4096)])
    return best_a.cpu().numpy(), best_b.cpu().numpy()


def frac(best, th):
    """Share of assessable latents (finite best value) whose best match is at least th."""
    ok = np.isfinite(best)
    return float((best[ok] >= th).mean()) if ok.any() else float("nan")


def procrustes(Xa, Xb):
    """Orthogonal R minimising ||(Xa - mean) R - (Xb - mean)||_F."""
    a = Xa.to(DEV).float()
    b = Xb.to(DEV).float()
    a, b = a - a.mean(0), b - b.mean(0)
    U, _, Vt = torch.linalg.svd(a.T @ b)
    return (U @ Vt).cpu()


def main(layer, pairs_file=None):
    tokens = np.fromfile(RUN / "data" / "heldout_tokens.bin", dtype=np.uint16).reshape(-1, CTX)[:N_SEQ]
    pairs = design() if pairs_file is None else json.loads(Path(pairs_file).read_text())
    needed = sorted({p["a"] for p in pairs} | {p["b"] for p in pairs})
    enc, proc, qual = {}, {}, []
    t0 = time.time()
    out_dir = RUN / "data" / "match" / f"L{layer}{TAG}"
    out_dir.mkdir(parents=True, exist_ok=True)
    for mname in needed:
        res, keep, n_tok = encode_model(mname, layer, tokens, {s: SAE(sae_dir(mname, layer, s)) for s in SEEDS})
        enc[mname], proc[mname] = res, keep
        for s in SEEDS:
            qual.append(dict(model=mname, seed=s, fvu=res[s]["fvu"], dead=float((res[s]["fired"] == 0).float().mean()),
                             assessable=int((res[s]["fired"] >= MIN_FIRE).sum()), n_tok=n_tok))
            np.save(out_dir / f"fired_{mname}_s{s}.npy", res[s]["fired"].numpy())
        print(f"L{layer} encoded {mname} ({time.time() - t0:.0f} s)", flush=True)
    # plan 7.7: EleutherAI's reference SAE on the original model, as context for the training budget
    ref_dir = RUN / "data" / "raw" / "eai_sae_ref" / f"layers.{layer}"
    ref_rows = []
    if "p160m" in enc and ref_dir.exists():
        ref, _, n_ref = encode_model("p160m", layer, tokens, {"ref": SAE(ref_dir)})
        ref = ref["ref"]
        qual.append(dict(model="eai_reference", seed=-1, fvu=ref["fvu"], dead=float((ref["fired"] == 0).float().mean()),
                         assessable=int((ref["fired"] >= MIN_FIRE).sum()), n_tok=n_ref))
        for s in SEEDS:
            ba, bb = corr_best(enc["p160m"][s], ref, n_tok)
            ref_rows.append(dict(kind="reference", a="p160m", sa=s, b="eai_reference", sb=-1, id=-1 - s,
                                 **{f"f{th}": (frac(ba, th) + frac(bb, th)) / 2 for th in THRESHOLDS}))
        del ref
        torch.cuda.empty_cache()
    tab = RUN / "results" / "tables"
    tab.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(qual).to_csv(tab / f"sae_quality_L{layer}{TAG}.csv", index=False)
    pd.DataFrame(ref_rows).to_csv(tab / f"reference_L{layer}{TAG}.csv", index=False)
    rows = []
    rot_cache = {}
    for n, p in enumerate(pairs):
        A, B = enc[p["a"]][p["sa"]], enc[p["b"]][p["sb"]]
        ba, bb = corr_best(A, B, n_tok)
        if p["a"] == p["b"]:
            Rot = None
        else:
            key = (p["a"], p["b"])
            if key not in rot_cache:
                rot_cache[key] = procrustes(proc[p["a"]], proc[p["b"]])
            Rot = rot_cache[key]
        ca, cb = dec_cos_best(A["W_dec"], B["W_dec"])
        ra, rb = dec_cos_best(A["W_dec"], B["W_dec"], Rot) if Rot is not None else (ca, cb)
        np.savez_compressed(out_dir / f"pair_{p['id']}.npz", corr_a=ba.astype(np.float16), corr_b=bb.astype(np.float16),
                            cos_a=ca.astype(np.float16), cos_b=cb.astype(np.float16),
                            rcos_a=ra.astype(np.float16), rcos_b=rb.astype(np.float16))
        row = dict(p)
        row.update(assess_a=int(np.isfinite(ba).sum()), assess_b=int(np.isfinite(bb).sum()))
        for th in THRESHOLDS:
            fa, fb = frac(ba, th), frac(bb, th)
            row[f"f{th}_ab"], row[f"f{th}_ba"], row[f"f{th}"] = fa, fb, (fa + fb) / 2
        for nm, (xa, xb) in (("cos", (ca, cb)), ("rcos", (ra, rb))):
            for th in (0.5, 0.7):
                row[f"{nm}{th}"] = (np.mean(xa >= th) + np.mean(xb >= th)) / 2
        rows.append(row)
        if n % 10 == 0:
            print(f"L{layer} pair {n + 1}/{len(pairs)} ({time.time() - t0:.0f} s)", flush=True)
            pd.DataFrame(rows).to_csv(tab / f"pairs_L{layer}{TAG}.csv", index=False)
    pd.DataFrame(rows).to_csv(tab / f"pairs_L{layer}{TAG}.csv", index=False)
    print(f"MATCH L{layer} DONE", flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]), sys.argv[2] if len(sys.argv) > 2 else None)
