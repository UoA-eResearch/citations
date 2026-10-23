"""Confirmation pass: recompute H2, the guard, H1 and the pooled rates with an independent all-pairs Theil-Sen
(scipy.stats.theilslopes on time-sorted input), using the study's data loading (D7 tier preference) but not its
theil_sen(). Compares with results/tables/h1_h2.json and islet_rates.csv. Also re-runs the guard span scan the report
cites from the review, now with the correct estimator. Writes only confirm_recompute.out (via the caller)."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import theilslopes

RUN = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RUN / "code"))
import rates as R  # noqa: E402

P = lambda *a, **k: print(*a, flush=True, **k)
T = RUN / "results" / "tables"
inv = pd.read_csv(RUN / "data" / "inventory.csv").set_index("islet")
H = json.load(open(T / "h1_h2.json"))
rates = pd.read_csv(T / "islet_rates.csv")


def ts(t, y):
    o = np.argsort(t)
    return float(theilslopes(y[o], t[o])[0])


def tyr(d):
    return (d.time.dt.year + (d.time.dt.dayofyear - 1) / 365.25).to_numpy()


def rate(d, col, ref, min_span, min_n=20, constrain=False):
    d = d.dropna(subset=[col, "level_m"])
    if len(d) < min_n:
        return None
    t = tyr(d)
    if t.max() - t.min() < min_span:
        return None
    y, h = d[col].to_numpy(float), d.level_m.to_numpy(float)
    b = np.polyfit(h, y, 1)[0] if np.ptp(h) > 0 else 0.0
    if constrain:
        c0 = np.polyfit(h, y, 1)[1]; r = y - (b * h + c0)
        se = np.sqrt(r.var(ddof=2) / ((h - h.mean()) ** 2).sum())
        b = b if b < -2 * se else 0.0
    return {"rc": ts(t, 100 * (y - b * h) / ref), "ru": ts(t, 100 * y / ref), "n": len(d), "span": t.max() - t.min()}


def boot(df, col, by="atoll", B=2000, seed=7):
    rng = np.random.default_rng(seed)
    groups = [g[col].to_numpy() for _, g in df.groupby(by)]
    m = [np.mean(np.concatenate([g[rng.integers(0, len(g), len(g))] for g in groups])) for _ in range(B)]
    return [round(float(np.percentile(m, 2.5)), 3), round(float(np.percentile(m, 97.5)), 3)]


# --- equality of the fixed theil_sen with scipy on a random-order input
rng = np.random.default_rng(0)
t = rng.uniform(2017, 2026, 60); y = 3 * t + rng.normal(0, 5, 60)
P("fixed R.theil_sen vs scipy on shuffled input: %.6f vs %.6f; reversed-order input: %.6f" % (
    R.theil_sen(t, y), ts(t, y), R.theil_sen(t[::-1], y[::-1])))

a = R.attach_levels(R.load_areas())
a["year"] = a.time.dt.year
ls_ = pd.read_csv(T / "land_screen.csv").set_index("islet")
keep = set(ls_.index[ls_.retained])
a = a[a.islet.isin(keep)]
P("D7 tier preference: LC08 rows by tier after load_areas:", a[a.sensor == "LC08"].scene.str[-2:].value_counts().to_dict())
a_f, _ = R.gross_filter(a)
s2 = a_f[a_f.sensor == "s2"]
ne = inv.index[(inv.engineered == 0)]

# --- H2 and the pooled rates
rows = []
for islet, d in s2[s2.islet.isin(ne) & (s2.islet.map(inv.area_ha) >= 1)].groupby("islet"):
    ref = inv.area_ha[islet] * 1e4
    r = rate(d, "area_otsu", ref, 6.0)
    if r:
        rc2 = rate(d, "area_otsu", ref, 6.0, constrain=True)
        rows.append({"islet": islet, "atoll": inv.atoll[islet], "area_ha": inv.area_ha[islet], "rc": r["rc"], "ru": r["ru"],
                     "bias": abs(r["ru"] - r["rc"]), "signed": r["ru"] - r["rc"], "rc_con": rc2["rc"], "bias_con": abs(rc2["ru"] - rc2["rc"])})
Y = pd.DataFrame(rows)
P("\n=== H2 / E2 (independent): islets %d" % len(Y))
P("H2 mean |bias| %.3f CI %s   (study %.4f %s)" % (Y.bias.mean(), boot(Y, "bias"), H["H2"]["mean_abs_bias"], H["H2"]["ci"]))
P("mean signed bias %.3f (study %.4f)" % (Y.signed.mean(), H["H2"]["mean_signed_bias"]))
P("pooled corrected mean %.3f CI %s median %.3f; uncorrected mean %.3f CI %s" % (Y.rc.mean(), boot(Y, "rc"), Y.rc.median(), Y.ru.mean(), boot(Y, "ru")))
P("by atoll corrected mean:", Y.groupby("atoll").rc.mean().round(3).to_dict())
P("   study:", {k: v["mean_rate"] for k, v in H["by_atoll_E2"].items()})
P("by atoll mean signed / mean abs bias:", Y.groupby("atoll").agg(signed=("signed", "mean"), abs=("bias", "mean")).round(2).T.to_dict())
P(">= 5 ha only: n %d mean |bias| %.3f CI %s" % ((Y.area_ha >= 5).sum(), Y[Y.area_ha >= 5].bias.mean(), boot(Y[Y.area_ha >= 5], "bias")))
P("constrained slopes: mean |bias| %.3f CI %s; pooled rate %.3f" % (Y.bias_con.mean(), boot(Y, "bias_con"), Y.rc_con.mean()))
P("by size [1,5) / [5,20) / >=20 mean |bias|:", Y.groupby(pd.cut(Y.area_ha, [1, 5, 20, 1e9], right=False), observed=True).bias.mean().round(3).to_dict())
st = rates[(rates.family == "E2") & (rates.series == "area_otsu") & (rates.robust_slope == 0)].set_index("islet")
j = Y.set_index("islet").join(st[["rate_corr", "rate_uncorr"]])
P("per-islet agreement with islet_rates.csv: max |rc diff| %.5f, max |ru diff| %.5f" % ((j.rc - j.rate_corr).abs().max(), (j.ru - j.rate_uncorr).abs().max()))
# no gross filter
rows = []
s2n = a[a.sensor == "s2"]
for islet, d in s2n[s2n.islet.isin(Y.islet)].groupby("islet"):
    r = rate(d, "area_otsu", inv.area_ha[islet] * 1e4, 6.0)
    if r:
        rows.append({"atoll": inv.atoll[islet], "bias": abs(r["ru"] - r["rc"]), "rc": r["rc"]})
J = pd.DataFrame(rows)
P("without gross filter: H2 %.3f CI %s pooled %.3f" % (J.bias.mean(), boot(J, "bias"), J.rc.mean()))

# --- the guard (D7 rules: final tier via load_areas; Landsat restricted to each islet's S2 window)
first_s2 = s2.groupby("islet").time.min()
gl_all = a_f[(a_f.sensor == "LC08") & (a_f.year >= 2016) & (a_f.year <= 2021)]
gl_all = gl_all[gl_all.time >= gl_all.islet.map(first_s2)]
gs_all = s2[(s2.year >= 2016) & (s2.year <= 2021)]
cand = [i for i in keep if inv.engineered[i] == 0 and inv.area_ha[i] >= 5]


def guard(min_span, min_n=20, ls=gl_all):
    rows = []
    for islet in cand:
        ref = inv.area_ha[islet] * 1e4
        rl = rate(ls[ls.islet == islet], "area_otsu", ref, min_span, min_n)
        rs = rate(gs_all[gs_all.islet == islet], "area_otsu_30m", ref, min_span, min_n)
        if rl and rs:
            rows.append({"islet": islet, "atoll": inv.atoll[islet], "rate_ls": rl["rc"], "rate_s2": rs["rc"], "diff": rl["rc"] - rs["rc"],
                         "n_ls": rl["n"], "n_s2": rs["n"], "span_ls": round(rl["span"], 2), "span_s2": round(rs["span"], 2)})
    return pd.DataFrame(rows)


G = guard(4.5)
P("\n=== guard (independent, D7 rules): islets %d mean diff %.3f CI %s   (study %d, %.4f %s)" % (
    len(G), G["diff"].mean(), boot(G, "diff"), H["guard"]["islets"], H["guard"]["mean_diff"], H["guard"]["ci"]))
P(G.round(2).to_string(index=False))
P("by atoll:", G.groupby("atoll")["diff"].agg(["size", "mean"]).round(3).T.to_dict())
P("span scan with the fixed estimator (min 20 scenes):")
for sp in (3.0, 3.5, 4.0, 4.5, 5.0):
    g = guard(sp)
    P("  min_span %.1f: islets %d mean diff %s CI %s atolls %s" % (sp, len(g), round(g["diff"].mean(), 2) if len(g) else None,
                                                                  boot(g, "diff") if len(g) else None, g.atoll.value_counts().to_dict() if len(g) else {}))
# the guard under the pre-D7 Landsat rules (no window restriction) for reference
gl_old = a_f[(a_f.sensor == "LC08") & (a_f.year >= 2016) & (a_f.year <= 2021)]
g = guard(4.5, ls=gl_old)
P("without the S2-window restriction (tier preference kept): islets %d mean diff %.3f CI %s" % (len(g), g["diff"].mean(), boot(g, "diff")))

# --- H1
rows = []
e1d = a_f[a_f.sensor.isin(["LT05", "LE07", "LC08"]) & (a_f.year <= 2015)]
for islet in cand:
    ref = inv.area_ha[islet] * 1e4
    r1 = rate(e1d[e1d.islet == islet], "area_otsu", ref, 6.0)
    r2 = rate(s2[s2.islet == islet], "area_otsu", ref, 6.0)
    if r1 and r2:
        rows.append({"islet": islet, "atoll": inv.atoll[islet], "e1": r1["rc"], "e2": r2["rc"], "D": r2["rc"] - r1["rc"]})
X = pd.DataFrame(rows)
P("\n=== H1 (independent): islets %d atolls %d mean E1 %.3f mean E2 %.3f D %.3f CI %s   (study %d, D %.4f %s; E1 %.4f E2 %.4f)" % (
    len(X), X.atoll.nunique(), X.e1.mean(), X.e2.mean(), X.D.mean(), boot(X, "D"), H["H1"]["islets"], H["H1"]["D"], H["H1"]["ci"],
    H["H1"]["mean_rate_E1"], H["H1"]["mean_rate_E2"]))

# --- DEP correlations from the tables
dep = pd.read_csv(T / "dep_audit_islets.csv"); dep = dep[dep.dep_points >= 5].copy()
dep["late"] = 100 * dep.dep_late_m_yr * dep.perimeter_m / dep.area_m2
m = Y.merge(dep[["islet", "late"]], on="islet").dropna()
P("\nDEP late vs corrected r %.3f, vs uncorrected r %.3f, n %d" % (np.corrcoef(m.late, m.rc)[0, 1], np.corrcoef(m.late, m.ru)[0, 1], len(m)))
P("done")
