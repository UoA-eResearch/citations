"""POST HOC (after independent review, finding 1): the single-seed analysis with N = total parameters (the
Chinchilla convention), beside the preregistered non-embedding N. Same 2,000 single-seed draws as fit.py (same RNG
seed and draw order), same fitting procedure; only the N column changes.

  sensitivity_total_n.py -> results/tables/sensitivity_total_n.json
"""
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fit as F  # noqa: E402


def main():
    lad, tgt = F.load()
    lad = lad.assign(N=lad.N_total)
    tgt = tgt.assign(N=tgt.N_total)
    Nt, Dt = float(tgt.loc["2.8b", "N"]), float(tgt.loc["2.8b", "D"])
    seeds_by_size = {s: sorted(lad[lad["size"] == s].seed.unique()) for s in F.SIZES}
    rng = np.random.default_rng(F.SEED)                   # the first draws fit.py makes are the n = 1 ladders
    with ProcessPoolExecutor(4) as pool:
        pred, par, _ = F.run_draws(lad, 1, F.NLAD, Nt, Dt, rng, seeds_by_size, pool=pool)
    actual = float(tgt.loc["2.8b", "loss"])
    pc = lambda v: [round(float(np.percentile(v, q)), 4) for q in (5, 50, 95)]
    out = {"N": "total parameters", "ladders": len(pred), "W1": round(F.width(pred), 5),
           "median_error_2p8b": round(float(np.median(pred - actual)), 5),
           "share_overshoot": round(float(np.mean(pred > actual)), 3),
           "alpha": pc(par[:, 3]), "beta": pc(par[:, 4]), "E": pc(np.exp(par[:, 2]))}
    (F.T / "sensitivity_total_n.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
