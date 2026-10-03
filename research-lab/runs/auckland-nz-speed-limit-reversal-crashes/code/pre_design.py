"""Design calibration from pre-period crashes only (FY2017/18 - FY2024/25 = 2017H2 - 2025H1). No post data.

1. Treated pre-period crash volumes (injury, fatal+serious, all).
2. Manipulation-check baseline: share of 2023H2-2025H1 crashes on treated segments whose CAS speedLimit equals the
   NSLR limit v0 (validates snapping and the register), and the same for controls.
3. Event study of treated vs control by half-year, 2017H2-2024H2, relative to 2024H2 (pre-trends), Poisson with
   segment and stratum x period fixed effects, SEs clustered by corridor.
4. Placebo in space: 200 draws assigning 'treated' to control segments (as many per stratum as real treated, from
   strata that contain real treated segments). The placebo mirrors the real design's shape: 6 pre half-years
   (2020H2-2023H1), fake transition half 2023H2 (dropped), fake post 2024H1-2024H2. The SD of the placebo log rate
   ratios against the mean clustered SE gives the SE calibration factor.
   (The real estimation window is 2022H1-2026H1: 6 pre half-years 2022H1-2024H2 for the 2025H1 cohort.)
5. Minimum detectable effect for the real design (post = 2025H2 + 2026H1), from the placebo SD scaled by sqrt of the
   ratio of fake-post to expected real-post treated crash counts.
Output: results/tables/pre_*.csv, results/figures/pre_event_study.png
"""
import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyfixest as pf
from joblib import Parallel, delayed

sys.path.insert(0, str(Path(__file__).resolve().parent))
import panel as P  # noqa: E402

warnings.filterwarnings("ignore")
RUN = P.RUN
TAB, FIG = RUN / "results" / "tables", RUN / "results" / "figures"
PRE = [p for p in P.PERIODS if p <= "2025H1"]


def fit(df, rhs="tp"):
    m = pf.fepois(f"y ~ {rhs} | seg + stratum^period", data=df, vcov={"CRV1": "corridor"})
    return m


def placebo_draw(p, d, r):
    rng = np.random.default_rng(r)
    tr = d[d.treated]
    need = tr.groupby("stratum").size()
    ctrl = d[~d.treated & d.stratum.isin(need.index)]
    fake = []
    for s, g in ctrl.groupby("stratum"):
        k = min(need[s], len(g))
        fake.extend(rng.choice(g.seg.values, k, replace=False))
    fake = set(fake)
    q = p[~p.treated & (p.period >= "2020H2") & (p.period <= "2024H2") & (p.period != "2023H2")].copy()
    q["tp"] = (q.seg.isin(fake) & q.period.isin(["2024H1", "2024H2"])).astype(int)
    q = q[q.groupby("seg").y.transform("sum") > 0]
    try:
        m = fit(q)
        return float(m.coef()["tp"]), float(m.se()["tp"]), int(q[q.seg.isin(fake) & (q.tp == 1)].y.sum())
    except Exception:  # noqa: BLE001
        return np.nan, np.nan, 0


