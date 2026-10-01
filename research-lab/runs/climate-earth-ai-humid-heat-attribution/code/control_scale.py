#!/usr/bin/env python
"""Linearity control (deviations.md D4; requested by the independent review). If the attributable change is a real
response to the imposed warming signal, flipping the signal's sign (scale = -1: warming ADDED) should flip the change in
event-peak TW, and halving it (scale = 0.5) should roughly halve it. If instead any perturbation of the initial state
lowers the forecast peak (an off-manifold 'perturbation penalty'), the change keeps its sign.
Events E1 (Persian Gulf) and E5 (US Gulf coast), lead 2 days, all six CMIP6 signals, worlds A and B, scales -1 and 0.5.
Output: data/processed/forecasts/{event}_L2_{world}_{model}_s{scale}.npz
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from perturb import counterfactual, deltas_to_n320  # noqa: E402
from run_forecasts import region_mask, run_one, save  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
PROC, TAB = RUN / "data" / "processed", RUN / "results" / "tables"
OUT = PROC / "forecasts"


def main():
    from anemoi.inference.runners.simple import SimpleRunner
    ev = pd.read_csv(TAB / "events.csv", parse_dates=["date"]).set_index("event_id")
    models = sorted(pd.read_csv(TAB / "cmip6_models.csv").model.unique())
    ll = np.load(PROC / "n320_latlon.npz")
    lat, lon = ll["lat"], ll["lon"]
    coslat = np.cos(np.radians(lat))
    runner = SimpleRunner(str(RUN / "data" / "raw" / "aifs" / "aifs-single-mse-1.0.ckpt"), device="cuda")
    t_start = time.time()
    for eid in ("E1", "E5"):
        e = ev.loc[eid]
        mask = region_mask(lat, lon, e.region)
        z = np.load(PROC / "ic" / f"{eid}_L2.npz")
        t0 = pd.Timestamp(str(z["t0"]))
        state = {k: z[k] for k in z.files if k != "t0"}
        for m in models:
            d = deltas_to_n320(m, int(e.date.month))
            for world in ("A", "B"):
                for scale in (-1.0, 0.5):
                    path = OUT / f"{eid}_L2_{world}_{m}_s{scale:g}.npz"
                    if path.exists():
                        continue
                    keep, g = run_one(runner, counterfactual(state, d, world, scale=scale), t0, e.date, mask, coslat)
                    save(path, keep, g)
        print(f"{eid} control done  elapsed {time.time() - t_start:.0f}s", flush=True)


if __name__ == "__main__":
    sys.exit(main())
