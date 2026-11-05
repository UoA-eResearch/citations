"""Post hoc (review finding 1): how the false-assurance share depends on the ladder's step size. For every pair of
settings on each method's frozen ladder, apparent convergence (spread <= 0.01) and false assurance (error > 0.03)
are recomputed from the same runs, and the median error ratio between adjacent settings is reported.

  posthoc_steps.py -> results/tables/posthoc_steps.json
"""
import itertools
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyse as A  # noqa: E402

d, excluded, r, I = A.load("main")
r = r[r.status == "ok"]
out = {"finest_pair_share": {}, "pairs": {}, "adjacent_error_ratio_median": {}, "finest_setting_median_error": {}}
for m, g in r.groupby("method"):
    sets = sorted(g.setting.unique(), key=lambda s: A.FINENESS[m](np.array([s]))[0] if hasattr(A.FINENESS[m](np.array([s])), "__len__") else A.FINENESS[m](s))
    piv = g.pivot_table(index="id", columns="setting", values="value")
    ex = g.groupby("id").exact.first()
    err = (piv.sub(ex, axis=0)).abs()
    for a, b in itertools.combinations(sets, 2):
        conv = (piv[a] - piv[b]).abs() <= A.TOL
        fa = conv & (err[b] > A.BAD)          # b is the finer of the pair
        out["pairs"][f"{m} {a} -> {b}"] = {"converged": int(conv.sum()), "false_assurance": int(fa.sum()),
                                           "share": round(float(fa.sum() / max(conv.sum(), 1)), 4)}
    for a, b in zip(sets[:-1], sets[1:]):
        ratio = (err[a] / err[b].replace(0, np.nan)).dropna()
        out["adjacent_error_ratio_median"][f"{m} {a} -> {b}"] = round(float(ratio.median()), 3)
    out["finest_setting_median_error"][m] = {"setting": str(sets[-1]), "median_error": round(float(err[sets[-1]].median()), 4)}
    a, b = sets[-2], sets[-1]
    third = ((err[b] > err[a] / 3)).mean()
    out["finest_pair_share"][m] = {"pair": f"{a} -> {b}", "share_error_falls_less_than_threefold": round(float(third), 3)}
(A.T / "posthoc_steps.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
print(json.dumps(out, indent=1, default=str))
