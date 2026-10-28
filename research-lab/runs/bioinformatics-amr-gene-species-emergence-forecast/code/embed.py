"""ESM-2 (650M) mean embeddings of the reference protein for each AMR gene symbol (plan section 0, features).

The GPU is shared with a vLLM server. This uses it only if several GB are free, caps its own share, and otherwise
runs on CPU. Sequences are truncated to 1,022 residues (the model's limit with its two special tokens).

  embed.py -> data/gene_embeddings.parquet (gene, embedding), results/tables/embed.json
"""
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from transformers import AutoModel, AutoTokenizer

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
MODEL = "facebook/esm2_t33_650M_UR50D"
MAXLEN = 1022
RESERVE_GB = 6.0


def pick_device():
    if not torch.cuda.is_available():
        return "cpu", None
    free, total = torch.cuda.mem_get_info()
    if free / 1e9 < RESERVE_GB + 1:
        return "cpu", round(free / 1e9, 1)
    torch.cuda.set_per_process_memory_fraction(RESERVE_GB * 1e9 / total)   # never crowd the shared server
    return "cuda", round(free / 1e9, 1)


def main():
    g = pd.read_parquet(D / "gene_proteins.parquet")
    g = g[g.seq.notna()].reset_index(drop=True)
    dev, free = pick_device()
    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModel.from_pretrained(MODEL, torch_dtype=torch.float16 if dev == "cuda" else torch.float32).to(dev).eval()
    order = np.argsort(g.seq.str.len().to_numpy())                         # batch similar lengths together
    embs = np.zeros((len(g), model.config.hidden_size), dtype=np.float32)
    bs = 8 if dev == "cuda" else 4
    with torch.inference_mode():
        for i in range(0, len(order), bs):
            idx = order[i:i + bs]
            seqs = [s[:MAXLEN] for s in g.seq.iloc[idx]]
            enc = tok(seqs, return_tensors="pt", padding=True, truncation=True, max_length=MAXLEN + 2).to(dev)
            h = model(**enc).last_hidden_state.float()
            m = enc["attention_mask"].unsqueeze(-1).float()
            m[:, 0] = 0                                                     # drop the special tokens from the mean
            for k, j in enumerate(idx):
                n = int(enc["attention_mask"][k].sum()) - 1
                m[k, n:] = 0
            embs[idx] = ((h * m).sum(1) / m.sum(1).clamp(min=1)).cpu().numpy()
            if i % (bs * 200) == 0:
                print(i, "/", len(order), flush=True)
    out = pd.DataFrame({"gene": g.gene, "embedding": list(embs)})
    out.to_parquet(D / "gene_embeddings.parquet")
    stats = {"model": MODEL, "device": dev, "gpu_free_gb_at_start": free, "genes": len(out),
             "dim": int(embs.shape[1]), "truncated": int((g.seq.str.len() > MAXLEN).sum())}
    (T / "embed.json").write_text(json.dumps(stats, indent=1) + "\n")
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main()
