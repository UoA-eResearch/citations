"""POST HOC (after the primary result): the preregistered pore-pressure kernel erfc(sqrt(tau/(t - t_i))) tends to 1
for lags much longer than tau, so the rain term becomes a cumulative rainfall anomaly that never drains. This check
replaces it with a draining kernel exp(-(t - t_i)/tau) (same tau grid, same design, split and scoring) to see whether
the held-out failure is the no-drainage form or the absence of a rain signal. Writes results/tables/posthoc_kernel.json."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dvv as D  # noqa: E402
import model as M  # noqa: E402


def drain_features(days, rain):
    r = rain - rain[(days >= M.T0) & (days <= M.TRAIN_END)].mean()
    n = len(r)
    lag = np.arange(1, n + 1)
    out = {}
    for tau in M.TAUS:
        conv = np.convolve(r, np.exp(-lag / tau))[:n]
        out[tau] = np.concatenate([[0.0], conv[:-1]])
    return out


def main():
    M.rain_features = drain_features          # same pipeline, draining kernel
    M.T_OUT = None
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        M.main("plan", "posthoc_kernel_raw.json")
    raw = json.loads((M.T / "posthoc_kernel_raw.json").read_text())
    (M.T / "posthoc_kernel_raw.json").unlink()
    (M.T / "posthoc_kernel_raw_fit.csv").rename(M.T / "posthoc_kernel_fit.csv")
    out = {k: raw[k] for k in ("pairs_scored", "median_heldout_r2", "ci", "share_pairs_r2_ge_0_5", "median_resid_2sd_pct", "tau_counts")}
    (M.T / "posthoc_kernel.json").write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
