import pandas as pd, numpy as np, re, sys
from pathlib import Path
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_colwidth", 70)
RUN = Path("/mnt/citations/research-lab/runs/future-health-nz-medicine-access-lag")
sys.path.insert(0, str(RUN/"code"))
from names import norm
L = pd.read_csv(RUN/"data/pharmac_listings.csv", dtype=str)
L["text"] = (L.chemical.fillna("")+" "+L.formulations.fillna("")).map(norm)
# what did 'dimethyl' match in HML 2013-10?
h = L[(L.source=="HML")&(L.edition=="2013-10-01")&L.text.str.contains(r"(?<![a-z0-9])dimethyl(?![a-z0-9])")]
print("HML 2013-10 'dimethyl' matches:"); print(h[["chemical","formulations"]].to_string())
for s in ["polidocanol","boceprevir","ticagrelor","defibrotide","para-aminosalicylic acid"]:
    h = L[(L.source=="HML")&(L.edition=="2013-10-01")&L.text.str.contains(r"(?<![a-z0-9])"+re.escape(s)+r"(?![a-z0-9])")]
    print(s, "->", list(h.chemical.unique()))
# community sections C, D, I: what are they? sample chemicals
for sec in ["C","D","I"]:
    g = L[(L.source=="schedule")&(L.section==sec)]
    print(f"\nsection {sec}: editions {g.edition.min()}..{g.edition.max()}, {g.chemical.nunique()} chemicals; sample:", list(g.chemical.drop_duplicates().head(12)))
# cohort substances whose first community appearance is in C/D/I before any B
d = pd.read_csv(RUN/"data/linked.csv", parse_dates=["t0","t1","t2","t3b","t3h","t3"])
d = d[~d.excluded_old]
U = L[L.source=="schedule"].copy(); U["ed"]=pd.to_datetime(U.edition)
rows=[]
for r in d.itertuples():
    pats = str(r.match_names).split("|")
    pat = "|".join(r"(?<![a-z0-9])"+re.escape(p)+r"(?![a-z0-9])" for p in pats)
    hit = U[U.text.str.contains(pat, regex=True)]
    if len(hit):
        nb = hit[hit.section!="B"]
        b = hit[hit.section=="B"].ed.min()
        if len(nb) and (pd.isna(b) or nb.ed.min() < b):
            rows.append(dict(substance=r.substance, t0=r.t0.date(), t2=r.t2, t3b=r.t3b, t3h=r.t3h, t3=r.t3, first_nonB=nb.ed.min().date(), nonB_sections=sorted(nb.section.unique()), chem=list(nb.chemical.unique())[:3]))
print("\ncohort substances with a non-B community listing before any B listing:", len(rows))
print(pd.DataFrame(rows).to_string())
