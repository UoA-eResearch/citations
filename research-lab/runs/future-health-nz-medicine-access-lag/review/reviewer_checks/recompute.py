"""Reviewer recomputation of H1a/H1b/stage/H3 with sensitivities. Read-only on study data; writes only to stdout."""
import json, sys, re
from pathlib import Path
import numpy as np, pandas as pd
from lifelines import KaplanMeierFitter
RUN = Path("/mnt/citations/research-lab/runs/future-health-nz-medicine-access-lag")
NB, SEED = 2000, 20261020
D = lambda a, b: (b - a).dt.days
def load():
    d = pd.read_csv(RUN/"data/linked.csv", parse_dates=["t0","t1","t2","t3b","t3h","t3","t3_au","consent_ended","t_app","t_dec","t_tga"])
    cutoff = pd.Timestamp("2026-10-01")
    d = d[~d.excluded_old].copy(); d.loc[d.t3 > cutoff, "t3"] = pd.NaT
    return d, cutoff
def boot(df, fn, seed=SEED):
    rng = np.random.default_rng(seed)
    v = [fn(df.iloc[rng.integers(0, len(df), len(df))]) for _ in range(NB)]
    v = [x for x in v if x is not None and np.isfinite(x)]
    return [round(float(np.percentile(v, 2.5)),3), round(float(np.percentile(v, 97.5)),3)]
share = lambda x: float(D(x.t0, x.t2).sum() / D(x.t0, x.t3).sum()) if len(x) else None
med = lambda x: float(D(x.t0, x.t3).median()) if len(x) else None
def h1(label, clean):
    s = share(clean); m = med(clean)
    print(f"{label:70s} n={len(clean):3d} share={s:.3f} CI={boot(clean, share)} median_per_sub={float((D(clean.t0,clean.t2)/D(clean.t0,clean.t3).clip(lower=1)).median()):.3f} | H1b median={m:.0f} CI={boot(clean, med)}")
d, cutoff = load()
pre = d[d.t0.dt.year <= 2023]; funded = pre[pre.t3.notna()]
clean = funded[funded.t2.notna() & (funded.t0 <= funded.t2) & (funded.t2 <= funded.t3)].copy()
print("== H1 as reported"); h1("as reported (74)", clean)
# S1: include the 13 excluded with clipping (T2 clipped into [T0, T3]); funded-without-consent cannot be included
x = funded[funded.t2.notna()].copy(); x["t2"] = x.t2.clip(lower=x.t0, upper=x.t3)
h1("S1 include funded-before-consent (share=1) and consent-before-T0 (share=0)", x)
x2 = funded[funded.t2.notna() & (funded.t0 <= funded.t2)].copy(); x2["t2"] = x2.t2.clip(upper=x2.t3)
h1("S1b include funded-before-consent only (share=1)", x2)
x3 = funded[funded.t2.notna() & (funded.t2 <= funded.t3)].copy(); x3["t2"] = x3.t2.clip(lower=x3.t0)
h1("S1c include consent-before-T0 only (share=0)", x3)
# S2: reviewer corrections (see review.md): T0 from FDA for CBER / unmerged duplicates; dimethyl false HML match; old substances dropped
fix = d.copy()
T0 = {"trastuzumab emtansine": "2013-02-22", "trastuzumab deruxtecan": "2019-12-20", "nonacog gamma": "2013-06-26", "eftrenonacog alfa": "2014-03-28",
      "efmoroctocog alfa": "2014-06-06", "tisagenlecleucel": "2017-08-30", "axicabtagene ciloleucel": "2017-10-18", "onasemnogene abeparvovec": "2019-05-24",
      "voretigene neparvovec": "2017-12-19", "andexanet alfa": "2018-05-03", "vonicog alfa": "2015-12-08", "fampridine": "2010-01-22",
      "lutetium vipivotide tetraxetan": "2022-03-23", "idecabtagene vicleucel": "2021-03-26", "lisocabtagene maraleucel": "2021-02-05",
      "brexucabtagene autoleucel": "2020-07-24", "ciltacabtagene autoleucel": "2022-02-28", "efanesoctocog alfa": "2023-02-23", "eptacog beta": "2020-04-01",
      "susoctocog alfa": "2014-10-23", "turoctocog alfa": "2013-10-15", "lonoctocog alfa": "2016-05-25", "damoctocog alfa pegol": "2018-08-30",
      "albutrepenonacog alfa": "2016-03-04", "human coagulation factor x": "2015-10-20", "talimogene laherparepvec": "2015-10-27",
      "etranacogene dezaparvovec": "2022-11-22", "exagamglogene autotemcel": "2023-12-08", "fidanacogene elaparvovec": "2024-04-26",
      "turoctocog alfa pegol": "2019-02-19", "radamts13": "2023-11-09", "nonacog beta pegol": "2017-05-31", "voxilaprevi": "2017-07-18"}
