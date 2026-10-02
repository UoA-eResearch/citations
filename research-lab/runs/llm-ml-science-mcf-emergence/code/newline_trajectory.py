#!/usr/bin/env python
"""EXPLORATORY (deviations.md D6, E5): OLMo-1B-0724's whole trajectory scored with the letter read after a newline
("Answer:\\n" then "A", "B", ...), five-shot MCF on all 3,000 items, because its final checkpoint prefers a newline
after "Answer:". Downloads each planned checkpoint, scores, deletes.
Usage: newline_trajectory.py  -> results/evals_newline/OLMo-1B-0724-hf/{revision}.parquet
"""
import json
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluate as EV  # noqa: E402
import pipeline as P  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
NAME = "OLMo-1B-0724-hf"


def score(md, rev, dest):
    tok = AutoTokenizer.from_pretrained(md)
    model = AutoModelForCausalLM.from_pretrained(md, dtype=torch.bfloat16, attn_implementation="sdpa").to("cuda").eval()
    ids = [tok(L, add_special_tokens=False).input_ids[0] for L in "ABCDE"]
    items = [json.loads(l) for t in EV.TASKS for l in open(RUN / "data" / "items" / f"{t}.jsonl")]
    seqs = [tok(it["mcf5"] + "\n").input_ids for it in items]
    lp = EV.hidden_at(model, seqs, [[len(s) - 1] for s in seqs], 48000, "cuda")
    rows = [dict(task=it["task"], id=it["id"], fmt="mcf5_newline", n_options=it["n_options"],
                 correct=int(int(l[0, ids[:it["n_options"]]].argmax()) == it["gold"]),
                 mass=float(l[0, ids[:it["n_options"]]].exp().sum())) for it, l in zip(items, lp)]
    pd.DataFrame(rows).to_parquet(dest, index=False)
    del model
    torch.cuda.empty_cache()


def main():
    ck = pd.read_csv(RUN / "data" / "checkpoints.csv")
    ck = ck[ck.run == NAME].to_dict("records")
    out = RUN / "results" / "evals_newline" / NAME
    out.mkdir(parents=True, exist_ok=True)
    todo = [r for r in ck if not (out / f"{r['revision']}.parquet").exists()]
    store = RUN / "data" / "ckpt" / "newline"
    with ThreadPoolExecutor(2) as ex:
        futs = {}
        for i in range(min(2, len(todo))):
            futs[i] = ex.submit(P.download, todo[i]["repo"], todo[i]["revision"], store / todo[i]["revision"])
        for i, r in enumerate(todo):
            d = futs.pop(i).result()
            if i + 2 < len(todo):
                futs[i + 2] = ex.submit(P.download, todo[i + 2]["repo"], todo[i + 2]["revision"], store / todo[i + 2]["revision"])
            score(d, r["revision"], out / f"{r['revision']}.parquet")
            shutil.rmtree(d, ignore_errors=True)
            print("done", r["revision"], flush=True)


if __name__ == "__main__":
    main()
