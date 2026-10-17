import pandas as pd, numpy as np, subprocess, io, sys, re
from pathlib import Path
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 70); pd.set_option("display.max_rows", 200)
RUN = Path("/mnt/citations/research-lab/runs/future-health-nz-medicine-access-lag")
c = pd.read_csv(RUN/"data/cohort.csv", parse_dates=["t0","fda_first","ema_first"])
d = pd.read_csv(RUN/"data/linked.csv", parse_dates=["t0","t1","t2","t3b","t3h","t3","t_prov","brand_t2","t_app","t_dec"])
print("cohort", len(c), c.t0_source.value_counts().to_dict(), "| excluded_old", int(d.excluded_old.sum()), "| analysed", int((~d.excluded_old).sum()), "| hml_first_edition", int(d.hml_first_edition.sum()))
print("HML-censored:", list(d[d.hml_first_edition].substance))
print("\n--- CBER-matched substances (cber_t0) ---")
exp = {"nonacog gamma":"2013-06-26","eftrenonacog alfa":"2014-03-28","efmoroctocog alfa":"2014-06-06","tisagenlecleucel":"2017-08-30","axicabtagene ciloleucel":"2017-10-18",
       "onasemnogene abeparvovec":"2019-05-24","voretigene neparvovec":"2017-12-19","andexanet alfa":"2018-05-03","vonicog alfa":"2015-12-08","idecabtagene vicleucel":"2021-03-26",
       "lisocabtagene maraleucel":"2021-02-05","brexucabtagene autoleucel":"2020-07-24","ciltacabtagene autoleucel":"2022-02-28","efanesoctocog alfa":"2023-02-23","eptacog beta":"2020-04-01",
       "susoctocog alfa":"2014-10-23","turoctocog alfa":"2013-10-15","lonoctocog alfa":"2016-05-25","damoctocog alfa pegol":"2018-08-30","albutrepenonacog alfa":"2016-03-04",
       "human coagulation factor x":"2015-10-20","talimogene laherparepvec":"2015-10-27","etranacogene dezaparvovec":"2022-11-22","exagamglogene autotemcel":"2023-12-08",
       "fidanacogene elaparvovec":"2024-04-26","turoctocog alfa pegol":"2019-02-19","radamts13":"2023-11-09","nonacog beta pegol":"2017-05-31","sipuleucel-t":"2010-04-29","rurioctocog alfa pegol":"2015-11-13"}
cb = c[c.cber_t0 == True][["substance","fda_first","fda_name","ema_first","t0","t0_source"]].copy()
cb["expected"] = cb.substance.map(exp); cb["ok"] = (cb.fda_first.dt.strftime("%Y-%m-%d") == cb.expected) | cb.expected.isna()
for col in ["fda_first","ema_first","t0"]: cb[col] = cb[col].dt.strftime("%Y-%m-%d")
print(cb.to_string(index=False)); print("mismatches vs reviewer expectations:", list(cb[~cb.ok].substance))
print("CBER date earlier than EMA (T0 moved):", int(((c.cber_t0==True) & (c.fda_first < c.ema_first.fillna(pd.Timestamp.max))).sum()))
# Purple Book semantics
pb = pd.read_csv(RUN/"data/raw/purplebook/purplebook.csv", skiprows=3, dtype=str, encoding="utf-8-sig")
print("\nPurple Book columns:", list(pb.columns)); print("Center counts:", pb.Center.value_counts().to_dict())
for b in ["KYMRIAH","ELOCTATE","PROVENGE","RIXUBIS","IXINITY","CORIFACT","ADSTILADRIN","RYPLAZIM","REBYOTA"]:
    h = pb[pb["Proprietary Name"].fillna("").str.upper().str.startswith(b)]
    print(f"  PB {b:11s} rows={len(h)} approval dates={sorted(h['Approval Date'].dropna().unique())[:4]} proper={list(h['Proper Name'].unique())[:1]} center={list(h.Center.unique())}")
