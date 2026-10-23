"""Eval corpus and checkpoint losses (plan section 1).

  evaluate.py corpus     val.jsonl.zst -> data/eval_tokens.npy (5,000,000 tokens in 2,048-token sequences) + sha256,
                         data/eval_docs.npy (document id of each sequence)
  evaluate.py run        every (size, seed, step) in the plan + the 1B/1.4B/2.8B targets -> results/tables/losses.csv
                         (resumable; each checkpoint is deleted from the cache after use)
  evaluate.py evalnoise  document bootstrap of the 410M seed-0 final loss -> results/tables/eval_noise.json
"""
import hashlib
import io
import json
import os
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
DATA = RUN / "data"
T = RUN / "results" / "tables"
os.environ.setdefault("HF_HOME", str(DATA / "hf"))
SIZES = ["14m", "31m", "70m", "160m", "410m"]
SEEDS = list(range(10))
STEPS = [2000, 4000, 8000, 16000, 32000, 64000, 100000, 143000]
TARGETS = ["1b", "1.4b", "2.8b"]
NTOK, SEQ = 5_000_000, 2048
TOKENS_PER_STEP = 2_097_152


def repo(size, seed):
    return f"EleutherAI/pythia-{size}" if seed == 0 else f"EleutherAI/pythia-{size}-seed{seed}"


def corpus():
    import zstandard
    from huggingface_hub import hf_hub_download
    from transformers import AutoTokenizer
    p = hf_hub_download("monology/pile-uncopyrighted", "val.jsonl.zst", repo_type="dataset",
                        token=open(os.path.expanduser("~/.config/hf/token")).read().strip())
    tok = AutoTokenizer.from_pretrained("EleutherAI/pythia-410m")
    ids, docs = [], []
    with open(p, "rb") as fh:
        stream = io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(fh), encoding="utf-8")
        for d, line in enumerate(stream):
            t = tok(json.loads(line)["text"]).input_ids + [tok.eos_token_id]
            ids += t
            docs += [d] * len(t)
            if len(ids) >= NTOK:
                break
    n = (NTOK // SEQ) * SEQ
    a = np.array(ids[:n], dtype=np.int32).reshape(-1, SEQ)
    dd = np.array(docs[:n], dtype=np.int32).reshape(-1, SEQ)[:, 0]
    np.save(DATA / "eval_tokens.npy", a)
    np.save(DATA / "eval_docs.npy", dd)
    h = hashlib.sha256(a.tobytes()).hexdigest()
    (T / "eval_corpus.json").write_text(json.dumps({"sequences": int(a.shape[0]), "tokens": int(a.size),
                                                    "documents": int(dd.max() + 1), "sha256": h}, indent=1))
    print(a.shape, h)


def seq_losses(model_id, revision, toks, bs):
    import torch
    from transformers import AutoModelForCausalLM
    m = AutoModelForCausalLM.from_pretrained(model_id, revision=revision, torch_dtype=torch.bfloat16).cuda().eval()
    n_params = sum(p.numel() for n, p in m.named_parameters() if "embed" not in n)
    out = []
    with torch.no_grad():
        for i in range(0, len(toks), bs):
            x = torch.from_numpy(toks[i:i + bs]).long().cuda()
            logits = m(x).logits.float()
            lp = torch.nn.functional.cross_entropy(logits[:, :-1].reshape(-1, logits.size(-1)), x[:, 1:].reshape(-1),
                                                   reduction="none").view(x.size(0), -1)
            out.append(lp.mean(1).cpu().numpy())
    del m
    torch.cuda.empty_cache()
    return np.concatenate(out), n_params


def clear_cache():
    hub = DATA / "hf" / "hub"
    for d in hub.glob("models--EleutherAI--pythia-*"):
        shutil.rmtree(d, ignore_errors=True)


def run():
    toks = np.load(DATA / "eval_tokens.npy")
    out = T / "losses.csv"
    done = set()
    if out.exists():
        d = pd.read_csv(out)
        done = set(zip(d.model, d.step))
    jobs = [(repo(s, sd), s, sd, st) for s in SIZES for sd in SEEDS for st in STEPS]
    jobs += [(f"EleutherAI/pythia-{t}", t, 0, 143000) for t in TARGETS]
    bs = {"14m": 32, "31m": 32, "70m": 16, "160m": 16, "410m": 8, "1b": 4, "1.4b": 2, "2.8b": 1}
    for model_id, size, seed, step in jobs:
        if (model_id, step) in done:
            continue
        t0 = time.time()
        for k in range(5):
            try:
                ls, n = seq_losses(model_id, f"step{step}", toks, bs[size])
                break
            except Exception as ex:
                print("retry", model_id, step, str(ex)[:200], flush=True)
                time.sleep(30 * (k + 1))
        else:
            raise RuntimeError(f"{model_id} step{step} failed")
        np.save(DATA / "seqloss" / f"{model_id.split('/')[1]}_step{step}.npy", ls) if (DATA / "seqloss").exists() else None
        row = pd.DataFrame([{"model": model_id, "size": size, "seed": seed, "step": step, "N": n,
                             "D": step * TOKENS_PER_STEP, "loss": float(ls.mean())}])
        row.to_csv(out, mode="a", header=not out.exists(), index=False)
        clear_cache()
        print(model_id, step, round(float(ls.mean()), 4), round(time.time() - t0), "s", flush=True)


def evalnoise():
    ls = np.load(DATA / "seqloss" / "pythia-410m_step143000.npy")
    docs = np.load(DATA / "eval_docs.npy")
    ud = np.unique(docs)
    rng = np.random.default_rng(20261024)
    per = pd.Series(ls).groupby(docs).agg(["sum", "count"])
    bs = []
    for _ in range(200):
        pick = rng.choice(ud, len(ud))
        sub = per.loc[pick]
        bs.append(sub["sum"].sum() / sub["count"].sum())
    out = {"loss": float(ls.mean()), "doc_bootstrap_sd": float(np.std(bs)), "documents": int(len(ud))}
    (T / "eval_noise.json").write_text(json.dumps(out, indent=1))
    print(out)


if __name__ == "__main__":
    (DATA / "seqloss").mkdir(parents=True, exist_ok=True)
    {"corpus": corpus, "run": run, "evalnoise": evalnoise}[sys.argv[1]]()
