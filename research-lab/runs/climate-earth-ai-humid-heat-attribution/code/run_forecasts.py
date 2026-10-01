#!/usr/bin/env python
"""AIFS re-forecasts (plan.md sec 3, 6). For each event and lead: the factual forecast F, and counterfactuals A and B for
each CMIP6 model's warming signal. Validation V3 first: a zero-delta counterfactual must reproduce F.
Saved per forecast: 2t, 2d, sp at the region's N320 points at 06, 12 and 18 UTC on the event day, and the global
(area-weighted by cos lat) mean 2t at the final step.
Output: data/processed/forecasts/{event}_L{L}_{world}_{model}.npz, results/tables/v3_check.csv
"""
import datetime
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from perturb import counterfactual, deltas_to_n320  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
PROC, TAB = RUN / "data" / "processed", RUN / "results" / "tables"
OUT = PROC / "forecasts"
REGIONS = {"South Asia": (22, 32, 68, 88), "Persian Gulf": (23, 31, 47, 57), "US Gulf coast": (27, 33, 263, 279)}
LEADS = (2, 4, 6)


def region_mask(lat, lon, region):
    la0, la1, lo0, lo1 = REGIONS[region]
    return (lat >= la0) & (lat <= la1) & (lon >= lo0) & (lon <= lo1)


def run_one(runner, state, t0, event_day, mask, coslat):
    hours = int((event_day - t0).total_seconds() // 3600) + 18
    keep = {}
    last = None
    inp = dict(date=t0.to_pydatetime(), fields={k: v.astype(np.float64) for k, v in state.items()})
    for s in runner.run(input_state=inp, lead_time=hours):
        d = pd.Timestamp(s["date"])
        if d.normalize() == event_day and d.hour in (6, 12, 18):
            keep[d.hour] = {k: np.asarray(s["fields"][k])[mask].astype(np.float32) for k in ("2t", "2d", "sp")}
        last = s
    g2t = float(np.sum(np.asarray(last["fields"]["2t"]) * coslat) / coslat.sum())
    return keep, g2t


def save(path, keep, g2t):
    arrs = {f"{k}_{h:02d}": v for h, fields in keep.items() for k, v in fields.items()}
    np.savez(path, global_2t_final=g2t, **arrs)


def main():
    from anemoi.inference.runners.simple import SimpleRunner
    OUT.mkdir(parents=True, exist_ok=True)
    ev = pd.read_csv(TAB / "events.csv", parse_dates=["date", "time"])
    models = sorted(pd.read_csv(TAB / "cmip6_models.csv").model.unique())
    ll = np.load(PROC / "n320_latlon.npz")
    lat, lon = ll["lat"], ll["lon"]
    coslat = np.cos(np.radians(lat))
    runner = SimpleRunner(str(RUN / "data" / "raw" / "aifs" / "aifs-single-mse-1.0.ckpt"), device="cuda")
    v3 = []
    t_start = time.time()
    for n_e, e in ev.iterrows():
        mask = region_mask(lat, lon, e.region)
        for L in LEADS:
            z = np.load(PROC / "ic" / f"{e.event_id}_L{L}.npz")
            t0 = pd.Timestamp(str(z["t0"]))
            state = {k: z[k] for k in z.files if k != "t0"}
            month = int(e.date.month)
            path = OUT / f"{e.event_id}_L{L}_F_none.npz"
            if not path.exists():
                keep, g = run_one(runner, state, t0, e.date, mask, coslat)
                save(path, keep, g)
                print(f"{e.event_id} L{L} F done  elapsed {time.time() - t_start:.0f}s", flush=True)
            if n_e == 0 and L == LEADS[0]:                               # V3: zero delta reproduces F
                d0 = deltas_to_n320(models[0], month)
                zero = counterfactual(state, d0, "B", scale=0.0)
                ic_diff = max(float(np.max(np.abs(zero[k].astype(np.float64) - state[k].astype(np.float64)))) for k in state)
                keep0, g0 = run_one(runner, zero, t0, e.date, mask, coslat)
                f = np.load(path)
                fc_diff = max(float(np.max(np.abs(keep0[h][k] - f[f"{k}_{h:02d}"]))) for h in keep0 for k in ("2t", "2d", "sp"))
                v3.append(dict(event=e.event_id, lead=L, max_abs_ic_diff=ic_diff, max_abs_forecast_diff=fc_diff))
                pd.DataFrame(v3).to_csv(TAB / "v3_check.csv", index=False)
                print("V3", v3[-1], flush=True)
            for m in models:
                d = deltas_to_n320(m, month)
                for world in ("A", "B"):
                    path = OUT / f"{e.event_id}_L{L}_{world}_{m}.npz"
                    if path.exists():
                        continue
                    cf = counterfactual(state, d, world)
                    keep, g = run_one(runner, cf, t0, e.date, mask, coslat)
                    save(path, keep, g)
            print(f"{e.event_id} L{L} all worlds done  elapsed {time.time() - t_start:.0f}s", flush=True)


if __name__ == "__main__":
    sys.exit(main())