def main():
    d = P.units()
    cr = pd.read_parquet(RUN / "data" / "crashes_pre.parquet")
    t = d[d.treated]
    vol = []
    for oc in ["injury", "ksi", "all"]:
        c = cr[cr.seg.isin(t.seg)]
        c = c if oc == "all" else c[c[oc]]
        v = c.groupby("period").size().reindex(PRE, fill_value=0)
        vol.append(v.rename(oc))
    vol = pd.concat(vol, axis=1)
    vol.to_csv(TAB / "pre_treated_volumes.csv")
    print("treated segments", len(t), "km", round(t.length_m.sum() / 1000), "| controls", (~d.treated).sum())
    print(vol.tail(6).to_string())

    # manipulation-check baseline
    rec = cr[cr.period.isin(["2023H2", "2024H1", "2024H2", "2025H1"]) & (cr.seg >= 0)].merge(d[["seg", "treated", "v0"]], on="seg")
    mc = rec.assign(agree=rec.cas_limit == rec.v0).groupby("treated").agree.agg(["mean", "size"])
    mc.to_csv(TAB / "pre_manipulation_baseline.csv")
    print("CAS limit == NSLR v0 (2023H2-2025H1):", mc.round(3).to_dict())

    # event study (pre-trends), injury crashes
    p = P.panel(cr, d, "injury", PRE)
    q = p[p.period <= "2024H2"].copy()
    q = q[q.groupby("seg").y.transform("sum") > 0]
    ev = [x for x in PRE if x <= "2024H2" and x != "2024H2"]
    for x in ev:
        q[f"e_{x}"] = (q.treated & (q.period == x)).astype(int)
    m = fit(q, " + ".join(f"e_{x}" for x in ev))
    es = pd.DataFrame({"period": ev, "coef": m.coef().values, "se": m.se().values})
    es.to_csv(TAB / "pre_event_study.csv", index=False)
    w = m.wald_test(R=np.eye(len(ev)))  # joint test of all pre-period coefficients
    print("event study joint Wald (2017H2-2024H1 vs 2024H2):", dict(w))
    late = [x for x in ev if x >= "2022H1"]
    m2 = fit(q[q.period >= "2022H1"], " + ".join(f"e_{x}" for x in late))
    w2 = m2.wald_test(R=np.eye(len(late)))
    print("event study joint Wald within the estimation window (2022H1-2024H1 vs 2024H2):", dict(w2))
    pd.DataFrame({"period": late, "coef": m2.coef().values, "se": m2.se().values}).to_csv(TAB / "pre_event_study_window.csv", index=False)
    fig, ax = plt.subplots(figsize=(8, 3.2))
    xs = np.arange(len(ev) + 1)
    ax.errorbar(xs[:-1], es.coef, yerr=1.96 * es.se, fmt="o", color="#2f5d8a", ms=4, capsize=2)
    ax.plot(xs[-1], 0, "o", color="k", ms=4)
    ax.axhline(0, color="#888", lw=0.8)
    ax.set_xticks(xs, ev + ["2024H2"], rotation=60, fontsize=7)
    ax.set_ylabel("log rate ratio vs 2024H2")
    ax.set_title("Treated vs control injury crashes before the reversals (pre-trends)", fontsize=9)
    fig.tight_layout()
    fig.savefig(FIG / "pre_event_study.png", dpi=150)

    # placebo in space
    pp = P.panel(cr, d, "injury", PRE)
    res = Parallel(n_jobs=24, verbose=0)(delayed(placebo_draw)(pp, d, r) for r in range(200))
    pl = pd.DataFrame(res, columns=["coef", "se", "fake_post_crashes"])
    pl.to_csv(TAB / "pre_placebo_space.csv", index=False)
    sd, mse = pl.coef.std(), pl.se.mean()
    print(f"placebo: n={pl.coef.notna().sum()} mean {pl.coef.mean():.4f} SD {sd:.4f} mean clustered SE {mse:.4f} "
          f"ratio {sd / mse:.2f}; rejection rate |z|>1.96 {(np.abs(pl.coef / pl.se) > 1.96).mean():.3f}")

    # MDE for the real design
    rate = vol.injury.loc[["2023H2", "2024H1", "2024H2", "2025H1"]].mean()  # treated injury crashes per half
    exp_post = 2 * rate
    fake_post = pl.fake_post_crashes.mean()
    se_real = sd * np.sqrt(fake_post / exp_post)
    out = dict(placebo_sd=sd, placebo_mean_se=mse, se_factor=sd / mse, treated_injury_per_half=rate,
               expected_post_injury=exp_post, fake_post_injury=fake_post, se_real=se_real,
               mde_alpha025_power80=np.exp((1.96 + 0.8416) * se_real),
               mde_alpha05_power80=np.exp((1.645 + 0.8416) * se_real))
    pd.Series(out).to_csv(TAB / "pre_mde.csv")
    print({k: round(float(v), 4) for k, v in out.items()})


if __name__ == "__main__":
    main()
