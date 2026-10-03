"""Preregistered analysis (plan.md sections 2-5).
Usage: analysis.py [vintage_file] [post_start] [post_end] [label]
Default: Q4 2025/26 vintage, post = Sep 2024 - Jun 2026 (Stage 1). The hold-out run passes a later vintage and
post = Jul - Dec 2026.
Outputs: results/tables/<label>_main.csv, <label>_permutation.csv, <label>_event.csv; results/figures/<label>_event.png
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

warnings.filterwarnings("ignore")
RUN = Path(__file__).resolve().parents[1]
RAW, TAB, FIG = RUN / "data" / "raw", RUN / "results" / "tables", RUN / "results" / "figures"
CONTROLS = ["Capital and Coast", "Hawke's Bay", "Hutt Valley", "MidCentral", "Wairarapa", "Whanganui", "Bay of Plenty",
            "Lakes", "Tairawhiti", "Taranaki", "Waikato", "Canterbury", "Nelson Marlborough", "South Canterbury",
            "West Coast"]
PRE = ("2021-07-31", "2023-01-31")
TOOL = ("2023-02-28", "2024-07-31")


def read_elective(vintage):
    """Elective sheet with columns mapped by name (older vintages add 'Quarter End when Data Extracted' and
    'Rurality'; rurality cells are summed by the groupby in load)."""
    e = pd.read_excel(RAW / vintage, sheet_name="Elective Waitlist")
    e = e.rename(columns={"Month End Date": "month", "Region": "region", "District": "district", "Specialty": "specialty",
                          "Ethnicity": "ethnicity", "Waiting under 120 days": "u120", "Total Waiting": "total"})
    e = e[["month", "region", "district", "specialty", "ethnicity", "u120", "total"]].copy()
    e["district"] = e.district.replace({"Hawkes Bay": "Hawke's Bay"})  # older vintages omit the apostrophe (D2)
    missing = set(CONTROLS + ["Auckland"]) - set(e.district)
    assert not missing, f"districts missing from {vintage}: {missing}"
    return e


def load(vintage, sup=2.5):
    e = read_elective(vintage)
    for c in ("u120", "total"):
        e[c] = pd.to_numeric(e[c].replace("<5", sup))
    e["month"] = pd.to_datetime(e.month)
    e["group"] = e.ethnicity.map({"Māori": "MP", "Pacific": "MP", "European/Other": "EO", "Asian": "AS"})
    g = e.groupby(["month", "district", "specialty", "group"], as_index=False)[["u120", "total"]].sum()
    g = g[g.total > 0]
    g["L"] = 100 * (1 - g.u120 / g.total)
    return g


def panel(g, treated, controls, group, post):
    q = g[g.district.isin([treated] + controls) & g.group.isin([group, "EO"])].copy()
    q = q[((q.month >= PRE[0]) & (q.month <= PRE[1])) | ((q.month >= TOOL[0]) & (q.month <= TOOL[1])) |
          ((q.month >= post[0]) & (q.month <= post[1]))]
    tg = (q.district == treated) & (q.group == group)
    q["tp"] = (tg & (q.month >= post[0])).astype(int)
    q["tt"] = (tg & (q.month >= TOOL[0]) & (q.month <= TOOL[1])).astype(int)
    q["dsg"] = q.district + "|" + q.specialty + "|" + q.group
    q["sm"] = q.specialty + "|" + q.month.dt.strftime("%Y-%m")
    q["dm"] = q.district + "|" + q.month.dt.strftime("%Y-%m")
    q["gm"] = q.group + "|" + q.month.dt.strftime("%Y-%m")
    return q


def est(q, weights=True):
    m = pf.feols("L ~ tp + tt | dsg + sm + dm + gm", data=q, weights="total" if weights else None,
                 vcov={"CRV1": "district"})
    return float(m.coef()["tp"]), float(m.coef()["tt"])


def permutation(g, group, post, weights=True):
    rows = []
    for d in ["Auckland"] + CONTROLS:
        ctr = CONTROLS if d == "Auckland" else [c for c in CONTROLS if c != d]
        b, t = est(panel(g, d, ctr, group, post), weights)
        rows.append(dict(district=d, beta=b, tool_era=t))
    p = pd.DataFrame(rows)
    p["rank"] = p.beta.rank(ascending=False).astype(int)
    return p


def main(vintage="waitlist-detail-extract-q4-2025-26.xlsx", post_start="2024-09-30", post_end="2026-06-30", label="stage1"):
    post = (post_start, post_end)
    g = load(vintage)
    perm = permutation(g, "MP", post)
    perm.to_csv(TAB / f"{label}_permutation.csv", index=False)
    a = perm.set_index("district").loc["Auckland"]
    plac = perm[perm.district != "Auckland"].beta
    q05, q95 = np.percentile(plac, [5, 95])
    nc = permutation(g, "AS", post)
    nc_a = nc.set_index("district").loc["Auckland"]
    nc.to_csv(TAB / f"{label}_negative_control.csv", index=False)
    sup = (a.beta >= 4) and (a["rank"] == 1) and (abs(nc_a.beta) < 2)
    con = (a.beta - q05) < 4
    verdict = "Supported" if sup else ("Contradicted" if con else "Inconclusive")
    rows = [dict(analysis="PRIMARY beta (Auckland MP-EO gap change, pp)", value=a.beta, rank=int(a["rank"]),
                 p_perm=a["rank"] / 16, q05=q05, q95=q95, verdict=verdict),
            dict(analysis="tool-era effect tau (pp)", value=a.tool_era),
            dict(analysis="negative control: Asian vs EO beta (pp)", value=nc_a.beta, rank=int(nc_a["rank"]))]
    # secondary
    if label == "stage1":
        b, _ = est(panel(g, "Auckland", CONTROLS, "MP", post), weights=False)
        rows.append(dict(analysis="unweighted beta", value=b))
        for s_ in (1, 4):
            gs = load(vintage, sup=s_)
            rows.append(dict(analysis=f"'<5' set to {s_}", value=est(panel(gs, "Auckland", CONTROLS, "MP", post))[0]))
        three = g.copy()
        three["district"] = three.district.replace({"Waitemata": "Auckland", "Counties Manukau": "Auckland"})
        three = three.groupby(["month", "district", "specialty", "group"], as_index=False)[["u120", "total"]].sum()
        three["L"] = 100 * (1 - three.u120 / three.total)
        rows.append(dict(analysis="treated = Auckland + Waitemata + Counties Manukau",
                         value=est(panel(three, "Auckland", CONTROLS, "MP", post))[0]))
        for grp, lab in [("Māori", "Maori only"), ("Pacific", "Pacific only")]:
            e = read_elective(vintage)
            for c in ("u120", "total"):
                e[c] = pd.to_numeric(e[c].replace("<5", 2.5))
            e = e[e.ethnicity.isin([grp, "European/Other"])].copy()
            e["month"] = pd.to_datetime(e.month)
            e["group"] = np.where(e.ethnicity == grp, "MP", "EO")
            e = e.groupby(["month", "district", "specialty", "group"], as_index=False)[["u120", "total"]].sum()
            e = e[e.total > 0]
            e["L"] = 100 * (1 - e.u120 / e.total)
            rows.append(dict(analysis=lab, value=est(panel(e, "Auckland", CONTROLS, "MP", post))[0]))
        for spec in ["General Surgery", "Orthopaedic Surgery", "Otorhinolaryngology (ENT)", "Gynaecology"]:
            rows.append(dict(analysis=f"specialty: {spec}", value=est(panel(g[g.specialty == spec], "Auckland", CONTROLS, "MP", post))[0]))
        rows.append(dict(analysis="specialty: all others", value=est(panel(g[~g.specialty.isin(["General Surgery", "Orthopaedic Surgery", "Otorhinolaryngology (ENT)", "Gynaecology"])], "Auckland", CONTROLS, "MP", post))[0]))
        # tool era split at the June 2023 halt
        q = panel(g, "Auckland", CONTROLS, "MP", post)
        tg = (q.district == "Auckland") & (q.group == "MP")
        q["tt1"] = (tg & (q.month >= TOOL[0]) & (q.month <= "2023-06-30")).astype(int)
        q["tt2"] = (tg & (q.month > "2023-06-30") & (q.month <= TOOL[1])).astype(int)
        m = pf.feols("L ~ tp + tt1 + tt2 | dsg + sm + dm + gm", data=q, weights="total", vcov={"CRV1": "district"})
        rows.append(dict(analysis="tool era Feb-Jun 2023 (pp)", value=float(m.coef()["tt1"])))
        rows.append(dict(analysis="tool era Jul 2023-Jul 2024 (pp)", value=float(m.coef()["tt2"])))
        # vintage revisions: primary beta by vintage (post truncated at each vintage's last month), pre-period L change
        base_pre = g[(g.month >= PRE[0]) & (g.month <= PRE[1])].set_index(["month", "district", "specialty", "group"]).L
        for vf in ["Waitlist-detail-extract.xlsx", "Waitlist-detail-extract-Q1-2025-26.xlsx", "waitlist-detail-extract-q2-25-26.xlsx",
                   "waitlist-detail-extract-q3-2025-26.xlsx"]:
            gv = load(vf)
            last = gv.month.max().strftime("%Y-%m-%d")
            bv = est(panel(gv, "Auckland", CONTROLS, "MP", (post[0], last)))[0]
            pv = gv[(gv.month >= PRE[0]) & (gv.month <= PRE[1])].set_index(["month", "district", "specialty", "group"]).L
            j = pd.concat([base_pre, pv], axis=1, join="inner")
            rows.append(dict(analysis=f"vintage {vf} (post to {last})", value=bv,
                             note=f"pre-period cells matched {len(j)}; mean |dL| {np.mean(np.abs(j.iloc[:, 0] - j.iloc[:, 1])):.2f} pp"))
        # event study
        q = panel(g, "Auckland", CONTROLS, "MP", post)
        tg = (q.district == "Auckland") & (q.group == "MP")
        months = sorted(q.month.unique())
        ref = pd.Timestamp(PRE[1])
        names = []
        for mth in months:
            if mth == ref:
                continue
            nm = "m" + pd.Timestamp(mth).strftime("%Y%m")
            q[nm] = (tg & (q.month == mth)).astype(int)
            names.append(nm)
        m = pf.feols("L ~ " + " + ".join(names) + " | dsg + sm + dm + gm", data=q, weights="total", vcov={"CRV1": "district"})
        ev = pd.DataFrame({"month": [pd.Timestamp(n[1:5] + "-" + n[5:7] + "-01") for n in names], "coef": m.coef().values})
        ev = pd.concat([ev, pd.DataFrame({"month": [pd.Timestamp("2023-01-01")], "coef": [0.0]})]).sort_values("month")
        pre_mean = ev[(ev.month >= "2021-07-01") & (ev.month <= "2023-01-31")].coef.mean()
        ev["coef"] = ev.coef - pre_mean  # relative to the pre-period mean (plan.md section 5)
        ev.to_csv(TAB / f"{label}_event.csv", index=False)
        fig, ax = plt.subplots(figsize=(8, 3.4))
        ax.plot(ev.month, ev.coef, ".-", color="#2f5d8a", ms=4, lw=0.8)
        ax.axhline(0, color="#888", lw=0.8)
        top = ax.get_ylim()[1]
        for (d_, lab_), yy in zip([("2023-02-01", "tool introduced"), ("2023-06-15", "rollout halted"), ("2024-08-01", "discontinued")],
                                  [top, top * 0.85, top]):
            ax.axvline(pd.Timestamp(d_), color="#b5443b", lw=0.8, ls="--")
            ax.text(pd.Timestamp(d_), yy, " " + lab_, fontsize=7, va="top", color="#b5443b")
        ax.set_ylabel("Auckland Maori+Pacific minus\nEuropean/Other long-wait gap,\nrelative to controls (pp)", fontsize=8)
        fig.tight_layout()
        fig.savefig(FIG / f"{label}_event.png", dpi=150)
    res = pd.DataFrame(rows)
    res.to_csv(TAB / f"{label}_main.csv", index=False)
    print(res.round(3).to_string(index=False))
    print(perm.sort_values("rank").round(2).to_string(index=False))


if __name__ == "__main__":
    main(*sys.argv[1:])
