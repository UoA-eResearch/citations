"""Feasibility probe (not an analysis): does AIFS single v1.0 run on the free GPU memory? Random/standard-atmosphere
input, 12-hour forecast."""
import datetime
import time

import numpy as np
import torch
from anemoi.inference.runners.simple import SimpleRunner

PARAM_SFC = {"10u": 0, "10v": 0, "2d": 285, "2t": 290, "msl": 101300, "skt": 290, "sp": 100000, "tcw": 20, "lsm": 0.3,
             "z": 1000, "slor": 0.01, "sdor": 10}
LEVELS = [1000, 925, 850, 700, 600, 500, 400, 300, 250, 200, 150, 100, 50]
N = 542080


def h(level):
    return 44330 * (1 - (level / 1013.25) ** 0.19)


def main():
    rng = np.random.default_rng(0)
    fields = {k: np.full((2, N), float(v)) + rng.normal(0, 0.1, (2, N)) for k, v in PARAM_SFC.items()}
    for p in ("swvl", "stl"):
        for lev in (1, 2):
            fields[f"{p}{lev}"] = np.full((2, N), 0.3 if p == "swvl" else 290.0)
    for lev in LEVELS:
        fields[f"z_{lev}"] = np.full((2, N), 9.80665 * h(lev))
        fields[f"t_{lev}"] = np.full((2, N), 288 - 6.5e-3 * min(h(lev), 11000))
        for p in ("u", "v", "w"):
            fields[f"{p}_{lev}"] = np.zeros((2, N))
        fields[f"q_{lev}"] = np.full((2, N), max(1e-6, 0.01 * (lev / 1000) ** 3))
    state = dict(date=datetime.datetime(2024, 6, 1, 0), fields=fields)
    print("free GPU GiB before", round(torch.cuda.mem_get_info()[0] / 2 ** 30, 1), flush=True)
    runner = SimpleRunner("data/raw/aifs/aifs-single-mse-1.0.ckpt", device="cuda")
    t = time.time()
    for s in runner.run(input_state=state, lead_time=12):
        print("step", s["date"], "fields", len(s["fields"]), "secs", round(time.time() - t, 1),
              "peak GiB", round(torch.cuda.max_memory_allocated() / 2 ** 30, 1), flush=True)


if __name__ == "__main__":
    main()
