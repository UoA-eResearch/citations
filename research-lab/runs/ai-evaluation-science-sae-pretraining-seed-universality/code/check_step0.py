"""Plan section 2 / 9.3: which initialisations are shared? Compares the step-0 checkpoint of each decoupled variant with
the original's (tensor by tensor), and checks that all 16 tokenizers are equivalent (same vocabulary and ids). Writes results/tables/step0_check.csv."""
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from transformers import AutoTokenizer

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
VARIANTS = [f"p160m-weight-seed{i}" for i in range(1, 4)] + [f"p160m-data-seed{i}" for i in range(1, 4)]


def load(d):
    return torch.load(d / "pytorch_model.bin", map_location="cpu", weights_only=True)


def main():
    ref = load(RAW / "step0" / "p160m")
    rows = []
    for v in VARIANTS:
        sd = load(RAW / "step0" / v)
        keys = sorted(set(ref) & set(sd))
        same = [k for k in keys if ref[k].shape == sd[k].shape and torch.equal(ref[k], sd[k])]
        maxdiff = max(float((ref[k].float() - sd[k].float()).abs().max()) for k in keys if ref[k].shape == sd[k].shape)
        rows.append(dict(variant=v, tensors=len(keys), identical_tensors=len(same), all_identical=len(same) == len(keys),
                         max_abs_diff=maxdiff, keys_only_in_one=len(set(ref) ^ set(sd))))
    # tokenizers: the training stream and H were tokenized once with the original's tokenizer, so every model's
    # tokenizer must have the same vocabulary and give the same ids (the tokenizer.json files differ in serialisation)
    base = AutoTokenizer.from_pretrained(RAW / "models" / "p160m")
    text = base.decode(np.fromfile(RUN / "data" / "train_tokens.bin", dtype=np.uint16, count=20000))
    same = [AutoTokenizer.from_pretrained(m).get_vocab() == base.get_vocab()
            and AutoTokenizer.from_pretrained(m)(text)["input_ids"] == base(text)["input_ids"]
            for m in sorted((RAW / "models").iterdir())]
    d = pd.DataFrame(rows)
    d["tokenizers_equivalent_all_16"] = all(same)
    (RUN / "results" / "tables").mkdir(parents=True, exist_ok=True)
    d.to_csv(RUN / "results" / "tables" / "step0_check.csv", index=False)
    print(d.to_string())


if __name__ == "__main__":
    main()
