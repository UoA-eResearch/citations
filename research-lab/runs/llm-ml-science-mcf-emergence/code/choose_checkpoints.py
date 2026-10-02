#!/usr/bin/env python
"""Checkpoint list (plan.md sec 2), fixed by formula before any evaluation.

Pythia runs: 16 targets log-spaced in step from 512 to 143,000, each mapped to the nearest available branch.
OLMo runs: 20 targets log-spaced in tokens from 4B to the last stage-1 (or only-stage) branch, nearest available branch.
Output: data/checkpoints.csv (group, run, repo, revision, step, tokens, dtype)
"""
import json
import re
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
PYTHIA_TOK_PER_STEP = 2_097_152
RUNS = (
    [("pythia_scale", f"EleutherAI/pythia-{s}") for s in ("1b", "1.4b", "2.8b", "6.9b")]
    + [("polypythia_410m", "EleutherAI/pythia-410m")] + [("polypythia_410m", f"EleutherAI/pythia-410m-seed{i}") for i in range(1, 10)]
    + [("olmo2", "allenai/OLMo-2-0425-1B"), ("olmo2", "allenai/OLMo-2-1124-7B")]
    + [("floor_160m", "EleutherAI/pythia-160m")] + [("floor_160m", f"EleutherAI/pythia-160m-seed{i}") for i in range(1, 10)]
    + [("added_olmo", "allenai/OLMo-7B-0424-hf"), ("added_olmo", "allenai/OLMo-1B-0724-hf")]
)


def branches(repo):
    d = json.load(urllib.request.urlopen(f"https://huggingface.co/api/models/{repo}/refs", timeout=120))
    return [b["name"] for b in d["branches"]]


def nearest(avail, targets):
    out = []
    for t in targets:
        j = int(np.argmin(np.abs(np.log(avail) - np.log(t))))
        if avail[j] not in out:
            out.append(avail[j])
    return out


def main():
    rows = []
    for group, repo in RUNS:
        b = branches(repo)
        if repo.startswith("EleutherAI"):
            steps = sorted(int(x[4:]) for x in b if re.fullmatch(r"step\d+", x) and int(x[4:]) > 0)
            chosen = nearest(np.array(steps, float), np.geomspace(512, 143000, 16))
            for s in chosen:
                rows.append(dict(group=group, run=repo.split("/")[1], repo=repo, revision=f"step{int(s)}", step=int(s),
                                 tokens=int(s) * PYTHIA_TOK_PER_STEP, dtype="float16"))
        else:
            cand = {}
            for x in b:
                m = re.fullmatch(r"(?:stage1-)?step(\d+)-tokens(\d+)B", x)
                if m and int(m.group(2)) > 0:
                    cand.setdefault(int(m.group(2)), (x, int(m.group(1))))
            toks = np.array(sorted(cand), float)
            chosen = nearest(toks, np.geomspace(4, toks.max(), 20))
            for t in chosen:
                name, step = cand[int(t)]
                rows.append(dict(group=group, run=repo.split("/")[1], repo=repo, revision=name, step=step,
                                 tokens=int(t) * 10**9, dtype="bfloat16"))
    df = pd.DataFrame(rows)
    df.to_csv(RUN / "data" / "checkpoints.csv", index=False)
    print(df.groupby("run", sort=False).agg(n=("revision", "size"), first=("revision", "first"), last=("revision", "last")).to_string())
    print("total checkpoints:", len(df))


if __name__ == "__main__":
    main()
