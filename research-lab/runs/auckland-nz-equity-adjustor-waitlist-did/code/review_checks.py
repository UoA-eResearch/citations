"""Checks added after independent review (deviations.md D3-D5). The preregistered verdict (analysis.py) is unchanged.

1. Specialty decomposition of beta (Frisch-Waugh-Lovell contributions by specialty).
2. Within-specialty models: FE dsg + dsm + gm, and fully saturated dsg + dsm + sgm, each with a 16-district permutation.
3. Quadruple difference: Maori+Pacific vs Asian (Asian as reference), with permutation.
4. Baselines and timing: pre-COVID baseline (Jul 2018 - Jan 2020); tool era as baseline; post halves; Jan-Jun 2026;
   beta - tau; rank of tau. Each with a 16-district permutation rank.
5. Long event study from Jul 2018 (plan FE and saturated FE).
6. Stock growth by ethnicity, Auckland vs controls (pre vs post).
7. Unweighted estimates with small cells trimmed.
8. Rank by |t| (heteroskedasticity-robust) and placebo min/max.
9. Maori and Pacific separately under saturated FE.
Outputs: results/tables/review_*.csv, results/figures/review_long_event.png
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402

warnings.filterwarnings("ignore")
TAB, FIG = A.TAB, A.FIG
PLAN_FE = "dsg + sm + dm + gm"
DSM_FE = "dsg + dsm + gm"
SAT_FE = "dsg + dsm + sgm"
VINTAGE = "waitlist-detail-extract-q4-2025-26.xlsx"


def panel(g, treated, controls, group, pre, post, tool=A.TOOL, ref="EO", min_total=None):
    q = g[g.district.isin([treated] + controls) & g.group.isin([group, ref])].copy()
    keep = ((q.month >= pre[0]) & (q.month <= pre[1])) | ((q.month >= post[0]) & (q.month <= post[1]))
    if tool is not None:
        keep |= (q.month >= tool[0]) & (q.month <= tool[1])
    q = q[keep]
    if min_total:
        q = q[q.total > min_total]
    tg = (q.district == treated) & (q.group == group)
    q["tp"] = (tg & (q.month >= post[0]) & (q.month <= post[1])).astype(int)
    q["tt"] = (tg & (q.month >= tool[0]) & (q.month <= tool[1])).astype(int) if tool is not None else 0
    ms = q.month.dt.strftime("%Y-%m")
    q["dsg"] = q.district + "|" + q.specialty + "|" + q.group
    q["sm"] = q.specialty + "|" + ms
    q["dm"] = q.district + "|" + ms
    q["gm"] = q.group + "|" + ms
    q["dsm"] = q.district + "|" + q.specialty + "|" + ms
    q["sgm"] = q.specialty + "|" + q.group + "|" + ms
    return q


def fit(q, fe=PLAN_FE, weights=True, vcov=None):
    terms = "tp" + (" + tt" if q.tt.sum() > 0 else "")
    return pf.feols(f"L ~ {terms} | {fe}", data=q, weights="total" if weights else None,
                    vcov=vcov or {"CRV1": "district"})


def perm(g, label, group="MP", pre=A.PRE, post=("2024-09-30", "2026-06-30"), tool=A.TOOL, ref="EO", fe=PLAN_FE,
         weights=True, min_total=None, coef="tp"):
    rows = []
    for d in ["Auckland"] + A.CONTROLS:
        ctr = A.CONTROLS if d == "Auckland" else [c for c in A.CONTROLS if c != d]
        q = panel(g, d, ctr, group, pre, post, tool, ref, min_total)
        try:
            m = fit(q, fe, weights, vcov="hetero")
        except ValueError:  # all regressors collinear (no treated cells after trimming)
            m = None
        if m is None or coef not in m.coef().index:  # indicator absorbed (e.g. no treated cells in a small district)
            print(f"  [{label}] {d}: {coef} not identified")
            rows.append(dict(district=d, beta=np.nan, t=np.nan))
            continue
        b = float(m.coef()[coef])
        rows.append(dict(district=d, beta=b, t=b / float(m.se()[coef])))
    p = pd.DataFrame(rows)
    p["rank"] = p.beta.rank(ascending=False)
    p["rank_t"] = p.t.rank(ascending=False)
    a = p[p.district == "Auckland"].iloc[0]
    pl = p[p.district != "Auckland"].beta
    return dict(analysis=label, beta=a.beta, rank=a["rank"], rank_t=a.rank_t, n_districts=int(p.beta.notna().sum()),
                placebo_min=pl.min(), placebo_max=pl.max())


def fwl_contrib(q, fe=PLAN_FE):
    """Frisch-Waugh-Lovell: beta = sum_i w r_tp r_y / sum_i w r_tp^2, where r are residuals after weighted demeaning
    by the fixed effects and partialling out tt; contributions are summed by specialty."""
    from pyfixest.estimation import demean
    q = q.reset_index(drop=True)
    fl = np.column_stack([pd.factorize(q[f])[0] for f in fe.replace(" ", "").split("+")]).astype(np.uint64)
    w = q.total.to_numpy(float)
    X, ok = demean(q[["tp", "tt", "L"]].to_numpy(float), fl, w, tol=1e-10)
    assert ok
    tp, tt, y = X[:, 0], X[:, 1], X[:, 2]
    bt = (w * tt * tp).sum() / (w * tt * tt).sum()
    rt = tp - bt * tt
    by = (w * tt * y).sum() / (w * tt * tt).sum()
    ry = y - by * tt
    c = pd.Series(w * rt * ry, index=q.index).groupby(q.specialty).sum() / (w * rt ** 2).sum()
    return c.sort_values(ascending=False)


def main():
    g = A.load(VINTAGE)
    post = ("2024-09-30", "2026-06-30")
    out = []
    # 1. decomposition
    q = panel(g, "Auckland", A.CONTROLS, "MP", A.PRE, post)
    c = fwl_contrib(q)
    c.rename("contribution_pp").to_csv(TAB / "review_fwl_specialty.csv")
    print("FWL total", round(c.sum(), 3)); print(c.head(8).round(2).to_string())
    # 2-4. permutations
    specs = [
        dict(label="preregistered (plan FE)"),
        dict(label="within specialty: FE dsg + dsm + gm", fe=DSM_FE),
        dict(label="fully saturated: FE dsg + dsm + sgm", fe=SAT_FE),
        dict(label="tool-era tau (plan FE)", coef="tt"),
        dict(label="quadruple difference: MP vs Asian (plan FE)", ref="AS"),
        dict(label="quadruple difference: MP vs Asian (saturated FE)", ref="AS", fe=SAT_FE),
        dict(label="Asian vs EO (plan FE)", group="AS"),
        dict(label="pre-COVID baseline Jul 2018 - Jan 2020 (plan FE)", pre=("2018-07-31", "2020-01-31")),
        dict(label="pre-COVID baseline (saturated FE)", pre=("2018-07-31", "2020-01-31"), fe=SAT_FE),
        dict(label="tool era as baseline: post vs Feb 2023 - Jul 2024", pre=A.TOOL, tool=None),
        dict(label="post Sep 2024 - Jul 2025", post=("2024-09-30", "2025-07-31")),
        dict(label="post Aug 2025 - Jun 2026", post=("2025-08-31", "2026-06-30")),
        dict(label="post Jan - Jun 2026", post=("2026-01-31", "2026-06-30")),
        dict(label="unweighted, cells with total > 5", weights=False, min_total=5),
        dict(label="unweighted, cells with total > 20", weights=False, min_total=20),
        dict(label="unweighted, cells with total > 50", weights=False, min_total=50),
    ]
    for sp in specs:
        lab = sp.pop("label")
        out.append(perm(g, lab, **sp))
    # Maori / Pacific separately, saturated
    for grp in ("Māori", "Pacific"):
        e = A.read_elective(VINTAGE)
        for col in ("u120", "total"):
            e[col] = pd.to_numeric(e[col].replace("<5", 2.5))
        e = e[e.ethnicity.isin([grp, "European/Other"])].copy()
        e["month"] = pd.to_datetime(e.month)
        e["group"] = np.where(e.ethnicity == grp, "MP", "EO")
        e = e.groupby(["month", "district", "specialty", "group"], as_index=False)[["u120", "total"]].sum()
        e["L"] = 100 * (1 - e.u120 / e.total)
        out.append(perm(e, f"{grp} only (saturated FE)", fe=SAT_FE))
    res = pd.DataFrame(out)
    res.to_csv(TAB / "review_checks.csv", index=False)
    print(res.round(2).to_string(index=False))
    # 6. stock growth
    raw = A.read_elective(VINTAGE)
    for col in ("u120", "total"):
        raw[col] = pd.to_numeric(raw[col].replace("<5", 2.5))
    raw["month"] = pd.to_datetime(raw.month)
    raw["long"] = raw.total - raw.u120
    raw["where"] = np.where(raw.district == "Auckland", "Auckland", np.where(raw.district.isin(A.CONTROLS), "controls", None))
    raw["per"] = np.where((raw.month >= A.PRE[0]) & (raw.month <= A.PRE[1]), "pre",
                         np.where((raw.month >= post[0]) & (raw.month <= post[1]), "post", None))
    r = raw.dropna(subset=["where", "per"]).groupby(["where", "ethnicity", "per", "month"])[["total", "long"]].sum()
    r = r.groupby(["where", "ethnicity", "per"]).mean().unstack("per")
    st = pd.DataFrame({"stock_pre": r[("total", "pre")], "stock_post": r[("total", "post")],
                       "stock_ratio": r[("total", "post")] / r[("total", "pre")],
                       "long_ratio": r[("long", "post")] / r[("long", "pre")],
                       "L_pre": 100 * r[("long", "pre")] / r[("total", "pre")],
                       "L_post": 100 * r[("long", "post")] / r[("total", "post")]})
    st.to_csv(TAB / "review_stock_growth.csv")
    print(st.round(2).to_string())
    # 5. long event study
    fig, ax = plt.subplots(figsize=(8.5, 3.6))
    for fe, col, lab in [(PLAN_FE, "#2f5d8a", "preregistered fixed effects"), (SAT_FE, "#d08a2c", "within specialty (saturated)")]:
        q = g[g.district.isin(["Auckland"] + A.CONTROLS) & g.group.isin(["MP", "EO"])].copy()
        q = q[(q.month >= "2018-07-31") & (q.month <= "2026-06-30") & (q.month != "2024-08-31")]
        ms = q.month.dt.strftime("%Y-%m")
        q["dsg"] = q.district + "|" + q.specialty + "|" + q.group
        q["sm"], q["dm"], q["gm"] = q.specialty + "|" + ms, q.district + "|" + ms, q.group + "|" + ms
        q["dsm"], q["sgm"] = q.district + "|" + q.specialty + "|" + ms, q.specialty + "|" + q.group + "|" + ms
        tg = (q.district == "Auckland") & (q.group == "MP")
        names = []
        for mth in sorted(q.month.unique()):
            if pd.Timestamp(mth) == pd.Timestamp("2023-01-31"):
                continue
            nm = "m" + pd.Timestamp(mth).strftime("%Y%m")
            q[nm] = (tg & (q.month == mth)).astype(int)
            names.append(nm)
        m = pf.feols("L ~ " + " + ".join(names) + f" | {fe}", data=q, weights="total", vcov="hetero")
        ev = pd.DataFrame({"month": [pd.Timestamp(n[1:5] + "-" + n[5:7] + "-01") for n in names], "coef": m.coef().values})
        ev = pd.concat([ev, pd.DataFrame({"month": [pd.Timestamp("2023-01-01")], "coef": [0.0]})]).sort_values("month")
        ev["coef"] -= ev[(ev.month >= "2021-07-01") & (ev.month <= "2023-01-31")].coef.mean()
        ev.assign(fe=fe).to_csv(TAB / f"review_long_event_{'plan' if fe == PLAN_FE else 'saturated'}.csv", index=False)
        sm = ev.set_index("month").coef.rolling(3, center=True, min_periods=1).mean()
        ax.plot(sm.index, sm.values, color=col, lw=1.4, label=lab)
    ax.axhline(0, color="#888", lw=0.8)
    for d_, lab_ in [("2020-03-25", "COVID"), ("2021-08-17", "Delta lockdown"), ("2023-02-01", "tool"), ("2024-08-01", "discontinued")]:
        ax.axvline(pd.Timestamp(d_), color="#b5443b", lw=0.7, ls="--")
        ax.text(pd.Timestamp(d_), ax.get_ylim()[1], " " + lab_, fontsize=7, va="top", color="#b5443b")
    ax.set_ylabel("Auckland MP minus EO long-wait gap\nrelative to controls (pp; 3-month mean)", fontsize=8)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(FIG / "review_long_event.png", dpi=150)


if __name__ == "__main__":
    main()
