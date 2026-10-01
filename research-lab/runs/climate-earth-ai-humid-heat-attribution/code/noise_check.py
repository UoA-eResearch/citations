#!/usr/bin/env python
"""Run-to-run nondeterminism of AIFS on this GPU (deviations.md D3): validation V3 showed that an identical initial
state gives a slightly different forecast. For each event at lead 2 days, the factual forecast is repeated twice more;
reported per field: max |difference| over the region points at the event-day times, and the spread of the event-peak and
area-mean TW across the three runs (the saved F plus two repeats).
Output: results/tables/noise_check.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze import tw_metrics  # noqa: E402
from run_forecasts import region_mask, run_one  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
PROC, TAB = RUN / "data" / "processed", RUN / "results" / "tables"


def main():
    from anemoi.inference.runners.simple import SimpleRunner
    ev = pd.read_csv(TAB / "events.csv", parse_dates=["date"])
    ll = np.load(PROC / "n320_latlon.npz")
    lat, lon = ll["lat"], ll["lon"]
    coslat = np.cos(np.radians(lat))
    runner = SimpleRunner(str(RUN / "data" / "raw" / "aifs" / "aifs-single-mse-1.0.ckpt"), device="cuda")
    rows = []
    for _, e in ev.iterrows():
        mask = region_mask(lat, lon, e.region)
        land = np.load(PROC / "era5_event" / f"{e.event_id}.npz")["lsm_12"][mask] > 0.5
        z = np.load(PROC / "ic" / f"{e.event_id}_L2.npz")
        t0 = pd.Timestamp(str(z["t0"]))
        state = {k: z[k] for k in z.files if k != "t0"}
        base = dict(np.load(PROC / "forecasts" / f"{e.event_id}_L2_F_none.npz"))
        runs = [base]
        for _ in range(2):
            keep, g = run_one(runner, state, t0, e.date, mask, coslat)
            runs.append({f"{k}_{h:02d}": v for h, f in keep.items() for k, v in f.items()})
        m = [tw_metrics(r, land) for r in runs]
        row = dict(event=e.event_id, peak_tw_runs=[round(x[0], 3) for x in m], area_tw_runs=[round(x[1], 3) for x in m],
                   peak_tw_range=max(x[0] for x in m) - min(x[0] for x in m), area_tw_range=max(x[1] for x in m) - min(x[1] for x in m))
        for k in ("2t", "2d", "sp"):
            row[f"max_abs_diff_{k}"] = max(float(np.max(np.abs(r[f"{k}_{h:02d}"] - base[f"{k}_{h:02d}"]))) for r in runs[1:] for h in (6, 12, 18))
            row[f"mean_abs_diff_{k}"] = float(np.mean([np.mean(np.abs(r[f"{k}_{h:02d}"] - base[f"{k}_{h:02d}"])) for r in runs[1:] for h in (6, 12, 18)]))
        rows.append(row)
        print(row, flush=True)
    pd.DataFrame(rows).to_csv(TAB / "noise_check.csv", index=False)


if __name__ == "__main__":
    sys.exit(main())