for k, v in T0.items():
    fix.loc[fix.substance == k, "t0"] = pd.Timestamp(v)
fix.loc[fix.substance == "dimethyl", ["t3h", "t3"]] = [pd.NaT, pd.Timestamp("2016-02-01")]   # HML 2013-10 hit was dimethyl sulfoxide
drop = {"para-aminosalicylic acid", "polidocanol", "pancreas powder", "human coagulation factor viii", "human von willebrand factor", "alpha1-proteinase inhibitor",
        "c1 inhibitor", "chlormethine", "acetylsalicylic acid", "ado-trastuzumab emtansine", "fam-trastuzumab deruxtecan", "lutetium lu-177 vipivotide tetraxetan",
        "dalfampridine", "voxilaprevir", "ezogabine", "autologous peripheral-blood mononuclear cells activated", "prostatic acid phosphatase granulocyte-macrophage colony-stimulating factor"}
fix = fix[~fix.substance.isin(drop)]
pre2 = fix[fix.t0.dt.year <= 2023]; funded2 = pre2[pre2.t3.notna()]
clean2 = funded2[funded2.t2.notna() & (funded2.t0 <= funded2.t2) & (funded2.t2 <= funded2.t3)].copy()
print("\n== S2 reviewer corrections"); h1("S2 corrected T0/T3, old entries dropped", clean2)
print("   joined:", sorted(set(clean2.substance) - set(clean.substance)), " left:", sorted(set(clean.substance) - set(clean2.substance)))
print("   funded 2010-23 after corrections:", len(funded2), "| excluded: before-consent", int((funded2.t2.notna() & (funded2.t3 < funded2.t2)).sum()),
      "no-consent", int(funded2.t2.isna().sum()), "consent<T0", int((funded2.t2.notna() & (funded2.t2 < funded2.t0)).sum()))
# S3: provisional consent lower bound: for funded substances with a provisional route, set T2 = T1 (earliest conceivable consent)
P = pd.read_csv(RUN/"data/medsafe_products.csv", dtype=str); A = pd.read_csv(RUN/"data/medsafe_applications.csv", dtype=str)
sys.path.insert(0, str(RUN/"code")); from link import has_any
prov = set()
for r in d[d.t2.notna()].itertuples():
    pats = str(r.match_names).split("|")
    p = P[P.substance.isin(pats) & P.ingredients.map(lambda x: has_any(pats, x))]; a = A[A.substance.isin(pats) & A.ingredients.map(lambda x: has_any(pats, x))]
    if p.status.str.contains("Provisional", na=False).any() or a.type.str.contains("Provisional", na=False).any() or a.change.str.contains("Provisional", na=False).any():
        prov.add(r.substance)
print("\n== provisional route:", len(prov), sorted(prov))
pf = clean[clean.substance.isin(prov)]
print("   in H1 population:", list(pf.substance), "| funded 2010-23 with provisional route:", list(funded[funded.substance.isin(prov)].substance))
x = clean.copy(); m = x.substance.isin(prov) & x.t1.notna(); x.loc[m, "t2"] = x.loc[m, "t1"]
h1("S3 provisional: T2 := T1 for provisional-route substances (lower bound)", x)
# stage split: as reported and with T1 < T0 included (sponsor delay clipped at 0)
st = d[d.t3.notna() & d.t1.notna() & d.t2.notna() & (d.t0.dt.year <= 2023)]
st_rep = st[(st.t0 <= st.t1) & (st.t1 <= st.t2) & (st.t2 <= st.t3)]
def stage(g, label):
    a, b, c_ = D(g.t0, g.t1).clip(lower=0), D(g.t1.clip(lower=g.t0), g.t2), D(g.t2, g.t3); tot = D(g.t0, g.t3)
    print(f"{label:60s} n={len(g)} medians sponsor={a.median():.0f} medsafe={b.median():.0f} funding={c_.median():.0f} total={tot.median():.0f} | shares {a.sum()/tot.sum():.3f} {b.sum()/tot.sum():.3f} {c_.sum()/tot.sum():.3f} | T0->T2 share {(a.sum()+b.sum())/tot.sum():.3f}")
