"""Synthetic checks of code/analysis.py before any real coverage is computed (plan section 8).

Uses the real panel's structure (countries, causes, years, quality groups) and the GBD 2021 values (p21, L21, U21) for
scale and interval widths. Every GBD 2023 value (p23, L23, U23) is REPLACED by simulation, so no outcome is seen.

Scenario A (calibrated): true error SD on the log scale equals the stated s for both releases, independent errors.
  Expect C2 near 0.95 and C1 near the benchmark E1.
Scenario B (too narrow where data are poor): in the `low` quality group, true error SDs are 2x the stated s.
  Expect C2(low) well below 0.95, C2(high) near 0.95, and H4 Supported.
Both scenarios add country- and cause-level heterogeneity (log-normal multipliers on the error SD, SD 0.3), so the
bootstrap intervals reflect clustering. The scenario-A interval widths give the precision used in plan section 9."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
import analysis as A  # noqa: E402

Z = A.Z


def simulate(p, q, inflate_low, seed):
    rng = np.random.default_rng(seed)
    p = p[["location_id", "cause_id", "year", "location_name", "cause_name", "l1_name", "l2_name", "p21", "L21", "U21", "pop21", "pop23"]].copy()
    ok = (p.p21 > 0) & (p.L21 > 0) & (p.U21 > p.L21)
    s = np.where(ok, (np.log(p.U21.where(ok, 1)) - np.log(p.L21.where(ok, 1))) / (2 * Z), 0.0)
    kc = dict(zip(q.location_id, rng.lognormal(0, 0.3, len(q))))
    kk = dict(zip(p.cause_id.unique(), rng.lognormal(0, 0.3, p.cause_id.nunique())))
    # normalise multipliers so that their mean square is 1 (keeps scenario A calibrated on average)
    k = p.location_id.map(kc).values * p.cause_id.map(kk).values
    k = k / np.sqrt(np.mean(k[ok] ** 2))
    low = p.location_id.isin(q[q.quality_group == "low"].location_id).values
    infl = np.where(low, inflate_low, 1.0) * k
    log_theta = np.log(np.where(ok, p.p21, 1.0)) - rng.normal(0, s * infl)       # truth consistent with observed p21
    s23 = 0.8 * s                                                                  # the later release states narrower UIs
    p23 = np.exp(log_theta + rng.normal(0, s23 * infl))
    p["p21"] = np.where(ok, p.p21, 0.0)
    p["p23"] = np.where(ok, p23, 0.0)
    p["L23"] = np.where(ok, p23 * np.exp(-Z * s23), 0.0)
    p["U23"] = np.where(ok, p23 * np.exp(Z * s23), 0.0)
    return A.metrics(p)


def main():
    panel = pd.read_parquet(RUN / "data" / "panel.parquet")
    q = pd.read_parquet(RUN / "data" / "quality.parquet")
    res = {}
    for name, inflate, seed in (("A_calibrated", 1.0, 1), ("B_low_too_narrow_x2", 2.0, 2)):
        p = simulate(panel, q, inflate, seed)
        out = A.primary(p, q)
        e = p[p.elig1 & p.elig2]
        res[name] = out
        print(f"--- {name}: C1 {out['H1']['estimate']:.3f} [{out['H1']['lower95']:.3f}, {out['H1']['upper95']:.3f}] (E1 {e.e1.mean():.3f});"
              f" C2 {out['H3']['estimate']:.3f} [{out['H3']['lower95']:.3f}, {out['H3']['upper95']:.3f}]")
        for h in ("H2", "H4"):
            g = out[h]["by_group"]
            print(f"    {h}: " + "; ".join(f"{k} {v['estimate']:.3f} [{v['lower95']:.3f}, {v['upper95']:.3f}]" for k, v in g.items())
                  + f" | high-low {out[h]['high_minus_low']['estimate']:.3f} [{out[h]['high_minus_low']['lower95']:.3f}, "
                  f"{out[h]['high_minus_low']['upper95']:.3f}] -> {out[h]['verdict']}")
        print("    verdicts:", {h: out[h]["verdict"] for h in ("H1", "H2", "H3", "H4")})
    a, b = res["A_calibrated"], res["B_low_too_narrow_x2"]
    assert abs(a["H3"]["estimate"] - 0.95) < 0.02, "scenario A: C2 should be near 0.95"
    assert b["H4"]["verdict"] == "Supported", "scenario B: the gradient should be detected"
    assert a["H4"]["verdict"] in ("Refuted", "Inconclusive"), "scenario A: no gradient"
    d = a["H4"]["high_minus_low"]
    print(f"precision: H4 difference half-width {(d['upper95'] - d['lower95']) / 2:.3f}; "
          f"H3 half-width {(a['H3']['upper95'] - a['H3']['lower95']) / 2:.3f}; H1 half-width {(a['H1']['upper95'] - a['H1']['lower95']) / 2:.3f}")
    print("SYNTHETIC TESTS PASSED")


if __name__ == "__main__":
    main()
