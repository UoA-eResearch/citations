"""Checks added after independent review (deviations.md D6-D11). None changes the preregistered primary estimate.

1. All-crash secondary: window sensitivity, non-injury only, event study (review F1).
2. Variable (school) zones near treated segments, and the primary without those segments (F2).
3. Strata table: treated vs control injury crashes in the window (F4).
4. Corrected reduction half (first post-t22 record carrying v0) and corrected cohort (first post-t0 record
   carrying v1) instead of the record in force at t0 / t1, which re-certifications can misdate (F5, F6).
5. Placebo in space with at most half the controls of each stratum fake-treated, so every stratum keeps controls (F3).
Outputs: results/tables/review_*.csv
"""
import sys
import warnings
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from joblib import Parallel, delayed

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402
import nslr  # noqa: E402
import panel as P  # noqa: E402

warnings.filterwarnings("ignore")
RUN, TAB = P.RUN, P.RUN / "results" / "tables"


def half(t):
    return f"{t.year}H{1 if t.month <= 6 else 2}"


def main():
    d = P.units()
    cr = A.crashes()
    out = []
    # 1. all-crash sensitivity
    for start in ["2017H2", "2020H2", "2022H1", "2023H2", "2024H1"]:
        out.append(A.row(f"all crashes, window from {start}", A.prep(P.panel(cr, d, "all"), win=(start, "2026H1")), outcome="all"))
    ni = cr.assign(noninj=~cr.injury)
    out.append(A.row("non-injury crashes only", A.prep(P.panel(ni, d, "noninj")), outcome="noninj"))
    q = P.panel(cr, d, "all")
    q = q[(q.period >= "2022H1") & (q.period <= "2026H1")]
    q = q[~(q.treated & (q.period == q.cohort)) & ~(q.treated & (q.cohort == "2025H2"))]
    q = q[q.groupby("seg").y.transform("sum") > 0]
    hs = [h for h in sorted(q.period.unique()) if h not in ("2024H2", "2025H1")]
    for h in hs:
        q[f"e_{h}"] = (q.treated & (q.period == h)).astype(int)
    m = A.est(q, " + ".join(f"e_{h}" for h in hs))
    pd.DataFrame({"period": hs, "rr": np.exp(m.coef().values), "z": (m.coef() / m.se()).values}).to_csv(
        TAB / "review_event_all_crashes.csv", index=False)

    # 2. variable (school) zones live Jul 2025 - Jun 2026 near treated segments
    var = nslr.load(category="Variable")
    var = var[(var.eff <= pd.Timestamp("2026-06-30", tz=nslr.TZ)) & (var.ineff.isna() | (var.ineff > pd.Timestamp("2025-07-01", tz=nslr.TZ)))]
    segs = gpd.read_parquet(RUN / "data" / "segments.parquet", columns=["seg", "geometry"])
    tseg = segs[segs.seg.isin(d[d.treated].seg)]
    prim = A.prep(P.panel(cr, d, "injury"))
    tpost = prim[prim.treated & (prim.tp == 1)].groupby("seg").y.sum()
    near = {}
    for r in (30, 50, 100):
        i, _ = var.sindex.query(tseg.geometry.values, predicate="dwithin", distance=r)
        near[r] = set(tseg.seg.values[np.unique(i)])
        out.append(dict(analysis=f"treated segments within {r} m of a live Variable zone", n_treated_seg=len(near[r]),
                        rr=len(near[r]) / len(tseg), treated_post_y=int(tpost.reindex(list(near[r])).fillna(0).sum())))
    out.append(A.row("primary without treated segments within 50 m of a Variable zone",
                     prim[~prim.seg.isin(near[50])], outcome="injury"))
    school = set(pd.read_parquet(RUN / "data" / "seg_class.parquet").pipe(lambda x: x[x.klass == "treated"]).seg) & \
        set(d[d.ttype == "urban_30_40_to_50"].seg)
    h = pd.read_parquet(RUN / "data" / "hist_segments.parquet")
    T0 = pd.Timestamp("2024-10-29", tz=nslr.TZ)
    live0 = h[(h.eff <= T0) & (h.ineff.isna() | (h.ineff > T0))].groupby("pid").reason.first()
    sch = set(live0[live0 == "The presence of a school"].index) & set(d[d.treated].seg)
    out.append(A.row("primary without treated segments whose t0 reason is 'presence of a school'",
                     prim[~prim.seg.isin(sch)], outcome="injury"))

    # 3. strata table
    st = prim.groupby(["stratum", "treated"]).y.sum().unstack(fill_value=0).rename(columns={True: "treated_y", False: "control_y"})
    st["treated_segs"] = d[d.treated].groupby("stratum").size()
    st["control_segs"] = d[~d.treated].groupby("stratum").size()
    st.sort_values("treated_y", ascending=False).to_csv(TAB / "review_strata.csv")

    # 4. corrected reduction half and cohort
    hh = h[h.pid.isin(d.seg)].sort_values("eff")
    T22, T0b = pd.Timestamp("2022-06-01", tz=nslr.TZ), pd.Timestamp("2024-10-29", tz=nslr.TZ)
    dd = d.set_index("seg")
    red = dd[dd.red_half != "none"]
    x = hh[hh.pid.isin(red.index) & (hh.eff > T22)].merge(red[["v0"]], left_on="pid", right_index=True)
    first_v0 = x[x.value == x.v0].groupby("pid").eff.min().map(half)
    tr = dd[dd.treated]
    y = hh[hh.pid.isin(tr.index) & (hh.eff > T0b)].merge(tr[["v1"]], left_on="pid", right_index=True)
    first_v1 = y[y.value == y.v1].groupby("pid").eff.min().map(half)
    d2 = d.copy()
    d2["red_half"] = d2.seg.map(first_v0).fillna(d2.red_half)
    d2["cohort"] = np.where(d2.treated, d2.seg.map(first_v1).fillna(d2.cohort), d2.cohort)
    d2["stratum"] = d2.rca + "|" + d2.v0.astype("Int64").astype(str) + "|" + d2.red_half + "|" + d2.clsg
    both = d2.groupby("stratum").treated.agg(lambda t: t.any() and (~t).any())
    d2 = d2[d2.stratum.map(both)]
    out.append(dict(analysis="segments whose reduction half changes", n_seg=int((d2.set_index("seg").red_half != dd.reindex(d2.seg).red_half.values).sum()),
                    n_treated_seg=int((d2[d2.treated].set_index("seg").cohort != dd.reindex(d2[d2.treated].seg).cohort.values).sum())))
    out.append(A.row("primary with corrected reduction half and cohort", A.prep(P.panel(cr, d2, "injury")), outcome="injury"))

    res = pd.DataFrame(out)
    res.to_csv(TAB / "review_checks.csv", index=False)
    print(res[["analysis", "rr", "lo", "hi", "n_treated_seg", "treated_post_y"]].round(3).to_string(index=False))

    # 5. placebo with at most half the controls per stratum
    pp = P.panel(pd.read_parquet(RUN / "data" / "crashes_pre.parquet"), d, "injury")

    def draw(r):
        rng = np.random.default_rng(10_000 + r)
        need = d[d.treated].groupby("stratum").size()
        fake = []
        for s, g in d[~d.treated & d.stratum.isin(need.index)].groupby("stratum"):
            fake.extend(rng.choice(g.seg.values, min(need[s], len(g) // 2), replace=False))
        fake = set(fake)
        qq = pp[~pp.treated & (pp.period >= "2020H2") & (pp.period <= "2024H2") & (pp.period != "2023H2")].copy()
        qq["tp"] = (qq.seg.isin(fake) & qq.period.isin(["2024H1", "2024H2"])).astype(int)
        qq = qq[qq.groupby("seg").y.transform("sum") > 0]
        try:
            mm = A.est(qq)
            return float(mm.coef()["tp"]), float(mm.se()["tp"])
        except Exception:  # noqa: BLE001
            return np.nan, np.nan
    pl = pd.DataFrame(Parallel(n_jobs=24)(delayed(draw)(r) for r in range(200)), columns=["coef", "se"])
    pl.to_csv(TAB / "review_placebo_half.csv", index=False)
    print(f"placebo (<= half of controls): SD {pl.coef.std():.4f}, mean SE {pl.se.mean():.4f}, ratio "
          f"{pl.coef.std() / pl.se.mean():.2f}, rejection {(np.abs(pl.coef / pl.se) > 1.96).mean():.3f}")


if __name__ == "__main__":
    main()
