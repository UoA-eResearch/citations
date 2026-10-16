"""Synthetic checks of analysis.py: known effects in, the right decision out. Added after D4 (analysis.py had
never been run before the real data, and its first run crashed)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402

A.NBOOT = 200
passed = failed = 0


def check(name, ok, detail=""):
    global passed, failed
    print(("PASS " if ok else "FAIL ") + name + (f"  {detail}" if detail else ""))
    passed += ok
    failed += not ok


def synth(n=300, storms=60, share_effect_a=0.0, share_effect_b=0.0, sids_tr=1.0, sids_disrupt=0.4, seed=1):
    rng = np.random.default_rng(seed)
    r = pd.DataFrame(dict(sid=rng.integers(0, storms, n).astype(str), log_size=rng.normal(7, 1, n),
                          log_activity=rng.normal(1, 0.7, n), cat=rng.integers(3, 6, n).astype(float),
                          closest_100km=rng.uniform(0, 1.5, n), share=rng.beta(0.5, 2, n),
                          sids=(rng.uniform(size=n) < 0.25).astype(float)))
    r["pict"] = False
    z = -0.5 + 0.8 * (r.log_activity - 1) + share_effect_a * (r.share - 0.2)
    p = 1 / (1 + np.exp(-z))
    p = np.where(r.sids == 1, sids_disrupt, p)
    r["D_"] = rng.uniform(size=n) < p
    scale = np.exp(2.0 + share_effect_b * (r.share - 0.2) + np.log(sids_tr) * r.sids)
    T = scale * rng.weibull(1.5, n)
    r["E_"] = (T < 120).astype(int)
    r["T_"] = np.where(r.D_, np.minimum(T, 120), 0.0)
    return r


r = synth()
h = A.h1(r)
check("no share effect -> not Supported", h["verdict"] != "Supported", f"dAIC {h['delta_aic']:.1f} {h['verdict']}")
r = synth(share_effect_a=4.0, share_effect_b=3.0)
h = A.h1(r)
check("strong share effect -> Supported", h["verdict"] == "Supported", f"dAIC {h['delta_aic']:.1f}")
check("...with the part-B ratio in the right direction", h["part_b_share_time_ratio"] > 1,
      f"TR per unit share {h['part_b_share_time_ratio']:.2f}, boot CI {h['part_b_share_tr_ci_storm_bootstrap']}")
r = synth(sids_tr=4.0, n=600, storms=120)
h = A.h2(r)
check("small-island time ratio 4 -> estimated near 4, not Refuted", h["verdict"] != "Refuted" and 2 < h["time_ratio"] < 8,
      f"TR {h['time_ratio']:.2f} ({h['lo']:.2f}, {h['hi']:.2f}) {h['verdict']}")
r = synth(sids_tr=1.0, n=600, storms=120)
h = A.h2(r)
check("small-island time ratio 1 -> Refuted", h["verdict"] == "Refuted", f"TR {h['time_ratio']:.2f} ({h['lo']:.2f}, {h['hi']:.2f})")
r = synth(sids_disrupt=0.01, seed=3)
r.loc[r.sids == 1, "D_"] = False
r.loc[r[r.sids == 1].index[:1], "D_"] = True
h = A.h2(r)
check("one disrupted small-island event -> Inconclusive, not a number", h["verdict"] == "Inconclusive" and h["time_ratio"] is None,
      h.get("reason", ""))
print(f"\n{passed}/{passed + failed} passed")
sys.exit(1 if failed else 0)
