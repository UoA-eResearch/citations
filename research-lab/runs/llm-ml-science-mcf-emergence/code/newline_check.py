#!/usr/bin/env python
"""EXPLORATORY check after review (deviations.md D6): OLMo-1B-0724's final checkpoint puts most probability on a newline
after "Answer:". Score its five-shot MCF with the label read after the newline instead ("Answer:\\n" then "A", "B", ...)
on all 3,000 items, to bound whether its at-chance MCF accuracy is a formatting artefact.
Usage: newline_check.py MODEL_DIR  -> results/tables/review_newline_check.csv
"""
import json
import sys
from pathlib import Path

import pandas as pd
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluate as EV  # noqa: E402

RUN = Path(__file__).resolve().parents[1]


def main():
    md = sys.argv[1]
    tok = AutoTokenizer.from_pretrained(md)
    model = AutoModelForCausalLM.from_pretrained(md, dtype=torch.bfloat16, attn_implementation="sdpa").to("cuda").eval()
    rows = []
    for variant, suffix, lab in (("study prompt (' A' after 'Answer:')", "", " "), ("newline then letter", "\n", "")):
        ids = [tok(lab + L, add_special_tokens=False).input_ids for L in "ABCDE"]
        assert all(len(x) == 1 for x in ids), ids
        ids = [x[0] for x in ids]
        items = [json.loads(l) for t in EV.TASKS for l in open(RUN / "data" / "items" / f"{t}.jsonl")]
        seqs = [tok(it["mcf5"] + suffix).input_ids for it in items]
        lp = EV.hidden_at(model, seqs, [[len(s) - 1] for s in seqs], 48000, "cuda")
        for it, l in zip(items, lp):
            v = l[0, ids[:it["n_options"]]]
            rows.append(dict(variant=variant, task=it["task"], correct=int(int(v.argmax()) == it["gold"]),
                             mass=float(v.exp().sum()), chance=1 / it["n_options"]))
    d = pd.DataFrame(rows)
    s = d.groupby(["variant", "task"]).agg(acc=("correct", "mean"), chance=("chance", "mean"), mass=("mass", "mean"))
    s["excess_points"] = (s.acc - s.chance) * 100
    s.to_csv(RUN / "results" / "tables" / "review_newline_check.csv")
    print(s.round(3).to_string())


if __name__ == "__main__":
    main()
