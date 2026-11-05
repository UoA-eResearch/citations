"""Training tokens (plan section 0): FineWeb-Edu sample-10BT, the first parquet shards in file order, tokenised with
the Qwen3 tokenizer and packed into 1,024-token sequences (documents joined with the EOS token). The first 300M tokens
are for training and the next 1M are held out for fidelity. Sets differ only in how the sequence order is permuted.

  data_prep.py -> data/train_tokens.u32 (N_seq x 1024), data/heldout_tokens.u32, data/tokens.json
"""
import json
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
from huggingface_hub import hf_hub_download
from transformers import AutoTokenizer

RUN = Path(__file__).resolve().parents[1]
D = RUN / "data"
SEQ, N_TRAIN, N_HELD = 1024, 300_000_000, 1_000_000
tok = AutoTokenizer.from_pretrained("Qwen/Qwen3-0.6B")
eos = tok.eos_token_id
need = (N_TRAIN + N_HELD) // SEQ + 1
buf, out, shard = [], [], 0
while sum(len(x) for x in out) < need:
    f = hf_hub_download("HuggingFaceFW/fineweb-edu", f"sample/10BT/{shard:03d}_00000.parquet", repo_type="dataset")
    for batch in pq.ParquetFile(f).iter_batches(columns=["text"], batch_size=2000):
        enc = tok(batch.column("text").to_pylist(), add_special_tokens=False).input_ids
        for ids in enc:
            buf.extend(ids); buf.append(eos)
        n = len(buf) // SEQ
        if n:
            out.append(np.asarray(buf[:n * SEQ], dtype=np.uint32).reshape(n, SEQ)); buf = buf[n * SEQ:]
        if sum(len(x) for x in out) >= need:
            break
    shard += 1
a = np.concatenate(out)[:need]
n_tr = N_TRAIN // SEQ
a[:n_tr].tofile(D / "train_tokens.u32"); a[n_tr:n_tr + N_HELD // SEQ].tofile(D / "heldout_tokens.u32")
(D / "tokens.json").write_text(json.dumps({"seq_len": SEQ, "train_seqs": int(n_tr), "heldout_seqs": int(N_HELD // SEQ), "shards_used": shard}) + "\n")
print("train seqs", n_tr, "held-out seqs", N_HELD // SEQ, "shards", shard)
