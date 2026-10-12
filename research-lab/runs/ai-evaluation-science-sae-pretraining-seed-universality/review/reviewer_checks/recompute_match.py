"""Reviewer check: an independent, dense re-implementation of the activation-correlation matching (plan section 4) for
one within pair and one full-seed pair at each layer, over the whole held-out set H, compared with the stored arrays
(data/match/L*/pair_<id>.npz) and the pair rows (results/tables/pairs_L*.csv).

Independence from code/match.py:
  - hookpoint: hidden_states[L + 1] from output_hidden_states=True (not a forward hook on m.layers[L]); it is also
    compared once with sparsify's own hook target (model.base_model.get_submodule('layers.L'));
  - SAE encode: sparsify's SparseCoder.load_from_disk(...).encode(...) (the installed library), not the study's SAE class;
  - cross-moments: dense fp32 matmul of the (tokens x latents) activation matrices (TF32 disabled), not the sparse
    k x k index_add_;
  - assessable rule, best match and fraction: re-implemented here.
Also recomputes FVU with sparsify's own forward() and the Procrustes rotation + rotated decoder cosine for the full pair.
Usage: venv/bin/python review/reviewer_checks/recompute_match.py   (GPU; ~20 minutes)"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sparsify import SparseCoder
from transformers import AutoModel

torch.backends.cuda.matmul.allow_tf32 = False
torch.backends.cudnn.allow_tf32 = False
RUN = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
DEV = "cuda"
CTX, NLAT, MIN_FIRE = 2048, 32768, 20
N_SEQ = int(sys.argv[1]) if len(sys.argv) > 1 else None  # all 1,025 sequences by default
CHUNK_TOK = 8192


@torch.no_grad()
def encode(model, layer, tokens, seeds, batch=16):
    """Returns per seed: dense-able (idx, val) per token, fired counts, FVU (sparsify forward), plus hook check."""
    m = AutoModel.from_pretrained(RUN / "data" / "raw" / "models" / model, dtype=torch.bfloat16).to(DEV).eval()
    saes = {s: SparseCoder.load_from_disk(RUN / "data" / "sae" / model / f"layers.{layer}" / f"seed{s}", device=DEV) for s in seeds}
    for s in saes:
        saes[s] = saes[s].float()
    # one-off hookpoint check: sparsify's hook target vs hidden_states[L+1]
    grab = {}
    h = m.base_model.get_submodule(f"layers.{layer}").register_forward_hook(
        lambda mod, inp, out: grab.__setitem__("x", out[0] if isinstance(out, tuple) else out))
    o = m(torch.from_numpy(tokens[:2].astype(np.int64)).to(DEV), output_hidden_states=True)
    h.remove()
    hs = o.hidden_states[layer + 1]
    hook_diff = float((hs.float() - grab["x"].float()).abs().max())
    n_hidden = len(o.hidden_states)
    out = {s: dict(idx=[], val=[]) for s in seeds}
    fired = {s: torch.zeros(NLAT, device=DEV, dtype=torch.long) for s in seeds}
    err = {s: 0.0 for s in seeds}
    sx = torch.zeros(m.config.hidden_size, device=DEV, dtype=torch.float64)
    sxx = 0.0
    n_tok = 0
    keep = []
    for b in range(0, len(tokens), batch):
        ids = torch.from_numpy(tokens[b:b + batch].astype(np.int64)).to(DEV)
        hs = m(ids, output_hidden_states=True).hidden_states[layer + 1]
        x = hs[:, 1:, :].reshape(-1, hs.shape[-1]).float()  # drop position 0
        sx += x.double().sum(0)
        sxx += float((x.double() ** 2).sum())
        n_tok += len(x)
        if n_tok <= 262_144:
            keep.append(x.to(torch.bfloat16).cpu())
        for s, sae in saes.items():
            top_acts, top_idx, _ = sae.encode(x)
            out[s]["idx"].append(top_idx.to(torch.int32).cpu())
            out[s]["val"].append(top_acts.float().cpu())
            fired[s] += torch.bincount(top_idx.flatten(), minlength=NLAT)
            recon = sae.decode(top_acts, top_idx)
            err[s] += float(((recon - x) ** 2).sum())
    tot = sxx - float((sx ** 2).sum()) / n_tok
    res = {}
    for s in seeds:
        res[s] = dict(idx=torch.cat(out[s]["idx"]), val=torch.cat(out[s]["val"]), fired=fired[s].cpu(),
                      fvu=err[s] / tot, W_dec=saes[s].W_dec.detach().float().cpu())
    del m
    torch.cuda.empty_cache()
    return res, torch.cat(keep)[:262_144], n_tok, dict(hook_vs_hidden_states_maxdiff=hook_diff, n_hidden_states=n_hidden)


@torch.no_grad()
def dense_corr_best(A, B, n_tok):
    """Dense Pearson correlation of every latent of A with every latent of B, over n_tok tokens, in fp32 (no TF32)."""
    C = torch.zeros(NLAT, NLAT, device=DEV, dtype=torch.float32)
    sa = torch.zeros(NLAT, device=DEV, dtype=torch.float64)
    sb = torch.zeros(NLAT, device=DEV, dtype=torch.float64)
    ssa = torch.zeros(NLAT, device=DEV, dtype=torch.float64)
    ssb = torch.zeros(NLAT, device=DEV, dtype=torch.float64)
    for t in range(0, n_tok, CHUNK_TOK):
        ia, va = A["idx"][t:t + CHUNK_TOK].to(DEV).long(), A["val"][t:t + CHUNK_TOK].to(DEV)
        ib, vb = B["idx"][t:t + CHUNK_TOK].to(DEV).long(), B["val"][t:t + CHUNK_TOK].to(DEV)
        Da = torch.zeros(len(ia), NLAT, device=DEV).scatter_(1, ia, va)
        Db = torch.zeros(len(ib), NLAT, device=DEV).scatter_(1, ib, vb)
        C += Da.T @ Db
        sa += Da.double().sum(0)
        sb += Db.double().sum(0)
        ssa += (Da.double() ** 2).sum(0)
        ssb += (Db.double() ** 2).sum(0)
        del Da, Db
    mu_a, mu_b = sa / n_tok, sb / n_tok
    sd_a = (ssa / n_tok - mu_a ** 2).clamp_min(0).sqrt()
    sd_b = (ssb / n_tok - mu_b ** 2).clamp_min(0).sqrt()
    ok_a, ok_b = (A["fired"] >= MIN_FIRE).to(DEV), (B["fired"] >= MIN_FIRE).to(DEV)
    best_a = torch.full((NLAT,), float("nan"), device=DEV, dtype=torch.float64)
    best_b = torch.full((NLAT,), float("-inf"), device=DEV, dtype=torch.float64)
    for r0 in range(0, NLAT, 4096):
        cov = C[r0:r0 + 4096].double() / n_tok - mu_a[r0:r0 + 4096, None] * mu_b[None, :]
        r = cov / (sd_a[r0:r0 + 4096, None] * sd_b[None, :]).clamp_min(1e-12)
        r = torch.where(ok_b[None, :], r, torch.full_like(r, float("-inf")))
        r = torch.where(ok_a[r0:r0 + 4096, None], r, torch.full_like(r, float("-inf")))
        best_a[r0:r0 + 4096] = r.max(1).values
        best_b = torch.maximum(best_b, r.max(0).values)
    best_a[~ok_a] = float("nan")
    best_b[~ok_b] = float("nan")
    del C
    torch.cuda.empty_cache()
    return best_a.cpu().numpy(), best_b.cpu().numpy()


def frac(best, th):
    ok = np.isfinite(best)
    return float((best[ok] >= th).mean())


def main():
    tokens = np.fromfile(RUN / "data" / "heldout_tokens.bin", dtype=np.uint16).reshape(-1, CTX)[:N_SEQ]
    report = {}
    for L in [4, 8]:
        d = pd.read_csv(RUN / "results" / "tables" / f"pairs_L{L}.csv")
        q = pd.read_csv(RUN / "results" / "tables" / f"sae_quality_L{L}.csv")
        # one within pair of the original and one full pair (original vs seed5, SAE seeds 1 vs 2)
        within = d[(d.kind == "within") & (d.a == "p160m") & (d.sa == 0) & (d.sb == 1)].iloc[0]
        full = d[(d.kind == "full") & (d.a == "p160m") & (d.b == "p160m-seed5") & (d.sa == 1)].iloc[0]
        t0 = time.time()
        encA, keepA, n_tok, hookA = encode("p160m", L, tokens, [0, 1])
        encB, keepB, n_tok_b, hookB = encode("p160m-seed5", L, tokens, [int(full.sb)])
        assert n_tok == n_tok_b
        print(f"L{L}: encoded ({time.time() - t0:.0f} s); n_tok={n_tok}; hook check {hookA} {hookB}", flush=True)
        rep = dict(n_tok=n_tok, hook_check_p160m=hookA, hook_check_seed5=hookB, pairs={})
        for name, p, A, B in (("within", within, encA[0], encA[1]), ("full", full, encA[int(full.sa)], encB[int(full.sb)])):
            t1 = time.time()
            ba, bb = dense_corr_best(A, B, n_tok)
            z = np.load(RUN / "data" / "match" / f"L{L}" / f"pair_{p.id}.npz")
            sa_, sb_ = z["corr_a"].astype(np.float32), z["corr_b"].astype(np.float32)
            r = dict(pair_id=int(p.id), a=p.a, sa=int(p.sa), b=p.b, sb=int(p.sb), seconds=round(time.time() - t1),
                     assessable_mine=[int(np.isfinite(ba).sum()), int(np.isfinite(bb).sum())],
                     assessable_stored=[int(p.assess_a), int(p.assess_b)],
                     nan_pattern_identical=[bool((np.isfinite(ba) == np.isfinite(sa_)).all()), bool((np.isfinite(bb) == np.isfinite(sb_)).all())],
                     max_abs_diff=[float(np.nanmax(np.abs(ba - sa_))), float(np.nanmax(np.abs(bb - sb_)))],
                     mean_abs_diff=[float(np.nanmean(np.abs(ba - sa_))), float(np.nanmean(np.abs(bb - sb_)))],
                     disagreements_at_0p7=[int(((ba >= 0.7) != (sa_ >= 0.7))[np.isfinite(ba)].sum()), int(((bb >= 0.7) != (sb_ >= 0.7))[np.isfinite(bb)].sum())])
            for th in (0.5, 0.7, 0.9):
                r[f"f{th}_mine"] = [frac(ba, th), frac(bb, th), (frac(ba, th) + frac(bb, th)) / 2]
                r[f"f{th}_stored"] = [float(p[f"f{th}_ab"]), float(p[f"f{th}_ba"]), float(p[f"f{th}"])]
            # fired counts vs stored
            for side, model, seed, E in (("a", p.a, p.sa, A), ("b", p.b, p.sb, B)):
                st = np.load(RUN / "data" / "match" / f"L{L}" / f"fired_{model}_s{seed}.npy")
                r[f"fired_{side}_identical"] = bool((st == E["fired"].numpy()).all())
                r[f"fvu_{side}_mine"] = float(E["fvu"])
                r[f"fvu_{side}_stored"] = float(q[(q.model == model) & (q.seed == seed)].fvu.iloc[0])
            # decoder cosine, raw and rotated (full pair only)
            Wa = A["W_dec"].to(DEV)
            Wb = B["W_dec"].to(DEV)
            Wa = Wa / Wa.norm(dim=1, keepdim=True)
            Wb = Wb / Wb.norm(dim=1, keepdim=True)
            raw = torch.cat([(Wa[i:i + 4096] @ Wb.T).max(1).values for i in range(0, NLAT, 4096)])
            r["cos0.5_mine_a_side"] = float((raw >= 0.5).float().mean())
            r["cos_max_a_side"] = float(raw.max())
            if name == "full":
                a = keepA.to(DEV).float()
                b = keepB.to(DEV).float()
                a, b = a - a.mean(0), b - b.mean(0)
                U, S, Vt = torch.linalg.svd(a.T @ b)
                R = U @ Vt
                r["rotation_det"] = float(torch.linalg.det(R))
                r["rotation_frob_dist_from_I"] = float((R - torch.eye(R.shape[0], device=DEV)).norm())
                r["haar_prediction_sqrt_2d"] = float(np.sqrt(2 * R.shape[0]))
                rot = torch.cat([((Wa[i:i + 4096] @ R) @ Wb.T).max(1).values for i in range(0, NLAT, 4096)])
                rotb = torch.cat([(Wb[i:i + 4096] @ (Wa @ R).T).max(1).values for i in range(0, NLAT, 4096)])
                r["rcos0.5_mine"] = float(((rot >= 0.5).float().mean() + (rotb >= 0.5).float().mean()) / 2)
                r["rcos0.5_stored"] = float(p["rcos0.5"])
                # how well does the rotation map A's residual onto B's on the fit tokens (FVU)?
                r["rotation_fit_fvu"] = float(((a @ R - b) ** 2).sum() / (b ** 2).sum())
                # share of variance in the top-10 dimensions of each model on the fit tokens
                r["top10_var_share"] = [float(a.var(0).topk(10).values.sum() / a.var(0).sum()), float(b.var(0).topk(10).values.sum() / b.var(0).sum())]
            rep["pairs"][name] = r
            print(f"L{L} {name}: {json.dumps(r)}", flush=True)
        report[f"L{L}"] = rep
        del encA, encB
        torch.cuda.empty_cache()
    json.dump(report, open(OUT / "recompute_match.json", "w"), indent=1)
    print("DONE", OUT / "recompute_match.json", flush=True)


if __name__ == "__main__":
    main()
