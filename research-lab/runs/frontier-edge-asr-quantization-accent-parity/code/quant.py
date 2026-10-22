"""Simulated quantization of Whisper's block linears (plan sections 3-4): RTN, GPTQ, AWQ-style, mixed precision.

Weights are quantized and dequantized to FP16 in place. Calibration statistics always come from the FP16 model
(non-sequential); the quantized weights are written only after every layer's statistics are collected.
"""
import math
import random

import torch
import torch.nn as nn

GROUP = 128


def block_linears(model):
    out = {}
    for part in ("encoder", "decoder"):
        for i, layer in enumerate(getattr(model.model, part).layers):
            for name, m in layer.named_modules():
                if isinstance(m, nn.Linear):
                    out[f"{part}.{i}.{name}"] = m
    return out


def grid(w, bits):
    """Asymmetric min-max grid per row of w (rows, cols), range forced to include 0 (as in the GPTQ reference)."""
    maxq = 2 ** bits - 1
    z0 = torch.zeros(w.shape[0], device=w.device)
    xmin, xmax = torch.minimum(w.min(1).values, z0), torch.maximum(w.max(1).values, z0)
    same = xmin == xmax
    xmin[same], xmax[same] = -1.0, 1.0
    scale = (xmax - xmin) / maxq
    zero = torch.round(-xmin / scale)
    return scale.unsqueeze(1), zero.unsqueeze(1), maxq


def qdq(w, scale, zero, maxq):
    return scale * (torch.clamp(torch.round(w / scale) + zero, 0, maxq) - zero)


def rtn_weight(W, bits):
    W = W.float()
    out = torch.empty_like(W)
    for j in range(0, W.shape[1], GROUP):
        s, z, m = grid(W[:, j:j + GROUP], bits)
        out[:, j:j + GROUP] = qdq(W[:, j:j + GROUP], s, z, m)
    return out


def gptq_weight(W, H, bits, block=128, damp=0.01):
    """GPTQ (Frantar et al. 2022), natural column order, lazy block updates, per-group grids as groups are reached."""
    W, H = W.float().clone(), H.clone()
    cols = W.shape[1]
    dead = torch.diag(H) == 0
    H[dead, dead] = 1.0
    W[:, dead] = 0.0
    for k in range(5):
        try:
            Hd = H + (damp * 10 ** k) * torch.mean(torch.diag(H)) * torch.eye(cols, device=H.device)
            Hinv = torch.linalg.cholesky(torch.cholesky_inverse(torch.linalg.cholesky(Hd)), upper=True)
            break
        except torch.linalg.LinAlgError:
            continue
    Q = torch.zeros_like(W)
    for i1 in range(0, cols, block):
        i2 = min(i1 + block, cols)
        W1, Q1, E1 = W[:, i1:i2].clone(), torch.zeros(W.shape[0], i2 - i1, device=W.device), None
        E1 = torch.zeros_like(Q1)
        Hi = Hinv[i1:i2, i1:i2]
        for i in range(i2 - i1):
            if (i1 + i) % GROUP == 0:
                s, z, m = grid(W1[:, i:i + GROUP], bits)
            w = W1[:, i]
            q = qdq(w.unsqueeze(1), s, z, m).squeeze(1)
            Q1[:, i] = q
            err = (w - q) / Hi[i, i]
            W1[:, i:] -= err.unsqueeze(1) @ Hi[i, i:].unsqueeze(0)
            E1[:, i] = err
        Q[:, i1:i2] = Q1
        W[:, i2:] -= E1 @ Hinv[i1:i2, i2:]
    return Q


class Collector:
    """Forward hooks on a subset of linears: Hessian 2XX^T/n, mean |x| per input channel, and a row sample of X."""

    def __init__(self, mods, hessian=True, sample_rows=0, seed=0):
        self.mods, self.hessian, self.sample_rows = mods, hessian, sample_rows
        self.H, self.n, self.absx, self.rows = {}, {}, {}, {}
        self.rng = random.Random(seed)
        self.per_call = 0
        self.handles = [m.register_forward_hook(self._hook(k)) for k, m in mods.items()]

    def _hook(self, k):
        def f(m, inp, out):
            x = inp[0].detach().reshape(-1, inp[0].shape[-1]).float()
            if self.hessian:
                if k not in self.H:
                    self.H[k] = torch.zeros(x.shape[1], x.shape[1], device=x.device)
                    self.n[k] = 0
                self.H[k] += x.T @ x
                self.n[k] += x.shape[0]
            self.absx[k] = self.absx.get(k, 0) + x.abs().sum(0)
            if self.sample_rows and self.per_call:
                idx = torch.tensor(self.rng.sample(range(x.shape[0]), min(self.per_call, x.shape[0])), device=x.device)
                self.rows.setdefault(k, []).append(x[idx].half().cpu())
        return f

    def close(self):
        for h in self.handles:
            h.remove()
        for k in list(self.H):
            self.H[k] = 2 * self.H[k] / self.n[k]


