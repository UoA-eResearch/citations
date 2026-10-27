"""Foundation-model embeddings (plan section 4). Runs inside the pcba-embed:1 image, offline, without credentials:

  docker run --rm --network none --user UID:GID -e HOME=/tmp -e USER=pcba -e LOGNAME=pcba -e HF_HOME=/models \
      -e HF_MODULES_CACHE=/tmp/hfmod -e HF_HUB_OFFLINE=1 -v data/models:/models:ro -v data:/data -v code:/code:ro \
      pcba-embed:3 python /code/embed.py MODEL /data/smiles_unique.parquet /data/emb_<name>.npy THREADS
(image: torch 2.10.0 CPU, transformers 5.16.1 - the MoLFormer snapshot's code needs transformers 5)

Mean-pooled last hidden layer over non-padding tokens; float32; rows in the input order.
Checkpoints: DeepChem/ChemBERTa-77M-MLM @ ed8a537, ibm/MoLFormer-XL-both-10pct @ 361063d.
"""
import sys
import time

import numpy as np
import pandas as pd
import torch
from transformers import AutoModel, AutoTokenizer

model_id, inp, out, threads = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
torch.set_num_threads(threads)
remote = "MoLFormer" in model_id                     # MoLFormer ships its own modelling code
tok = AutoTokenizer.from_pretrained(model_id, trust_remote_code=remote)
kw = {"deterministic_eval": True} if remote else {}
model = AutoModel.from_pretrained(model_id, trust_remote_code=remote, **kw).eval()
smiles = pd.read_parquet(inp).smiles.tolist()
embs, t0, B = [], time.time(), 128
with torch.inference_mode():
    for i in range(0, len(smiles), B):
        enc = tok(smiles[i:i + B], padding=True, truncation=True, max_length=200, return_tensors="pt")
        h = model(**enc).last_hidden_state
        m = enc["attention_mask"].unsqueeze(-1).float()
        embs.append(((h * m).sum(1) / m.sum(1)).numpy().astype(np.float32))
        if (i // B) % 200 == 0:
            print(f"{i + B}/{len(smiles)} {time.time() - t0:.0f}s", flush=True)
np.save(out, np.concatenate(embs))
print("== done", len(smiles), f"{time.time() - t0:.0f}s", flush=True)
