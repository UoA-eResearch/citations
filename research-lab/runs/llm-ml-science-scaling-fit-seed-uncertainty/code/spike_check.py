"""Post hoc (after fit.py): are the late-checkpoint loss jumps in a few runs real checkpoint properties or evaluation
artefacts? Evaluates neighbouring checkpoints of the outlier runs, a control seed, and the 410M seed-4 final checkpoint
again at batch size 1 -> results/tables/spike_check.csv"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluate as ev  # noqa: E402

JOBS = [("410m", 4, 142000, 2), ("410m", 4, 141000, 2), ("410m", 4, 143000, 1), ("410m", 3, 99000, 2), ("410m", 3, 101000, 2),
        ("410m", 3, 142000, 2), ("410m", 0, 142000, 2), ("14m", 4, 142000, 4), ("14m", 4, 100000, 4), ("31m", 5, 142000, 4),
        ("31m", 5, 100000, 4), ("14m", 0, 142000, 4)]

if __name__ == "__main__":
    toks = np.load(ev.DATA / "eval_tokens.npy")
    out = []
    for size, seed, step, bs in JOBS:
        mid = ev.repo(size, seed)
        l, _ = ev.seq_losses(mid, f"step{step}", toks, bs)
        out.append({"size": size, "seed": seed, "step": step, "batch": bs, "loss": float(l.mean())})
        print(out[-1], flush=True)
        ev.clear_cache()
    pd.DataFrame(out).to_csv(ev.T / "spike_check.csv", index=False)
