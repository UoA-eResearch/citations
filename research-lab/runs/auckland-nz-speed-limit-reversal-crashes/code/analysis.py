"""Preregistered analysis (plan.md sections 4-5), Stage 1: post = 2025H2 + 2026H1.

Primary: Poisson DiD, injury crashes, segment + stratum x half-year FE, treated x post, SEs clustered by corridor,
window 2022H1-2026H1, transition half dropped for treated segments. Verdict: Supported if RR >= 1.10 and the one-sided
97.5% lower bound > 1; Contradicted if the one-sided 97.5% upper bound < 1.10; else Inconclusive.
Outputs: results/tables/main_results.csv, event_window.csv, manipulation_check.csv, power_benchmark.csv, data_checks.csv,
tiles.json; results/figures/event_window.png
"""
import json
import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyfixest as pf

sys.path.insert(0, str(Path(__file__).resolve().parent))
import panel as P  # noqa: E402

warnings.filterwarnings("ignore")
RUN = P.RUN
TAB, FIG = RUN / "results" / "tables", RUN / "results" / "figures"
Z = 1.959964
WIN = ("2022H1", "2026H1")


def crashes(tol=None):
    sfx = "" if tol is None else f"_tol{tol}"
    a = pd.read_parquet(RUN / "data" / f"crashes_pre{sfx}.parquet")
    b = pd.read_parquet(RUN / "data" / f"crashes_post{sfx}.parquet")
    return pd.concat([a, b], ignore_index=True)


def prep(p, win=WIN, last_post=None):
    last_post = last_post or win[1]
    p = p[(p.period >= win[0]) & (p.period <= win[1])].copy()
    trans = p.treated & (p.period == p.cohort)
    p = p[~trans].copy()
    p["tp"] = (p.treated & (p.period > p.cohort) & (p.period <= last_post)).astype(int)
    p = p[p.groupby("seg").y.transform("sum") > 0]
    return p


def est(p, rhs="tp"):
    m = pf.fepois(f"y ~ {rhs} | seg + stratum^period", data=p, vcov={"CRV1": "corridor"})
    return m


def row(label, p, **kw):
    try:
        m = est(p)
        b, se = float(m.coef()["tp"]), float(m.se()["tp"])
    except Exception as e:  # noqa: BLE001
        print(label, "failed:", e)
        b, se = np.nan, np.nan
    t = p[p.treated]
    return dict(analysis=label, rr=np.exp(b), lo=np.exp(b - Z * se), hi=np.exp(b + Z * se), log_rr=b, se=se,
                n_seg=p.seg.nunique(), n_treated_seg=t.seg.nunique(), treated_post_y=int(t[t.tp == 1].y.sum()),
                treated_pre_y=int(t[t.tp == 0].y.sum()), n_clusters=p.corridor.nunique(), **kw)


def verdict(r):
    if r["rr"] >= 1.10 and r["lo"] > 1.0:
        return "Supported"
    if r["hi"] < 1.10:
        return "Contradicted"
    return "Inconclusive"


