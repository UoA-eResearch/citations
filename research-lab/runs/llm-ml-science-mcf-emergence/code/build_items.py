#!/usr/bin/env python
"""Fixed item sets and prompts (plan.md sec 3).

Per task: 500 MCF items and the first 200 of them for CF (seed 0), plus 5 fixed shots from the training/dev split
(MMLU: the 5 dev items of the test item's subject).
Output: data/items/{task}.jsonl, one record per item: id, task, n_options, gold (index), mcf5 (five-shot prompt ending in
"Answer:"), mcf0 (zero-shot prompt), cf_context (five-shot cloze context ending in "Answer:"), options (list), cf (bool)
"""
import json
import random
from pathlib import Path

from datasets import load_dataset
from transformers import AutoTokenizer

RUN = Path(__file__).resolve().parents[1]
LETTERS = "ABCDE"
N_MCF, N_CF, SEED = 500, 200, 0
MAX_TOK = 1900                                 # all models have >= 2048 context (deviations.md D1)
TOKS = [AutoTokenizer.from_pretrained(m) for m in ("EleutherAI/pythia-160m", "allenai/OLMo-2-0425-1B")]


def ntok(s):
    return max(len(t(s).input_ids) for t in TOKS)


def arc(cfg):
    def conv(x):
        labels = x["choices"]["label"]
        return dict(q=x["question"], options=x["choices"]["text"], gold=labels.index(x["answerKey"]))
    return ("allenai/ai2_arc", cfg, "test", "train", conv)


def csqa():
    def conv(x):
        return dict(q=x["question"], options=x["choices"]["text"], gold=x["choices"]["label"].index(x["answerKey"]))
    return ("tau/commonsense_qa", None, "validation", "train", conv)


def piqa():
    def conv(x):
        return dict(q=x["goal"], options=[x["sol1"], x["sol2"]], gold=int(x["label"]))
    return ("baber/piqa", None, "validation", "train", conv)


def hellaswag():
    def conv(x):
        return dict(q=x["ctx"], options=list(x["endings"]), gold=int(x["label"]))
    return ("Rowan/hellaswag", None, "validation", "train", conv)


TASKS = {"arc_easy": arc("ARC-Easy"), "arc_challenge": arc("ARC-Challenge"), "csqa": csqa(), "piqa": piqa(),
         "hellaswag": hellaswag()}


def mcf_block(it, with_answer):
    s = f"Question: {it['q']}\n" + "".join(f" {LETTERS[i]}. {o}\n" for i, o in enumerate(it["options"])) + "Answer:"
    return s + (f" {LETTERS[it['gold']]}" if with_answer else "")


def cf_block(it, with_answer):
    s = f"Question: {it['q']}\nAnswer:"
    return s + (f" {it['options'][it['gold']]}" if with_answer else "")


def records(task, items, shots_for):
    out = []
    for i, it in enumerate(items):
        shots = shots_for(it)
        k = len(shots)                                                   # drop the earliest shots until the prompt fits
        while k > 0 and ntok("\n\n".join([mcf_block(s, True) for s in shots[len(shots) - k:]] + [mcf_block(it, False)])) > MAX_TOK:
            k -= 1
        kc = len(shots)
        longest = max(it["options"], key=len)
        while kc > 0 and ntok("\n\n".join([cf_block(s, True) for s in shots[len(shots) - kc:]] + [cf_block(it, False)]) + " " + longest) > MAX_TOK:
            kc -= 1
        sm, sc = shots[len(shots) - k:], shots[len(shots) - kc:]
        out.append(dict(id=f"{task}-{i}", task=task, n_options=len(it["options"]), gold=it["gold"], options=it["options"],
                        mcf5="\n\n".join([mcf_block(s, True) for s in sm] + [mcf_block(it, False)]),
                        mcf0=mcf_block(it, False),
                        cf_context="\n\n".join([cf_block(s, True) for s in sc] + [cf_block(it, False)]),
                        shots_mcf=k, shots_cf=kc, cf=i < N_CF))
    return out


def main():
    out = RUN / "data" / "items"
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    for task, (repo, cfg, split, shot_split, conv) in TASKS.items():
        ev = [conv(x) for x in load_dataset(repo, cfg, split=split)]
        ev = [x for x in ev if len(x["options"]) <= 5]
        tr = [conv(x) for x in load_dataset(repo, cfg, split=shot_split)]
        tr = [x for x in tr if len(x["options"]) == max(len(e["options"]) for e in ev[:50])]
        shots = rng.sample(tr, 5)
        items = rng.sample(ev, N_MCF)
        recs = records(task, items, lambda it: shots)
        (out / f"{task}.jsonl").write_text("\n".join(json.dumps(r) for r in recs) + "\n")
        print(task, len(recs), "items; options", sorted({r["n_options"] for r in recs}))
    # MMLU: pooled test items, subject-specific dev shots
    test = load_dataset("cais/mmlu", "all", split="test")
    dev = load_dataset("cais/mmlu", "all", split="dev")
    by_subj = {}
    for x in dev:
        by_subj.setdefault(x["subject"], []).append(dict(q=x["question"], options=x["choices"], gold=int(x["answer"])))
    idx = rng.sample(range(len(test)), N_MCF)
    items = [dict(q=test[i]["question"], options=test[i]["choices"], gold=int(test[i]["answer"]), subject=test[i]["subject"])
             for i in idx]
    recs = records("mmlu", items, lambda it: by_subj[it["subject"]][:5])
    (out / "mmlu.jsonl").write_text("\n".join(json.dumps(r) for r in recs) + "\n")
    print("mmlu", len(recs), "items")


if __name__ == "__main__":
    main()
