"""Power of the preregistered decision rule (plan section 6), by simulation. No study data are used.

Generative model, for one layer (the primary pools two layers, simulated as independent):
  - model effect u_m ~ N(0, sd_model) for each of the 10 full-seed models;
  - within-model (SAE-seed) pair score: f = mu_sae + u_m + e,   e ~ N(0, sd_within), 3 pairs per model;
  - cross-model pair score:             f = mu_pre + (u_i + u_j) / 2 + v,  v ~ N(0, sd_pair), 3 SAE-seed combinations
    per model pair, sharing a pair effect w_ij ~ N(0, sd_pair) plus e.
R = mean cross / mean within (pooled over layers); 95% interval from the dyadic bootstrap over the 10 models.
Supported if the upper bound < 0.8, Refuted if the lower bound >= 0.8, Inconclusive otherwise.
Writes results/power.txt."""
import itertools
from pathlib import Path

import numpy as np

RUN = Path(__file__).resolve().parents[1]
M, S, B, SIMS = 10, 3, 400, 300


def scores(rng, mu_sae, ratio, sd_model, sd_pair, sd_within):
    u = rng.normal(0, sd_model, M)
    within = mu_sae + u[:, None] + rng.normal(0, sd_within, (M, S))
    cross = np.zeros((M, M, S))
    for i, j in itertools.combinations(range(M), 2):
        w = rng.normal(0, sd_pair)
        cross[i, j] = cross[j, i] = mu_sae * ratio + (u[i] + u[j]) / 2 + w + rng.normal(0, sd_within, S)
    return within.mean(1), cross.mean(2)


def stat(win, cr, idx):
    """R for a bootstrap draw idx (list of layers' (within, cross)); pairs of identical draws are skipped."""
    num, den = 0.0, 0.0
    for w, c in zip(win, cr):
        den += w[idx].mean()
        ii, jj = np.triu_indices(len(idx), 1)
        a, b = idx[ii], idx[jj]
        keep = a != b
        num += c[a[keep], b[keep]].mean()
    return num / den


def run(rng, ratio, sd_model, sd_pair, sd_within, mu_sae=0.6):
    out = []
    for _ in range(SIMS):
        layers = [scores(rng, mu_sae, ratio, sd_model, sd_pair, sd_within) for _ in range(2)]
        win, cr = [x[0] for x in layers], [x[1] for x in layers]
        bs = [stat(win, cr, rng.integers(0, M, M)) for _ in range(B)]
        lo, hi = np.percentile(bs, [2.5, 97.5])
        out.append("S" if hi < 0.8 else "R" if lo >= 0.8 else "I")
    return {k: out.count(k) / SIMS for k in "SRI"}


def main():
    rng = np.random.default_rng(20261012)
    lines = ["true R | sd_model | sd_pair | sd_within | P(Supported) | P(Refuted) | P(Inconclusive)"]
    for sd_model, sd_pair, sd_within in [(0.02, 0.02, 0.01), (0.05, 0.04, 0.02)]:
        for ratio in [0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 1.0]:
            p = run(rng, ratio, sd_model, sd_pair, sd_within)
            lines.append(f"{ratio:.2f} | {sd_model} | {sd_pair} | {sd_within} | {p['S']:.2f} | {p['R']:.2f} | {p['I']:.2f}")
            print(lines[-1], flush=True)
    (RUN / "results").mkdir(exist_ok=True)
    (RUN / "results" / "power.txt").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
