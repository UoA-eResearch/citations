"""Checks on the recovery-time algorithm and the models, with synthetic data whose answers are known.

Run before any real event is analysed.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import recovery as R  # noqa: E402

rng = np.random.default_rng(7)
d0 = pd.Timestamp("2022-06-01")
dates = pd.date_range(d0 - pd.Timedelta(days=R.FIT_BACK), d0 + pd.Timedelta(days=R.HORIZON + 2 * R.MAX_K))
day = (dates - d0).days.to_numpy()
passed = failed = 0


def check(name, ok, detail=""):
    global passed, failed
    print(("PASS " if ok else "FAIL ") + name + (f"  {detail}" if detail else ""))
    passed += ok
    failed += not ok


def busy(mu=6.0, alpha=0.2):
    n = 1 / alpha
    return rng.negative_binomial(n, n / (n + mu), size=len(dates)).astype(float)


# 1. a busy port with no disruption: mostly not flagged
flags = [R.one_event(pd.Series(busy(), index=dates), None, d0, rng, use_index=False)["disrupted"] for _ in range(40)]
check("no closure -> rarely flagged (false alarms)", np.mean(flags) <= 0.15, f"rate {np.mean(flags):.2f}")

# 2. a busy port closed for 14 days: flagged, recovery near 14
Ts = []
for _ in range(30):
    y = busy(); y[(day >= 0) & (day < 14)] = 0
    res = R.one_event(pd.Series(y, index=dates), None, d0, rng, use_index=False)
    if res["disrupted"]:
        Ts.append(res["T"])
check("14-day closure detected", len(Ts) >= 28, f"{len(Ts)}/30")
check("14-day closure -> recovery time near 14 (centred window, no trailing lag)",
      abs(np.median(Ts) - 14) <= 4, f"median T {np.median(Ts):.0f}")

# 3. a closure that never ends is censored at the horizon
y = busy(); y[day >= 0] = 0
res = R.one_event(pd.Series(y, index=dates), None, d0, rng, use_index=False)
check("permanent closure -> censored at horizon", res["event"] == 0 and res["T"] == R.HORIZON, str(res.get("T")))

# 4. a global shock that also hits the reference index is NOT read as a disruption when the index is used
shock = np.where(day >= -5, 0.35, 1.0)
idx = pd.Series(rng.poisson(400 * shock), index=dates).astype(float)
y = pd.Series(rng.poisson(6 * shock), index=dates).astype(float)
with_idx = R.one_event(y, idx, d0, rng, use_index=True)
without = R.one_event(y, None, d0, rng, use_index=False)
check("shared shock absorbed by the reference index", not with_idx["disrupted"], f"with index: {with_idx['disrupted']}")
check("...and read as a disruption without it", without["disrupted"], f"own history: {without['disrupted']}")

# 5. a QUIET port (0.5 calls/day) closed for 28 days: detected with the traffic-scaled window. With a fixed 7-day
#    window this was never detected, because zero-call weeks occur by chance and the statistic floors at zero.
hits = 0
for _ in range(20):
    y = busy(mu=0.5, alpha=0.25); y[(day >= 0) & (day < 28)] = 0
    hits += R.one_event(pd.Series(y, index=dates), None, d0, rng, use_index=False)["disrupted"]
check("quiet port, 28-day closure -> detected (traffic-scaled window)", hits >= 14, f"{hits}/20")
fa = sum(R.one_event(pd.Series(busy(mu=0.5, alpha=0.25), index=dates), None, d0, rng, use_index=False)["disrupted"]
         for _ in range(20))
check("quiet port, no closure -> rarely flagged", fa <= 3, f"{fa}/20")

# 6. history too short is refused, not guessed
short = pd.Series(busy()[-200:], index=dates[-200:])
check("short history refused", R.one_event(short, None, d0, rng, use_index=False)["status"] == "short_history")

print(f"\n{passed}/{passed + failed} passed")
sys.exit(1 if failed else 0)
