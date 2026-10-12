"""D6 (post hoc): which initialisation did each released training run actually start from? Correlates the weights of
each model at step 1, step 1000 and step 143000 with each available step-0 checkpoint, tensor by tensor, over the 50
weight matrices (embedding, attention, MLP, unembedding). Also the pairwise similarity of the original, the
weight-seed variants and data-seed1 at step 1000 and step 143000. Writes results/tables/lineage_check.csv and
results/tables/lineage_pairwise.csv."""
from pathlib import Path

import pandas as pd
import torch

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
INITS = ["p160m", "p160m-weight-seed1", "p160m-weight-seed2", "p160m-weight-seed3", "p160m-data-seed1"]
MODELS = ["p160m", "p160m-seed1", "p160m-weight-seed1", "p160m-weight-seed2", "p160m-weight-seed3", "p160m-data-seed1"]


def load(d):
    sd = torch.load(d / "pytorch_model.bin", map_location="cpu", weights_only=True)
    return {k.replace("gpt_neox.", ""): v for k, v in sd.items() if k.endswith(".weight") and v.dim() == 2}


def corr(a, b):
    a, b = a.double().flatten(), b.double().flatten()  # float64: float32 sums over 38M entries drift above 1
    a, b = a - a.mean(), b - b.mean()
    return float((a @ b) / (a.norm() * b.norm()))


def main():
    init = {m: load(RAW / "step0" / m) for m in INITS}
    rows = []
    for step, sub in (("step1", "step1"), ("step1000", "step1000"), ("step143000", "models")):
        for m in MODELS:
            d = RAW / sub / m
            if not (d / "pytorch_model.bin").exists():
                continue
            w = load(d)
            for i in INITS:
                cs = [corr(w[k], init[i][k]) for k in w]
                rows.append(dict(model=m, step=step, init=i, tensors=len(cs), median_corr=float(pd.Series(cs).median()),
                                 min_corr=min(cs), max_corr=max(cs)))
    d = pd.DataFrame(rows)
    d.to_csv(RUN / "results" / "tables" / "lineage_check.csv", index=False)
    print(d.pivot_table(index=["step", "model"], columns="init", values="median_corr").round(3).to_string())
    pw, ms = [], [m for m in MODELS if m != "p160m-seed1"]
    for step, sub in (("step1000", "step1000"), ("step143000", "models")):
        w = {m: load(RAW / sub / m) for m in ms}
        for i, a in enumerate(ms):
            for b in ms[i + 1:]:
                cs = [corr(w[a][k], w[b][k]) for k in w[a]]
                pw.append(dict(step=step, a=a, b=b, median_corr=float(pd.Series(cs).median()),
                               identical_tensors=sum(torch.equal(w[a][k], w[b][k]) for k in w[a])))
    pw = pd.DataFrame(pw)
    pw.to_csv(RUN / "results" / "tables" / "lineage_pairwise.csv", index=False)
    print(pw.round(4).to_string())


if __name__ == "__main__":
    main()
