"""How many substances have a 'Provisional Consent (Section 23)' application earlier than the linked T1 (which only
counts '^New .*Medicine Application' rows), and how many of those are funded / in the H1 and stage populations?"""
import sys, re
from pathlib import Path
import pandas as pd
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 60)
RUN = Path("/mnt/citations/research-lab/runs/future-health-nz-medicine-access-lag")
sys.path.insert(0, str(RUN/"code")); from link import has_any
d = pd.read_csv(RUN/"data/linked.csv", parse_dates=["t0","t1","t2","t3"]); d = d[~d.excluded_old]
A = pd.read_csv(RUN/"data/medsafe_applications.csv", dtype=str); A["ad"] = pd.to_datetime(A.application_date, dayfirst=True, errors="coerce")
rows = []
for r in d.itertuples():
    pats = str(r.match_names).split("|")
    a = A[A.substance.isin(pats) & A.ingredients.map(lambda x: has_any(pats, x))]
    prov = a[a.type.fillna("").str.contains("Provisional Consent")]
    if len(prov):
        first_prov = prov.ad.min()
        rows.append(dict(substance=r.substance, t0=r.t0.date(), t1=r.t1.date() if pd.notna(r.t1) else None, t2=r.t2.date() if pd.notna(r.t2) else None,
                         t3=r.t3.date() if pd.notna(r.t3) else None, first_prov_appl=first_prov.date(), prov_status=prov.status.iloc[0],
                         t1_earlier_by_days=int((r.t1 - first_prov).days) if pd.notna(r.t1) else None, funded=pd.notna(r.t3),
                         in_H1=bool(pd.notna(r.t3) and pd.notna(r.t2) and r.t0 <= r.t2 <= r.t3 and r.t0.year <= 2023)))
x = pd.DataFrame(rows); print(x.to_string(index=False))
print("\nsubstances with a provisional-consent application:", len(x), "; where it precedes the linked T1 (or T1 missing):", int(((x.t1_earlier_by_days.fillna(1) > 0)).sum()),
      "; funded:", int(x.funded.sum()), "; in H1 population:", int(x.in_H1.sum()))
# product status 'Provisional consent' rows: approval_date is the provisional consent date - check a couple of granted-then-full cases
P = pd.read_csv(RUN/"data/medsafe_products.csv", dtype=str)
for s in ["Zelboraf", "Tecentriq, Concentrate for infusion 1200", "Paxlovid", "Columvi", "Polivy", "Kadcyla", "Zinforo"]:
    print(P[P["product"].str.contains(s, na=False)][["approval_date", "notification_date", "status", "product"]].drop_duplicates().head(3).to_string(index=False, header=False))
