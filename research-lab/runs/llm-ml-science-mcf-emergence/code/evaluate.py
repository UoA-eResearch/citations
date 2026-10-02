#!/usr/bin/env python
"""Evaluate one checkpoint on all tasks (plan.md sec 3): five-shot MCF, zero-shot MCF and five-shot CF.

MCF: at the position after "Answer:", letter mass = total softmax probability (full vocabulary) on the item's valid
labels " A", " B", ...; prediction = the valid label with the highest logit.
CF: each option's summed log-probability as a continuation of the cloze context, divided by its length in characters.
Logits are computed only at the positions needed (base model + output head), in the model's training dtype.

Usage: evaluate.py MODEL_DIR RUN REVISION DTYPE
Output: results/evals/{RUN}/{REVISION}.parquet (one row per item x format: task, id, fmt, n_options, correct, mass)
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

RUN = Path(__file__).resolve().parents[1]
LETTERS = "ABCDE"
TASKS = ["arc_easy", "arc_challenge", "csqa", "piqa", "hellaswag", "mmlu"]


def load_items():
    return {t: [json.loads(l) for l in open(RUN / "data" / "items" / f"{t}.jsonl")] for t in TASKS}


def batches(lengths, budget):
    order = np.argsort(lengths)
    cur, mx = [], 0
    for i in order:
        m = max(mx, lengths[i])
        if cur and m * (len(cur) + 1) > budget:
            yield cur
            cur, m = [], lengths[i]
        cur.append(i)
        mx = m
    if cur:
        yield cur


@torch.no_grad()
def hidden_at(model, seqs, positions, budget, device):
    """Final hidden states at the requested positions for each sequence (right padding)."""
    head = model.get_output_embeddings()
    out = [None] * len(seqs)
    lengths = [len(s) for s in seqs]
    for b in batches(lengths, budget):
        L = max(lengths[i] for i in b)
        ids = torch.zeros((len(b), L), dtype=torch.long)
        att = torch.zeros((len(b), L), dtype=torch.long)
        for r, i in enumerate(b):
            ids[r, :lengths[i]] = torch.tensor(seqs[i])
            att[r, :lengths[i]] = 1
        h = model.base_model(input_ids=ids.to(device), attention_mask=att.to(device)).last_hidden_state
        for r, i in enumerate(b):
            out[i] = head(h[r, positions[i]]).float().log_softmax(-1).cpu()
    return out


def main():
    model_dir, run, revision, dtype = sys.argv[1:5]
    dest = RUN / "results" / "evals" / run
    dest.mkdir(parents=True, exist_ok=True)
    if (dest / f"{revision}.parquet").exists():
        return
    t0 = time.time()
    device = "cuda"
    tok = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForCausalLM.from_pretrained(model_dir, dtype=getattr(torch, dtype), attn_implementation="sdpa").to(device).eval()
    n_params = sum(p.numel() for p in model.parameters())
    budget = 24000 if n_params > 4e9 else 48000
    label_ids = [tok(" " + L, add_special_tokens=False).input_ids for L in LETTERS]
    assert all(len(x) == 1 for x in label_ids), label_ids
    label_ids = [x[0] for x in label_ids]
    items = load_items()
    rows = []
    for fmt in ("mcf5", "mcf0"):
        flat = [it for t in TASKS for it in items[t]]
        seqs = [tok(it[fmt]).input_ids for it in flat]
        lp = hidden_at(model, seqs, [[len(s) - 1] for s in seqs], budget, device)
        for it, l in zip(flat, lp):
            k = it["n_options"]
            v = l[0, label_ids[:k]]
            rows.append(dict(task=it["task"], id=it["id"], fmt=fmt, n_options=k, correct=int(int(v.argmax()) == it["gold"]),
                             mass=float(v.exp().sum())))
    # CF
    flat = [it for t in TASKS for it in items[t] if it["cf"]]
    seqs, pos, meta = [], [], []
    for it in flat:
        ctx = tok(it["cf_context"]).input_ids
        for j, o in enumerate(it["options"]):
            full = tok(it["cf_context"] + " " + o).input_ids
            if full[:len(ctx)] != ctx:
                full = ctx + tok(" " + o, add_special_tokens=False).input_ids
            c = len(full) - len(ctx)
            seqs.append(full)
            pos.append(list(range(len(ctx) - 1, len(full) - 1)))
            meta.append((it, j, full[len(ctx):], len(" " + o)))
    lp = hidden_at(model, seqs, pos, budget, device)
    scores = {}
    for (it, j, cont, nchar), l in zip(meta, lp):
        s = float(l[torch.arange(len(cont)), torch.tensor(cont)].sum()) / nchar
        scores.setdefault(it["id"], (it, []))[1].append(s)
    for iid, (it, sc) in scores.items():
        rows.append(dict(task=it["task"], id=iid, fmt="cf", n_options=it["n_options"],
                         correct=int(int(np.argmax(sc)) == it["gold"]), mass=np.nan))
    df = pd.DataFrame(rows)
    df.to_parquet(dest / f"{revision}.parquet", index=False)
    s = df.groupby(["fmt", "task"]).correct.mean().unstack(0).round(3)
    print(f"{run} {revision}: {time.time() - t0:.0f}s, params {n_params / 1e9:.2f}B", flush=True)
    return s


if __name__ == "__main__":
    main()