def main():
    d = P.units()
    cr = crashes()
    checks = {"post_periods": sorted(cr[cr.fy >= "2025/2026"].period.unique().tolist()),
              "post_snapped_share": float((cr[cr.fy >= "2025/2026"].seg >= 0).mean()),
              "all_crashes_by_half_2025H1_2025H2_2026H1": cr.groupby("period").size().reindex(["2025H1", "2025H2", "2026H1"]).tolist()}
    print(checks)
    rows = []
    for oc in ["injury", "ksi", "all"]:
        p = prep(P.panel(cr, d, oc))
        rows.append(row({"injury": "PRIMARY injury crashes", "ksi": "fatal+serious crashes", "all": "all crashes"}[oc], p,
                        outcome=oc))
        if oc == "injury":
            prim = p
    pri = rows[0]
    pri["verdict"] = verdict(pri)
    print("PRIMARY:", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in pri.items()})
    # subsets of the primary
    for lab, mask in [("urban 30/40->50", "urban_30_40_to_50"), ("urban 50->60-80", "urban_50_up"),
                      ("peri-urban 60/70->70-100", "periurban_60_70_up"), ("rural 80/90->90-100", "rural_80_90_up")]:
        keep = (~prim.treated) | (prim.ttype == mask)
        q = prim[keep & prim.stratum.isin(prim[prim.ttype == mask].stratum)]
        rows.append(row(f"type: {lab}", q, outcome="injury"))
    sh = prim.rca == "State Highways"
    rows.append(row("state highways only", prim[sh], outcome="injury"))
    rows.append(row("local roads only", prim[~sh], outcome="injury"))
    rows.append(row("Auckland only", prim[prim.rca == "Auckland"], outcome="injury"))
    rows.append(row("without 2025H2 cohort", prim[~(prim.treated & (prim.cohort == "2025H2"))], outcome="injury"))
    for tol in (15, 50):
        rows.append(row(f"snap tolerance {tol} m", prep(P.panel(crashes(tol), d, "injury")), outcome="injury"))
    cn = cr[(cr.seg < 0) | cr.name_match]
    rows.append(row("name/SH-matched snaps only", prep(P.panel(cn, d, "injury")), outcome="injury"))
    full = prep(P.panel(cr, d, "injury"), win=("2017H2", "2026H1"))
    rows.append(row("full window 2017H2-2026H1 (known pre-trends)", full, outcome="injury"))
    # effect by post half
    for h in ["2025H2", "2026H1"]:
        q = prim[(prim.tp == 0) | (prim.period == h)]
        q = q[~(q.treated & (q.period > q.cohort) & (q.period != h))]
        rows.append(row(f"post half {h} only", q, outcome="injury"))
    # cohort-specific (ETWFE-style): separate treated x post indicators per cohort; report the 2025H1 cohort's
    q = prim.copy()
    q["tp_h2"] = (q.tp.astype(bool) & (q.cohort == "2025H2")).astype(int)
    q["tp"] = (q.tp.astype(bool) & (q.cohort == "2025H1")).astype(int)
    try:
        m = est(q, "tp + tp_h2") if q.tp_h2.sum() > 0 else est(q)
        b, se = float(m.coef()["tp"]), float(m.se()["tp"])
        rows.append(dict(analysis="cohort-specific indicators: 2025H1 cohort", rr=np.exp(b), lo=np.exp(b - Z * se),
                         hi=np.exp(b + Z * se), log_rr=b, se=se, outcome="injury",
                         n_treated_seg=q[q.treated & (q.cohort == "2025H1")].seg.nunique()))
    except Exception as e:  # noqa: BLE001
        print("cohort-specific failed:", e)
    # expressway 100 -> 110 (exploratory): same design with the expressway class as treated
    dx = pd.read_parquet(RUN / "data" / "seg_class.parquet")
    dx = dx[dx.klass.isin(["expressway", "control"])].copy()
    both = dx.groupby("stratum").klass.agg(lambda k: {"expressway", "control"} <= set(k))
    dx = dx[dx.stratum.map(both)].copy()
    dx["corridor"] = dx.rca + "|" + dx.name.fillna("") + "|" + np.where(dx.name.fillna("") == "", dx.way.astype(str), "")
    dx["treated"] = dx.klass == "expressway"
    if dx.treated.any():
        rows.append(row("exploratory: expressway 100->110", prep(P.panel(cr, dx, "injury")), outcome="injury"))
    res = pd.DataFrame(rows)
    res.to_csv(TAB / "main_results.csv", index=False)
    print(res[["analysis", "rr", "lo", "hi", "n_treated_seg", "treated_post_y", "treated_pre_y"]].round(3).to_string(index=False))

    # event study over the window
    q = P.panel(cr, d, "injury")
    q = q[(q.period >= WIN[0]) & (q.period <= WIN[1])]
    q = q[~(q.treated & (q.period == q.cohort)) & ~(q.treated & (q.cohort == "2025H2"))]
    q = q[q.groupby("seg").y.transform("sum") > 0]
    hs = [h for h in sorted(q.period.unique()) if h not in ("2024H2", "2025H1")]  # 2025H1 = transition (dropped)
    for h in hs:
        q[f"e_{h}"] = (q.treated & (q.period == h)).astype(int)
    m = est(q, " + ".join(f"e_{h}" for h in hs))
    ev = pd.DataFrame({"period": hs, "coef": m.coef().values, "se": m.se().values})
    ev.to_csv(TAB / "event_window.csv", index=False)
    allh = sorted(hs + ["2024H2", "2025H1"])
    e = ev.set_index("period")
    co = [0.0 if h == "2024H2" else (np.nan if h == "2025H1" else float(e.coef[h])) for h in allh]
    se = [0.0 if h in ("2024H2", "2025H1") else float(e.se[h]) for h in allh]
    fig, ax = plt.subplots(figsize=(7.5, 3.4))
    x = np.arange(len(allh))
    post = [h >= "2025H2" for h in allh]
    for i in range(len(allh)):
        if np.isnan(co[i]):
            continue
        c = "#c2462e" if post[i] else "#2f5d8a"
        ax.errorbar(x[i], np.exp(co[i]), yerr=[[np.exp(co[i]) - np.exp(co[i] - Z * se[i])], [np.exp(co[i] + Z * se[i]) - np.exp(co[i])]],
                    fmt="o", color=c, ms=5, capsize=3)
    ax.axhline(1, color="#888", lw=0.8)
    ax.axhline(1.10, color="#c2462e", lw=0.8, ls=":")
    ax.set_yscale("log")
    ax.set_yticks([0.6, 0.8, 1.0, 1.25, 1.6]); ax.set_yticklabels(["0.6", "0.8", "1.0", "1.25", "1.6"])
    ax.set_xticks(x, [h.replace("H", " H") for h in allh], fontsize=8)
    ax.axvspan(allh.index("2025H1") - 0.5, allh.index("2025H1") + 0.5, color="#ddd", alpha=0.6, lw=0)
    ax.set_ylabel("injury-crash rate ratio\n(treated vs control, vs 2024 H2)", fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG / "event_window.png", dpi=150)

    # manipulation check: CAS recorded limit on treated segments, before vs after
    c = cr[cr.seg.isin(d[d.treated & (d.cohort == "2025H1")].seg)].merge(d[["seg", "v0", "v1"]], on="seg")
    c["when"] = np.where(c.period >= "2025H2", "post 2025H2-2026H1", np.where(c.period.isin(["2023H2", "2024H1", "2024H2"]), "pre 2023H2-2024H2", "other"))
    mc = c[c.when != "other"].groupby("when").apply(lambda g: pd.Series({"n": len(g), "share_v0": (g.cas_limit == g.v0).mean(),
                                                                       "share_v1": (g.cas_limit == g.v1).mean()}))
    mc.to_csv(TAB / "manipulation_check.csv")
    print(mc.round(3).to_string())

    # power-model benchmark (exploratory)
    t = d[d.treated]
    pre_y = crashes()
    pre_y = pre_y[pre_y.injury & pre_y.period.isin(["2023H2", "2024H1", "2024H2"])].merge(t[["seg", "v0", "v1", "ttype"]], on="seg")
    pre_y["pred"] = ((pre_y.v0 + 0.25 * (pre_y.v1 - pre_y.v0)) / pre_y.v0) ** 2
    bm = pre_y.groupby("ttype").pred.agg(["mean", "size"])
    bm.loc["all"] = [pre_y.pred.mean(), len(pre_y)]
    bm.to_csv(TAB / "power_benchmark.csv")
    print(bm.round(3).to_string())
    pd.Series(checks).to_csv(TAB / "data_checks.csv")
    tiles = [["Injury-crash rate ratio", f"{pri['rr']:.2f}", f"95% CI {pri['lo']:.2f}-{pri['hi']:.2f}; Stage 1 verdict: {pri['verdict']}"],
             ["Roads raised", f"{round(t.length_m.sum() / 1000):,} km", f"{len(t):,} 100 m segments, mostly Auckland and state highways"],
             ["Injury crashes after", f"{pri['treated_post_y']}", "on raised roads, Jul 2025-Jun 2026"],
             ["Detectable effect", "RR 1.33", "80% power, one-sided 2.5% (from pre-period data)"]]
    json.dump(tiles, open(TAB / "tiles.json", "w"))


if __name__ == "__main__":
    main()
