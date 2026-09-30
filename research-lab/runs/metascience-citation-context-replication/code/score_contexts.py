#!/usr/bin/env python
"""Score every harvested context with C1 (fine-tuned SciBERT, GPU) and C2 (local LLM via the vLLM OpenAI API,
zero-shot, temperature 0, 8 concurrent requests) on the validation pool, and on capped analysis contexts only if it
becomes the primary classifier (deviations.md D3).
Resumable: C2 answers are cached by text hash.
Usage: score_contexts.py [c1|c2|both] [pool|analysis]
Output: data/processed/scores_c1.parquet, data/processed/scores_c2_{pool,analysis}.parquet
"""
import hashlib
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import requests

RUN = Path(__file__).resolve().parents[1]
PROC = RUN / "data" / "processed"
PROMPT = ("You classify citation contexts from scientific papers. Does this citation context express doubt about the reliability, "
          "replicability or validity of the cited work's findings (for example failed replications, contradictory results, "
          "methodological criticism)? Answer with exactly one word: NEGATIVE, POSITIVE (explicit confirmation or successful "
          "replication of the cited finding), or NEUTRAL.\n\nCitation context: \"{c}\"\n\nAnswer:")


def c1(ctx):
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from train_c1 import LABELS, predict
    path = PROC / "c1_scibert"
    tok = AutoTokenizer.from_pretrained(path)
    model = AutoModelForSequenceClassification.from_pretrained(path).cuda()
    texts = ctx.text.astype(str).tolist()
    p = predict(model, tok, texts, bs=128)
    out = pd.DataFrame(p, columns=[f"p_{l.lower()}" for l in LABELS])
    out.insert(0, "ctx_id", ctx.ctx_id.values)
    out["label"] = np.array(LABELS)[p.argmax(1)]
    out.to_parquet(PROC / "scores_c1.parquet", index=False)
    print("C1", out.label.value_counts().to_dict())
    del model
    torch.cuda.empty_cache()


def ask(text):
    for attempt in range(5):
        try:
            r = requests.post("http://localhost:8000/v1/chat/completions", timeout=120, json={
                "model": "nemotron_3_nano_omni", "temperature": 0, "max_tokens": 8,
                "chat_template_kwargs": {"enable_thinking": False},
                "messages": [{"role": "user", "content": PROMPT.format(c=text[:2000])}]})
            ans = (r.json()["choices"][0]["message"].get("content") or "").strip().upper()
            for lab in ("NEGATIVE", "POSITIVE", "NEUTRAL"):
                if lab in ans:
                    return lab.title()
            return "Unparsed"
        except Exception:                                                # noqa: BLE001
            continue
    return "Error"


def windows():
    f = pd.read_csv(RUN / "data" / "raw" / "flora_filtered.csv", low_memory=False)
    f = f[(f.type == "replication") & f.doi_o.notna()].assign(doi_o=lambda d: d.doi_o.str.strip().str.lower())
    return f.groupby("doi_o").agg(yr1=("year_r", "min"), year_o=("year_o", "min"))


def c2_selection(ctx, pre_cap=100, post_cap=50):
    """deviations.md D3: if C2 becomes the primary classifier, it scores the contexts of analysis citing papers only.
    Per original (first replication year from FLoRA; no outcome used): pre-replication citing papers (year_o <= year <
    first year), a random pre_cap if more; post-replication citing papers (year >= first year + 1), a random post_cap.
    The random draw is seeded per original, so it does not depend on harvest order."""
    papers = ctx.groupby(["doi_o", "citing_id"]).year.first().reset_index().merge(windows(), left_on="doi_o", right_index=True)
    keep = []
    for doi, p in papers.groupby("doi_o"):
        rng = np.random.default_rng(int(hashlib.sha1(doi.encode()).hexdigest()[:8], 16))
        pre = p[(p.year >= p.year_o) & (p.year < p.yr1)].sort_values("citing_id")
        post = p[p.year >= p.yr1 + 1].sort_values("citing_id")
        for part, cap in ((pre, pre_cap), (post, post_cap)):
            if len(part) > cap:
                part = part.iloc[np.sort(rng.choice(len(part), cap, replace=False))]
            keep.append(part[["doi_o", "citing_id"]])
    sel = pd.concat(keep).drop_duplicates()
    return ctx.merge(sel, on=["doi_o", "citing_id"])


def validation_pool(ctx, n_pre=15000, n_post=5000):
    """deviations.md D3: the pool from which the validation sample is drawn (C2 scores it first): random contexts from
    pre-replication (n_pre) and post-replication (n_post) citing papers, seed 5."""
    c = ctx.merge(windows(), left_on="doi_o", right_index=True)
    pre = c[(c.year >= c.year_o) & (c.year < c.yr1)]
    post = c[c.year >= c.yr1 + 1]
    return pd.concat([pre.sample(min(n_pre, len(pre)), random_state=5), post.sample(min(n_post, len(post)), random_state=5)])


def c2(ctx, scope="pool"):
    ctx = validation_pool(ctx) if scope == "pool" else c2_selection(ctx)
    cache_path = PROC / "c2_cache.jsonl"
    cache = {}
    if cache_path.exists():
        for line in cache_path.read_text().splitlines():
            h, lab = json.loads(line)
            cache[h] = lab
    texts = ctx.text.astype(str)
    hashes = texts.map(lambda t: hashlib.sha1(t.encode()).hexdigest())
    todo = sorted(set(hashes) - set(cache))
    by_hash = dict(zip(hashes, texts))
    print("C2 to score", len(todo), "of", hashes.nunique(), flush=True)
    with open(cache_path, "a") as fh, ThreadPoolExecutor(8) as ex:
        for n, (h, lab) in enumerate(zip(todo, ex.map(lambda h: ask(by_hash[h]), todo))):
            cache[h] = lab
            fh.write(json.dumps([h, lab]) + "\n")
            if n % 5000 == 0:
                fh.flush()
                print("  scored", n, flush=True)
    out = pd.DataFrame(dict(ctx_id=ctx.ctx_id.values, label=hashes.map(cache).values))
    out.to_parquet(PROC / f"scores_c2_{scope}.parquet", index=False)
    print("C2", out.label.value_counts().to_dict())


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    ctx = pd.read_parquet(PROC / "contexts.parquet")
    if which in ("c1", "both"):
        c1(ctx)
    if which in ("c2", "both"):
        c2(ctx, sys.argv[2] if len(sys.argv) > 2 else "pool")


if __name__ == "__main__":
    sys.exit(main())