print("trenonacog in cohort?", "trenonacog alfa" in set(c.substance), "| PB trenonacog rows:", int(pb["Proper Name"].fillna("").str.contains("trenonacog", case=False).sum()))
# CBER novel BLAs 2010-2024 not in cohort: list PB CBER proper names with first approval in window, not matched to any cohort name/brand
pbc = pb[pb.Center=="CBER"].copy(); pbc["date"] = pd.to_datetime(pbc["Approval Date"], format="mixed", errors="coerce")
first = pbc.groupby("Proper Name").agg(date=("date","min"), brand=("Proprietary Name","first")).reset_index()
first = first[(first.date >= "2010-01-01") & (first.date <= "2024-12-31")]
sys.path.insert(0, str(RUN/"code")); from names import norm
names = set(c.substance) | set("|".join(c.aliases.fillna("")).split("|")) | set(c.fda_name.fillna("").str.lower()) | set(c.ema_name.fillna("").str.lower().str.split().str[0])
brands_in = set(c.fda_name.fillna("").str.extract(r"CBER (\S+)")[0].dropna().str.lower()) | set(c.ema_name.fillna("").str.lower().str.split().str[0])
first["in_cohort"] = [ (norm(p) in names) or (str(b).lower().split()[0] in brands_in) for p, b in zip(first["Proper Name"], first.brand)]
miss = first[~first.in_cohort].sort_values("date")
print(f"\nPB CBER proper names first approved 2010-2024 not matched to the cohort: {len(miss)}")
print(miss[["date","brand","Proper Name"]].to_string(index=False))
# key rows
for s in ["dimethylfumarate","tenofovir alafenamide","plasminogen","remestemcel-l","trastuzumab emtansine","trastuzumab deruxtecan","nonacog gamma","eftrenonacog alfa","atezolizumab","vemurafenib","defibrotide","sipuleucel-t","fecal microbiota"]:
    r = d[d.substance==s]
    print(f"  {s:24s}", r[["t0","t0_source","t1","t2","t_prov","brand_t2","t3b","t3h","t3","hml_first_edition","excluded_old"]].to_string(index=False, header=False) if len(r) else "NOT IN LINKED")
# recompute H1 / stage
D = lambda a,b: (b-a).dt.days
x = d[~d.excluded_old].copy(); x.loc[x.t3 > "2026-10-01","t3"] = pd.NaT
pre = x[x.t0.dt.year<=2023]; f = pre[pre.t3.notna()]; cl = f[f.t2.notna() & (f.t0<=f.t2) & (f.t2<=f.t3)]
print(f"\nH1: pre {len(pre)} funded {len(f)} used {len(cl)}; share {D(cl.t0,cl.t2).sum()/D(cl.t0,cl.t3).sum():.4f}; median {D(cl.t0,cl.t3).median():.0f}; all funded median {D(f.t0,f.t3).median():.0f}")
st = cl[cl.t1.notna()].copy(); st["t1c"] = st[["t1","t0"]].max(axis=1); st = st[st.t1c<=st.t2]
print(f"stage n={len(st)}, early filers {(st.t1<st.t0).sum()}, medians {D(st.t0,st.t1c).median():.0f}/{D(st.t1c,st.t2).median():.0f}/{D(st.t2,st.t3).median():.0f}/{D(st.t0,st.t3).median():.0f}, shares {D(st.t0,st.t1c).sum()/D(st.t0,st.t3).sum():.3f}/{D(st.t1c,st.t2).sum()/D(st.t0,st.t3).sum():.3f}/{D(st.t2,st.t3).sum()/D(st.t0,st.t3).sum():.3f}")
pv = cl.copy(); pv["t2"] = pv[["t2","t_prov"]].min(axis=1); print(f"provisional bound: n_with_section23={int(cl.t_prov.notna().sum())} share {D(pv.t0,pv.t2).sum()/D(pv.t0,pv.t3).sum():.4f}")
print("H1 excluded:", "before consent", int((f.t2.notna()&(f.t3<f.t2)).sum()), "no consent", int(f.t2.isna().sum()), "consent<T0", list(f[f.t2.notna()&(f.t2<f.t0)].substance))
# frozen match names vs c0386fc linked
old = pd.read_csv(io.StringIO(subprocess.run(["git","show","c0386fc:research-lab/runs/future-health-nz-medicine-access-lag/results/tables/linked.csv"], cwd=RUN, capture_output=True, text=True).stdout))
mn = pd.read_csv(RUN/"results/forecast_2026_match_names.csv"); fc = pd.read_csv(RUN/"results/forecast_2026.csv")
m = mn.merge(old[["substance","match_names"]], on="substance", suffixes=("_frozen","_c0386fc"))
print(f"\nmatch-names file: {len(mn)} rows; substances == forecast file: {set(mn.substance)==set(fc.substance)}; equal to c0386fc match_names: {(m.match_names_frozen==m.match_names_c0386fc).all()}")
# forecast at-risk set now vs frozen
ar = x[x.t2.notna() & (x.t2<=pd.Timestamp('2026-10-01')) & x.t3.isna()]
print("at-risk now:", len(ar), "| in frozen but not at-risk now:", sorted(set(fc.substance)-set(ar.substance)), "| at-risk now but not frozen:", sorted(set(ar.substance)-set(fc.substance)))