print("\n== stage split"); stage(st_rep, "as reported (T0<=T1 required)")
st_all = st[(st.t1 <= st.t2) & (st.t2 <= st.t3) & (st.t0 <= st.t2)]
stage(st_all, "T1<T0 included, sponsor delay clipped at 0")
print("   substances with T1<T0 among funded 2010-23 with T1,T2 and T0<=T2<=T3:", int((st_all.t1 < st_all.t0).sum()))
stage(st_all[st_all.t0.dt.year <= 2014], "  2010-14 incl. early filers"); stage(st_all[(st_all.t0.dt.year >= 2015) & (st_all.t0.dt.year <= 2019)], "  2015-19 incl. early filers")
# Medsafe share among the 74 (H1 population) by imputing: Medsafe review = T2 - max(T0,T1) where T1 known
g = clean[clean.t1.notna()].copy()
print(f"   of the 74 H1 substances, {len(g)} have T1; Medsafe review share there = {D(g.t1.clip(lower=g.t0), g.t2).sum()/D(g.t0,g.t3).sum():.3f}, sponsor share {D(g.t0,g.t1).clip(lower=0).sum()/D(g.t0,g.t3).sum():.3f}, T0->T2 share {D(g.t0,g.t2).sum()/D(g.t0,g.t3).sum():.3f}")
# H3 and horizon sensitivity
c2 = d[d.t2.notna()].copy(); c2 = c2[~(c2.t3.notna() & (c2.t3 < c2.t2))]; f2 = c2[c2.t3.notna()]
dur = D(c2.t2, c2.t3.fillna(cutoff)).clip(lower=0); ev = c2.t3.notna()
k = KaplanMeierFitter().fit(dur, ev)
yrs = lambda v: v/365.25
print("\n== H3"); print(f"funded-only n={len(f2)} mean={yrs(D(f2.t2,f2.t3).mean()):.2f} median={yrs(D(f2.t2,f2.t3).median()):.2f}; consented n={len(c2)} events={int(ev.sum())} KM median={yrs(k.median_survival_time_):.2f}")
for tau in (5, 7.7, 8, 10, 12, 13):
    rm = float(np.trapz(k.survival_function_at_times(np.arange(0, int(tau*365.25)+1)).values, dx=1))
    print(f"   RMST to {tau:>4} y = {yrs(rm):.2f} y   (max follow-up {yrs(dur.max()):.1f} y; S at tau = {float(k.survival_function_at_times(int(tau*365.25)).iloc[0]):.3f})")
# funded-only mean restricted to T0 2010-2023 and to those consented before 2016 (10+ years follow-up), as a check on the survivor framing
old = c2[c2.t2 <= pd.Timestamp("2016-10-01")]
print(f"   consented before Oct 2016 (>=10 y follow-up): n={len(old)}, funded {int(old.t3.notna().sum())}, funded-only mean {yrs(D(old[old.t3.notna()].t2, old[old.t3.notna()].t3).mean()):.2f} y")
# H3 verdict logic
print("   plan rule: Supported only if funded-only within 7.7±1 AND no censoring-aware hit. funded hit:", any(abs(v-7.7)<=1 for v in (yrs(D(f2.t2,f2.t3).mean()), yrs(D(f2.t2,f2.t3).median()))))
# counts for the report
print("\n== counts"); print("cohort 680; T0 2010-23:", len(pre), "funded:", len(funded), "consented:", int(d.t2.notna().sum()), "funded all:", int(d.t3.notna().sum()))
print("funded with t3 == 2013-10-01 (HML start):", list(d[d.t3 == "2013-10-01"].substance))
print("2024 cohort:", int((d.t0.dt.year == 2024).sum()), "consented", int(((d.t0.dt.year == 2024) & d.t2.notna()).sum()), "funded", int(((d.t0.dt.year == 2024) & d.t3.notna()).sum()))
# D4 effect: did any SU gap listing set T3 earlier than the HML?
gap = d[((d.t3b >= "2018-01-01") & (d.t3b < "2018-02-01")) | ((d.t3b >= "2024-06-01") & (d.t3b < "2026-01-01"))]
print("gap-window T3B rows:", len(gap), "; rows where T3B < T3H (gap fill changed T3):", int((gap.t3b < gap.t3h.fillna(pd.Timestamp.max)).sum()))
