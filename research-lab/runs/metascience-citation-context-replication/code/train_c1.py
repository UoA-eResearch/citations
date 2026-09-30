#!/usr/bin/env python
"""Classifier C1 (plan.md sec 3): SciBERT fine-tuned on CC30k majority-vote labels (Positive / Negative / Neutral).
Stratified 90/10 split (seed 0), 3 epochs, learning rate 2e-5, max length 256, batch 16, bf16 autocast.
Outputs: data/processed/c1_scibert/ (model), results/tables/c1_cc30k_test.csv (held-out metrics).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup

RUN = Path(__file__).resolve().parents[1]
MODEL = "allenai/scibert_scivocab_uncased"
LABELS = ["Negative", "Neutral", "Positive"]
OUT = RUN / "data" / "processed" / "c1_scibert"


def batches(texts, labels, tok, bs, shuffle, rng):
    idx = rng.permutation(len(texts)) if shuffle else np.arange(len(texts))
    for i in range(0, len(idx), bs):
        j = idx[i:i + bs]
        enc = tok([texts[k] for k in j], truncation=True, max_length=256, padding=True, return_tensors="pt")
        yield {k: v.cuda() for k, v in enc.items()}, (torch.tensor(labels[j]).cuda() if labels is not None else None)


def predict(model, tok, texts, bs=64):
    model.eval()
    probs = []
    with torch.no_grad(), torch.autocast("cuda", dtype=torch.bfloat16):
        for enc, _ in batches(texts, None, tok, bs, False, None):
            probs.append(torch.softmax(model(**enc).logits.float(), -1).cpu().numpy())
    return np.concatenate(probs)


def main():
    d = pd.read_csv(RUN / "data" / "raw" / "cc30k_dataset.csv", low_memory=False)
    d = d[d.majority_vote.isin(LABELS) & d.input_context.notna()]
    y = d.majority_vote.map({l: i for i, l in enumerate(LABELS)}).values
    tr_idx, te_idx = train_test_split(np.arange(len(d)), test_size=0.1, stratify=y, random_state=0)
    texts = d.input_context.astype(str).tolist()
    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL, num_labels=3).cuda()
    opt = torch.optim.AdamW(model.parameters(), lr=2e-5, weight_decay=0.01)
    steps = 3 * int(np.ceil(len(tr_idx) / 16))
    sch = get_linear_schedule_with_warmup(opt, int(0.06 * steps), steps)
    rng = np.random.default_rng(0)
    tr_texts, tr_y = [texts[i] for i in tr_idx], y[tr_idx]
    for epoch in range(3):
        model.train()
        tot = 0.0
        for n, (enc, lab) in enumerate(batches(tr_texts, tr_y, tok, 16, True, rng)):
            with torch.autocast("cuda", dtype=torch.bfloat16):
                loss = torch.nn.functional.cross_entropy(model(**enc).logits.float(), lab)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sch.step()
            opt.zero_grad()
            tot += loss.item()
        print(f"epoch {epoch + 1} mean loss {tot / (n + 1):.4f}", flush=True)
    p = predict(model, tok, [texts[i] for i in te_idx])
    rep = classification_report(y[te_idx], p.argmax(1), target_names=LABELS, output_dict=True)
    out = pd.DataFrame(rep).T
    (RUN / "results" / "tables").mkdir(parents=True, exist_ok=True)
    out.to_csv(RUN / "results" / "tables" / "c1_cc30k_test.csv")
    print(out.round(3).to_string())
    OUT.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(OUT)
    tok.save_pretrained(OUT)


if __name__ == "__main__":
    sys.exit(main())
