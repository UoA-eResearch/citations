"""Tokenize the Pile (uncopyrighted) val and test splits with the Pythia (GPT-NeoX) tokenizer.

Documents are concatenated with the end-of-text token (id 0) between them and cut into 2,048-token sequences. The
sequence order is shuffled once with a fixed seed. Every SAE in the study is trained on the same sequences in the same
order (sparsify does not shuffle a memmap dataset).

  val  -> data/train_tokens.bin    (uint16; SAE training stream; length set by --train_tokens)
  test -> data/heldout_tokens.bin  (uint16; held-out matching set H; --heldout_seqs sequences)

Usage: tokenize_pile.py <train_tokens> <heldout_seqs>"""
import io
import json
import sys
from pathlib import Path

import numpy as np
import zstandard
from transformers import AutoTokenizer

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
CTX, SEED, EOT = 2048, 20261012, 0


def stream(path, tok, max_tokens):
    """Concatenated token ids of the file's documents, up to max_tokens (None: all)."""
    out, n, batch = [], 0, []
    with open(path, "rb") as fh:
        reader = io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(fh), encoding="utf-8")
        for line in reader:
            batch.append(json.loads(line)["text"])
            if len(batch) == 1000:
                for ids in tok(batch)["input_ids"]:
                    out.append(np.asarray(ids + [EOT], dtype=np.uint16))
                    n += len(ids) + 1
                batch = []
                if max_tokens and n >= max_tokens:
                    break
        if batch and not (max_tokens and n >= max_tokens):
            for ids in tok(batch)["input_ids"]:
                out.append(np.asarray(ids + [EOT], dtype=np.uint16))
                n += len(ids) + 1
    return np.concatenate(out)


def write(arr, n_seq, dst, seed):
    seqs = arr[: (len(arr) // CTX) * CTX].reshape(-1, CTX)
    order = np.random.default_rng(seed).permutation(len(seqs))
    if n_seq > len(seqs):
        raise SystemExit(f"{dst.name}: only {len(seqs)} sequences available, {n_seq} requested")
    seqs[order[:n_seq]].tofile(dst)
    print(f"{dst.name}: {n_seq} sequences x {CTX} = {n_seq * CTX:,} tokens (of {len(seqs):,} available)", flush=True)


def main(train_tokens, heldout_seqs):
    tok = AutoTokenizer.from_pretrained(RAW / "models" / "p160m")
    assert tok.eos_token_id == EOT, tok.eos_token_id
    n_train = -(-train_tokens // CTX)
    tr = stream(RAW / "pile" / "val.jsonl.zst", tok, None)
    write(tr, n_train, RUN / "data" / "train_tokens.bin", SEED)
    te = stream(RAW / "pile" / "test.jsonl.zst", tok, (heldout_seqs + 10) * CTX * 4)
    write(te, heldout_seqs, RUN / "data" / "heldout_tokens.bin", SEED + 1)
    print("TOKENIZE DONE", flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]))
