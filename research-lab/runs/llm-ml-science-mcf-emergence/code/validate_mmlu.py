#!/usr/bin/env python
"""Diagnostic for the MMLU validation gap (deviations.md D2); it does not change the study's prompts.

Final OLMo-7B-0424 checkpoint, five-shot MCF on 2,000 MMLU test items (seed 1), in two prompt variants: the study's
prompt, and the same with the OLMES-style header "The following are multiple choice questions (with answers) about
{subject}." Reports micro and subject-macro accuracy for each.
Usage: validate_mmlu.py MODEL_DIR  -> results/tables/validation_mmlu.csv
"""
import random
import sys
from pathlib import Path

import pandas as pd
import torch
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_items as BI  # noqa: E402
import evaluate as EV  # noqa: E402

RUN = Path(__file__).resolve().parents[1]


def main():
    model_dir = sys.argv[1]
    tok = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForCausalLM.from_pretrained(model_dir, dtype=torch.bfloat16, attn_implementation="sdpa").to("cuda").eval()
    label_ids = [tok(" " + L, add_special_tokens=False).input_ids[0] for L in "ABCD"]
    test = load_dataset("cais/mmlu", "all", split="test")
    dev = load_dataset("cais/mmlu", "all", split="dev")
    shots = {}
    for x in dev:
        shots.setdefault(x["subject"], []).append(dict(q=x["question"], options=x["choices"], gold=int(x["answer"])))
    idx = random.Random(1).sample(range(len(test)), 2000)
    items = [dict(q=test[i]["question"], options=test[i]["choices"], gold=int(test[i]["answer"]), subject=test[i]["subject"])
             for i in idx]
    rows = []
    for variant in ("study prompt", "with subject header"):
        seqs = []
        for it in items:
            body = "\n\n".join([BI.mcf_block(s, True) for s in shots[it["subject"]][:5]] + [BI.mcf_block(it, False)])
            if variant != "study prompt":
                body = f"The following are multiple choice questions (with answers) about {it['subject'].replace('_', ' ')}.\n\n" + body
            ids = tok(body).input_ids
            seqs.append(ids[-2040:])
        lp = EV.hidden_at(model, seqs, [[len(s) - 1] for s in seqs], 24000, "cuda")
        for it, l in zip(items, lp):
            rows.append(dict(variant=variant, subject=it["subject"], correct=int(int(l[0, label_ids].argmax()) == it["gold"])))
    d = pd.DataFrame(rows)
    out = d.groupby("variant").agg(micro=("correct", "mean")).join(
        d.groupby(["variant", "subject"]).correct.mean().groupby("variant").mean().rename("macro"))
    out.to_csv(RUN / "results" / "tables" / "validation_mmlu.csv")
    print((out * 100).round(1).to_string())


if __name__ == "__main__":
    main()
