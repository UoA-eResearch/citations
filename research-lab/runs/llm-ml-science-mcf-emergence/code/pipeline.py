#!/usr/bin/env python
"""Download -> evaluate -> delete, for a list of checkpoints (plan.md sec 2-3).

Checkpoints are prefetched in parallel (each download itself uses several connections) and evaluated one at a time on
the GPU, each in a fresh subprocess. Weights are deleted after a successful evaluation. At most PREFETCH downloads are
outstanding beyond the checkpoint being evaluated, and no download starts while free disk is below MIN_FREE_GB
(deviations.md D3). Rerunnable: evaluated checkpoints are skipped.

Usage: pipeline.py --size big|small|all [--prefetch 3] [--only RUN:REVISION,...]
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
from huggingface_hub import HfApi, snapshot_download

RUN = Path(__file__).resolve().parents[1]
BIG = {"pythia-6.9b", "OLMo-2-1124-7B", "OLMo-7B-0424-hf"}
MIN_FREE_GB = 150


def wait_for_disk():
    while shutil.disk_usage(RUN).free < MIN_FREE_GB * 1e9:
        print(f"disk below {MIN_FREE_GB} GB free; waiting", flush=True)
        time.sleep(120)


def overrides():
    """Explicit weight files for branches that hold a stale duplicate (deviations.md D5)."""
    p = RUN / "data" / "weight_overrides.csv"
    if not p.exists():
        return {}
    o = pd.read_csv(p)
    return {(r.run, r.revision): r.patterns.split(";") for r in o.itertuples()}


def download(repo, revision, dest, weights=None):
    wait_for_disk()
    files = HfApi().list_repo_files(repo, revision=revision)
    if weights is None:
        weights = ["*.safetensors", "*.safetensors.index.json"] if any(f.endswith(".safetensors") for f in files) \
            else ["*.bin", "*.bin.index.json"]
    for attempt in range(5):
        try:
            snapshot_download(repo, revision=revision, local_dir=dest, max_workers=8,
                              allow_patterns=weights + ["config.json", "generation_config.json", "tokenizer*",
                                                        "special_tokens_map.json", "vocab.json", "merges.txt"])
            return dest
        except Exception as e:                                            # transient network errors
            print(f"download retry {attempt + 1} {repo}@{revision}: {str(e)[:120]}", flush=True)
            time.sleep(30 * (attempt + 1))
    raise RuntimeError(f"download failed {repo}@{revision}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", default="all", choices=["big", "small", "all"])
    ap.add_argument("--prefetch", type=int, default=3)
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    ck = pd.read_csv(RUN / "data" / "checkpoints.csv")
    if a.only:
        want = [tuple(x.split(":", 1)) for x in a.only.split(",")]
        extra = []
        for run, rev in want:
            m = ck[(ck.run == run) & (ck.revision == rev)]
            if len(m):
                extra.append(m.iloc[0].to_dict())
            else:                                                         # e.g. validation checkpoints not in the list
                base = ck[ck.run == run].iloc[0].to_dict()
                extra.append(dict(base, revision=rev))
        ck = pd.DataFrame(extra)
    elif a.size != "all":
        ck = ck[ck.run.isin(BIG) == (a.size == "big")]
    todo = [r for r in ck.to_dict("records")
            if not (RUN / "results" / "evals" / r["run"] / f"{r['revision']}.parquet").exists()]
    print(f"{len(todo)} checkpoints to evaluate", flush=True)
    store = RUN / "data" / "ckpt"
    ov = overrides()
    with ThreadPoolExecutor(a.prefetch) as ex:
        futs = {}

        def submit(i):
            r = todo[i]
            futs[i] = ex.submit(download, r["repo"], r["revision"], store / r["run"] / r["revision"],
                                ov.get((r["run"], r["revision"])))

        for i in range(min(a.prefetch, len(todo))):
            submit(i)
        for i, r in enumerate(todo):
            f = futs.pop(i)
            try:
                d = f.result()
            except Exception as e:
                print(f"SKIP {r['run']} {r['revision']}: {e}", flush=True)
                continue
            finally:
                if i + a.prefetch < len(todo):                           # bounded: the backlog never exceeds PREFETCH
                    submit(i + a.prefetch)
            p = subprocess.run([sys.executable, str(RUN / "code" / "evaluate.py"), str(d), r["run"], r["revision"],
                                r["dtype"]], capture_output=True, text=True)
            print(p.stdout.strip() or f"EVAL FAILED {r['run']} {r['revision']}: {p.stderr.strip()[-400:]}", flush=True)
            if p.returncode == 0:
                shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    main()