def run_calibration(model, batches, collector):
    collector.per_call = max(1, math.ceil(collector.sample_rows / len(batches))) if collector.sample_rows else 0
    with torch.no_grad():
        for feats, dec in batches:
            model(input_features=feats, decoder_input_ids=dec)
    collector.close()


def chunks(mods, budget_bytes=1.5e9):
    cur, size, out = {}, 0, []
    for k, m in mods.items():
        b = m.in_features ** 2 * 4
        if cur and size + b > budget_bytes:
            out.append(cur)
            cur, size = {}, 0
        cur[k] = m
        size += b
    return out + ([cur] if cur else [])


def quantize_gptq(model, batches, bits_of):
    """bits_of: module name -> bits (absent = left FP16)."""
    mods = {k: m for k, m in block_linears(model).items() if k in bits_of}
    new = {}
    for ch in chunks(mods):
        c = Collector(ch)
        run_calibration(model, batches, c)
        for k, m in ch.items():
            new[k] = gptq_weight(m.weight.data, c.H[k], bits_of[k]).half().cpu()
        del c
        torch.cuda.empty_cache()
    for k, w in new.items():
        mods[k].weight.data.copy_(w.to(mods[k].weight.device))


def quantize_rtn(model, bits):
    for m in block_linears(model).values():
        m.weight.data.copy_(rtn_weight(m.weight.data, bits).half())


def quantize_awq(model, batches, bits, alphas=(0.0, 0.25, 0.5, 0.75, 1.0), rows=2048):
    mods = block_linears(model)
    c = Collector(mods, hessian=False, sample_rows=rows)
    run_calibration(model, batches, c)
    chosen = {}
    for k, m in mods.items():
        X = torch.cat(c.rows[k]).to(m.weight.device).float()
        W = m.weight.data.float()
        Y = X @ W.T
        a = c.absx[k] / c.absx[k].numel()
        best = None
        for al in alphas:
            s = a.clamp(min=1e-8) ** al
            s = s / (s.max() * s.min()).sqrt()
            Wq = rtn_weight(W * s, bits) / s
            err = ((X @ Wq.T - Y) ** 2).mean().item()
            if best is None or err < best[0]:
                best = (err, al, Wq)
        chosen[k] = best[1]
        m.weight.data.copy_(best[2].half())
    return chosen


def layer_error(model, batches, rows=2048, bits=4):
    """Relative output error of RTN weights per linear on the given calibration batches."""
    mods = block_linears(model)
    c = Collector(mods, hessian=False, sample_rows=rows)
    run_calibration(model, batches, c)
    out = {}
    for k, m in mods.items():
        X = torch.cat(c.rows[k]).to(m.weight.device).float()
        W = m.weight.data.float()
        Y = X @ W.T
        out[k] = (((X @ rtn_weight(W, bits).T) - Y) ** 2).sum().item() / max((Y ** 2).sum().item(), 1e-12)
    return out


def size_bits(model, bits_of):
    """Packed size of the block linears: weights at their bits plus an FP16 scale and zero per group of 128."""
    tot = 0
    for k, m in block_linears(model).items():
        n = m.weight.numel()
        b = bits_of.get(k, 16)
        tot += n * b + (0 if b == 16 else (n // GROUP) * 32)
    return tot


def mixed_allocation(model, err_worst, err_best, promote_share=0.05, base=4, hi=8, lo=3):
    """Promote the most accent-differential layers to `hi` bits (>= 5% of weights); demote the least to `lo` bits until
    total bits match uniform `base` (plan section 4: base 4, hi 8, lo 3; D1 fallback: base 3, hi 8, lo 2)."""
    mods = block_linears(model)
    score = {k: err_worst[k] - err_best[k] for k in mods}
    order = sorted(mods, key=lambda k: score[k], reverse=True)
    total = sum(m.weight.numel() for m in mods.values())
    bits = {k: base for k in mods}
    target = size_bits(model, bits)
    promoted = 0
    for k in order:
        if promoted >= promote_share * total:
            break
        bits[k] = hi
        promoted += mods[k].weight.numel()
    for k in reversed(order):
        if size_bits(model, bits) <= target:
            break
        if bits[k] == base:
            bits[k] = lo
    # step back if overshot below target by more than 1%
    return bits, score, size_bits(model, bits) / target
