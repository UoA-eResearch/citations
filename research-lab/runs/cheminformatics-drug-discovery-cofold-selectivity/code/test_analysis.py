"""Checks on the estimators in analysis.py against cases whose answer is known in advance.

Run before the panel results exist, so the statistics cannot be tuned to the outcome:
    venv/bin/python code/test_analysis.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402

rng = np.random.default_rng(7)
L, K = 32, 32
# a measured matrix with a ligand effect, a kinase effect and interaction, censored at 5
truth = 5.5 + rng.normal(0, 1, (L, 1)) + rng.normal(0, 0.8, (1, K)) + rng.normal(0, 0.7, (L, K))
meas = np.maximum(truth, 5.0)

ok = []


def check(name, cond, detail=""):
    ok.append(cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name} {detail}")


# 1. A perfect predictor: within-ligand median rho = 1
p = A.primary(truth, truth)
check("perfect predictor P1 == 1", abs(p["point"] - 1) < 1e-9, f"P1={p['point']:.3f}")

# 2. A ligand-only predictor carries no target information: rho == 0 for every ligand
lo = np.repeat(truth.mean(1)[:, None], K, axis=1)
p = A.primary(lo, meas)
check("ligand-only P1 == 0", p["point"] == 0 and p["lo"] == 0 and p["hi"] == 0)

# 3. A kinase-only predictor recovers the kinase effect, not the interaction: 0 < rho < 1
ko = np.repeat(truth.mean(0)[None, :], L, axis=0)
p = A.primary(ko, meas)
check("kinase-only P1 strictly between 0 and 1", 0.05 < p["point"] < 0.98, f"P1={p['point']:.3f}")

# 4. Sign: a predictor that is the negative of the truth gives -1
p = A.primary(-truth, truth)
check("sign convention", abs(p["point"] + 1) < 1e-9, f"P1={p['point']:.3f}")

# 5. Pure noise sits near zero and its interval covers zero
p = A.primary(rng.normal(0, 1, (L, K)), meas)
check("noise P1 interval covers 0", p["lo"] < 0 < p["hi"], f"P1={p['point']:.3f} [{p['lo']:.3f},{p['hi']:.3f}]")

# 6. Within-ligand on uncensored cells only drops ligands with too few uncensored values
few = meas.copy()
few[0] = 5.0
few[0, :6] = [6, 7, 8, 9, 10, 11]
r = A.within_ligand(truth, few, uncensored_only=True)
check("P2 keeps a ligand with 6 uncensored cells", np.isfinite(r[0]))
few[0, :6] = 5.0
few[0, :3] = [6, 7, 8]
r = A.within_ligand(truth, few, uncensored_only=True)
check("P2 drops a ligand with 3 uncensored cells", not np.isfinite(r[0]))

# 7. Two-way decomposition recovers the planted variance shares
m = 5 + np.repeat(rng.normal(0, 1, (L, 1)), K, 1)
d = A.two_way(m)
check("decomposition: ligand-only matrix", d["ligand"] > 0.999 and d["kinase"] < 1e-9,
      f"ligand={d['ligand']:.4f} kinase={d['kinase']:.2e}")
m = 5 + np.repeat(rng.normal(0, 1, (1, K)), L, 0)
d = A.two_way(m)
check("decomposition: kinase-only matrix", d["kinase"] > 0.999 and d["ligand"] < 1e-9,
      f"kinase={d['kinase']:.4f} ligand={d['ligand']:.2e}")

# 8. Hit rates: a perfect predictor gets top1 == 1 and precision@3 == 1
h = A.hit_rates(truth, truth)
check("perfect hit rates", h["top1"] == 1 and h["precision_at_3"] == 1)
# A predictor with no variation within a ligand has no ranking, so its hit rate must be undefined rather
# than whatever the column order happens to give. The previous version of this check asserted only that
# the number was small, which it was — by accident of the synthetic data's column order.
h = A.hit_rates(lo, meas)
check("ligand-only top1 is undefined, not a number", h["n"] == 0 and np.isnan(h["top1"]),
      f"n={h['n']} top1={h['top1']}")
import numpy.random as _r  # noqa: E402
perm = _r.default_rng(0).permutation(meas.shape[1])
h2 = A.hit_rates(lo[:, perm], meas[:, perm])
check("...and stays undefined under any column order", h2["n"] == 0)

# 9. The paired difference against a baseline is the difference of the two medians
diff = A.paired_difference(truth, meas, lo)
check("paired difference point estimate", abs(diff["point"] - (A.med(A.within_ligand(truth, meas))
                                                               - 0.0)) < 1e-12)

# 10. The promiscuity baseline uses no chemistry: identical columns for every ligand bar leave-one-out
Y = np.maximum(5.0 + rng.normal(0, 1, (68, 60)), 5.0)
b = A.base_promiscuity(Y, list(range(10)), list(range(20)))
check("promiscuity baseline rows nearly identical", np.std(b, axis=0).max() < 0.1,
      f"max column sd {np.std(b, axis=0).max():.3f}")

# 11. verdict() implements the decision rule
check("verdict Refuted", A.verdict(dict(lo=0.3, hi=0.5), dict(point=0.5)) == "Refuted")
check("verdict Supported", A.verdict(dict(lo=0.05, hi=0.2), dict(point=0.5)) == "Supported")
check("verdict Inconclusive (straddles)", A.verdict(dict(lo=0.1, hi=0.4), dict(point=0.5)) == "Inconclusive")
check("verdict Inconclusive (ligand-blind too)",
      A.verdict(dict(lo=0.05, hi=0.2), dict(point=0.1)).startswith("Inconclusive"))

print(f"\n{sum(ok)}/{len(ok)} passed")
sys.exit(0 if all(ok) else 1)
