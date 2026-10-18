"""Exploratory, not preregistered (written after the primary results were seen). How much does the H1 survival share
depend on the empirical null's centre? The fitted null is centred well below zero (negative controls are reported
less often with these drugs than with the rest of FAERS). Recomputes survival with the MLE sigma but the centre set to
0, and over a grid of centres and widths. Reads results/tables/signals_results.csv and primary.json; writes
results/tables/null_sensitivity.json."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from analysis import bh, calibrated_p, cluster_boot

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"


def main():
    ok = pd.read_csv(T / "signals_results.csv", dtype={"paper": str})
    prim = json.load(open(T / "primary.json"))
    mu0, sg0 = prim["null"]["mle"]["mu"], prim["null"]["mle"]["sigma"]
    lr, se = np.log(ok.primary_ror.values), ok.primary_se.values

    def share(mu, sg, x=ok):
        q = bh(calibrated_p(np.log(x.primary_ror.values), x.primary_se.values, mu, sg))
        return float(((x.primary_ror.values > 1) & (q < 0.05)).mean())
    out = dict(fitted=dict(mu=mu0, sigma=sg0, share=share(mu0, sg0)))
    out["centre_zero"] = dict(mu=0.0, sigma=sg0, share=share(0.0, sg0), ci=cluster_boot(ok, lambda x: share(0.0, sg0, x)))
    out["grid"] = [dict(mu=m, sigma=s, share=round(share(m, s), 3)) for m in (-0.85, -0.5, -0.25, 0.0, 0.25) for s in (0.5, 0.75, 0.96, 1.12)]
    json.dump(out, open(T / "null_sensitivity.json", "w"), indent=1)
    print(json.dumps({k: out[k] for k in ("fitted", "centre_zero")}, indent=1))


if __name__ == "__main__":
    main()
