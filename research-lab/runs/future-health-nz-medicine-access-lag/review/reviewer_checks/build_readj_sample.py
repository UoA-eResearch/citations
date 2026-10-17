"""Reviewer re-adjudication sample: 40 from the agent's two validation samples (all with a present T2 or T3, plus flagged
rows, filled at random) + 30 new substances (seed 20261030; 20 with a present date, 10 absent). Writes richer evidence
files (adds the independent UoA Medsafe register snapshot, the PHARMAC application tracker, TGA and MSW rows) to
cache/evidence/ and the sample key to readjudication_sample.csv."""
import re, sys
from pathlib import Path
import pandas as pd
from rapidfuzz import fuzz
RUN = Path("/mnt/citations/research-lab/runs/future-health-nz-medicine-access-lag"); OUT = RUN/"review/reviewer_checks"
sys.path.insert(0, str(RUN/"code")); from names import norm; from link import has
d = pd.read_csv(RUN/"data/linked.csv")
v1 = pd.read_csv(RUN/"results/tables/link_validation.csv"); v2 = pd.read_csv(RUN/"results/tables/link_validation_v2.csv")
v = pd.concat([v1.assign(sample="v1"), v2.assign(sample="v2")]).merge(d[["substance","t1","t2","t3","excluded_old"]], on="substance")
present = v[(v.t2.notna() | v.t3.notna()) & ~v.excluded_old]
flagged = v[v.note.notna() & ~v.id.isin(present.id)]
rng = 20261030
pick = pd.concat([present, flagged]).drop_duplicates("id")
if len(pick) > 40: pick = pd.concat([present.sample(min(len(present), 32), random_state=rng), flagged]).drop_duplicates("id").head(40)
else: pick = pd.concat([pick, v[~v.id.isin(pick.id)].sample(40 - len(pick), random_state=rng)])
print("from validation samples:", len(pick), "(present dates:", int((pick.t2.notna() | pick.t3.notna()).sum()), ")")
rest = d[~d.substance.isin(v.substance) & ~d.excluded_old]
newp = rest[rest.t2.notna() | rest.t3.notna()].sample(20, random_state=rng); newa = rest[rest.t2.isna() & rest.t3.isna()].sample(10, random_state=rng)
new = pd.concat([newp, newa]).assign(sample="new", id=[f"n{i:03d}" for i in range(30)])
key = pd.concat([pick[["id","sample","substance"]], new[["id","sample","substance"]]]).reset_index(drop=True)
key.to_csv(OUT/"readjudication_sample.csv", index=False); print(len(key), "substances in reviewer sample")
# evidence
P = pd.read_csv(RUN/"data/medsafe_products.csv", dtype=str); A = pd.read_csv(RUN/"data/medsafe_applications.csv", dtype=str)
REG = pd.read_csv(RUN/"data/raw/uoa_pharmac/medsafe_register.csv", dtype=str); REG["n"] = REG["Active ingredients"].fillna("").map(norm)
L = pd.read_csv(RUN/"data/pharmac_listings.csv", dtype=str)
U = (L.assign(text=(L.chemical.fillna("") + " " + L.formulations.fillna(""))).groupby(["source","section","chemical"]).agg(first=("edition","min"), text=("text","first")).reset_index())
U["ntext"] = U.text.map(norm); U["nchem"] = U.chemical.fillna("").map(norm)
SU = pd.read_csv(RUN/"data/su_listings.csv", dtype=str); SU["n"] = SU.chemical.fillna("").map(norm)
APP = pd.read_csv(RUN/"data/raw/uoa_pharmac/pharmac_approvals.csv", dtype=str); APP["n"] = APP.Chemical_Name__c.fillna("").map(norm)
TGA = pd.read_csv(RUN/"data/raw/uoa_pharmac/tga_artg.csv", dtype=str); TGA["n"] = TGA.Name.fillna("").map(norm)
W = pd.read_csv(RUN/"data/msw.csv", dtype=str); W["n"] = W.drug.fillna("").map(norm)
SUT = [(t.stem, t.read_text()) for t in sorted((RUN/"data/su_text").glob("*.txt"))]
(OUT/"cache/evidence").mkdir(parents=True, exist_ok=True)
for r in key.merge(d, on="substance").itertuples():
    sub = r.substance; pats = str(r.match_names).split("|"); stem = min((p.split()[0] for p in pats), key=len)[:7]
    loose = re.compile(r"(?<![a-z])" + re.escape(stem))
    o = [f"SUBSTANCE: {sub}   T0 {r.t0} ({r.t0_source})   match names: {r.match_names}", f"LINKED: T1 {r.t1}  T2 {r.t2}  T3B {r.t3b}  T3H {r.t3h}  T3 {r.t3}  T3_AU {r.t3_au}  T_app {r.t_app}  T_TGA {r.t_tga}  excluded_old {r.excluded_old}", "",
         "MEDSAFE PRODUCTS from this study's crawl (+ passed filter; search term in brackets):"]
    for x in P[P.substance.isin(pats)].head(40).itertuples(): o.append(f"  {'+' if any(has(q, x.ingredients) for q in pats) else ' '} {x.approval_date:>11} | {x.status:28s} | {x.product[:70]} | {x.ingredients[:60]} [{x.term}]")
    o.append("MEDSAFE APPLICATIONS (all rows returned):")
    for x in A[A.substance.isin(pats)].head(40).itertuples(): o.append(f"  {'+' if any(has(q, x.ingredients) for q in pats) else ' '} {x.application_date:>11} | {x.status:12s} | {x.type[:40]:40s} | {str(x.change)[:50]:50s} | {x.product[:50]}")
    o.append(f"INDEPENDENT Medsafe register snapshot (UoA, 2026-03-30), loose match on '{stem}':")
    for x in REG[REG.n.str.contains(loose)].head(25).itertuples(): o.append(f"    {x._5:>11} | {x.Status:28s} | {x.Product[:70]} | {x._2[:60]}")
    pat = re.compile("|".join(r"(?<![a-z0-9])" + re.escape(q) + r"(?![a-z0-9])" for q in pats))
    hit = U[U.ntext.str.contains(pat)]; o.append("PHARMAC XML first editions (matched by the study rule):")
    o += [f"  {x.source:8} {x.section:3} {x.first} | {x.chemical} | {x.text[:80]}" for x in hit.itertuples()]
    near = U[~U.index.isin(hit.index)]; near = near[[fuzz.partial_ratio(sub, c) >= 85 or bool(loose.search(t)) for c, t in zip(near.nchem, near.ntext)]]
    o.append(f"PHARMAC near-miss (fuzzy>=85 on chemical, or loose '{stem}' in chemical+formulation; not matched):")
    o += [f"  {x.source:8} {x.section:3} {x.first} | {x.chemical} | {x.text[:80]}" for x in near.head(12).itertuples()]
    su = SU[SU.n.str.contains(loose)]; o.append(f"SCHEDULE UPDATE parsed new-listing rows, loose '{stem}': " + "; ".join(f"{x.effective} {x.chemical}" for x in su.head(8).itertuples()))
    first = next(((s, [l.strip()[:160] for l in t.splitlines() if re.search(r"(?i)(?<![a-z])" + re.escape(stem), l)][:4]) for s, t in SUT if re.search(r"(?i)(?<![a-z])" + re.escape(stem), t)), (None, []))
    o.append(f"SCHEDULE UPDATE PDF text, first file mentioning '{stem}': {first[0]}"); o += [f"  > {l}" for l in first[1]]
    ap = APP[APP.n.str.contains(loose)]; o.append("PHARMAC application tracker (UoA), loose match:")
    o += [f"  {str(x._12)[:10]} received | {x.Stage__c:22s} | {x.Chemical_Name__c[:50]} | {str(x.Brand_Name__c)[:30]}" for x in ap.head(8).itertuples()]
    tg = TGA[TGA.n.str.contains(loose)].copy(); tg["dt"] = pd.to_datetime(tg.RegistrationDate, errors="coerce"); tg = tg.sort_values("dt")
    o.append("TGA ARTG, loose match (earliest 5):"); o += [f"  {x.RegistrationDate} | {x.Name[:100]}" for x in tg.head(5).itertuples()]
    w = W[W.n.str.contains(loose)]; o.append("PBS MSW, loose match:"); o += [f"  listed {x.listed_date} | {x.drug[:60]} | {str(x.subtype)[:30]} | {str(x.meeting)[:25]}" for x in w.head(6).itertuples()]
    (OUT/"cache/evidence"/f"{r.id}.txt").write_text("\n".join(o) + "\n")
print("evidence written")
