"""(1) SU gap-fill recall: chemicals new in Schedule_2026-01 vs Schedule_2024-05 should appear in SU rows effective Jun 2024-Dec 2025.
(2) Consented-in-NZ substances with no TGA match. (3) Provisional-consent cases with their Medsafe rows."""
import re, sys
from pathlib import Path
import pandas as pd
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 90); pd.set_option("display.max_rows", 300)
RUN = Path("/mnt/citations/research-lab/runs/future-health-nz-medicine-access-lag")
sys.path.insert(0, str(RUN/"code")); from names import norm; from link import has_any
L = pd.read_csv(RUN/"data/pharmac_listings.csv", dtype=str)
S = L[(L.source == "schedule") & (L.section == "B")]
pre = set(S[S.edition == "2024-05-01"].chemical.map(norm)); post = set(S[S.edition == "2026-01-01"].chemical.map(norm))
new = sorted(post - pre)
SU = pd.read_csv(RUN/"data/su_listings.csv", dtype=str); SU["eff"] = pd.to_datetime(SU.effective, errors="coerce")
G = SU[(SU.eff >= "2024-06-01") & (SU.eff < "2026-01-01")]; gtext = " || ".join(G.chemical.map(norm))
miss = [c for c in new if not re.search(r"(?<![a-z0-9])" + re.escape(c.split()[0]) + r"(?![a-z0-9])", gtext)]
print(f"(1) Section B chemicals present in 2026-01 but not 2024-05: {len(new)}; first word absent from SU gap rows: {len(miss)}")
print("   missing:", miss[:60])
print("   SU gap rows:", len(G), "; by month:", G.eff.dt.to_period("M").value_counts().sort_index().to_dict())
# same for the Jan 2018 gap
pre1 = set(S[S.edition == "2017-12-01"].chemical.map(norm)); post1 = set(S[S.edition == "2018-02-01"].chemical.map(norm))
new1 = sorted(post1 - pre1); G1 = SU[(SU.eff >= "2018-01-01") & (SU.eff < "2018-02-01")]
print(f"   Jan-2018 gap: new chemicals in 2018-02 vs 2017-12: {new1}; SU rows effective Jan 2018: {len(G1)} -> {list(G1.chemical)}")
# (2) TGA no-match among consented
d = pd.read_csv(RUN/"data/linked.csv", parse_dates=["t0","t2","t3","t_tga"]); d = d[~d.excluded_old]
nm = d[d.t2.notna() & d.t_tga.isna()]
print(f"\n(2) consented in NZ (n={int(d.t2.notna().sum())}) but no TGA match: {len(nm)}"); print(nm[["substance","t0","t2","t3","match_names"]].to_string(index=False))
T = pd.read_csv(RUN/"data/raw/uoa_pharmac/tga_artg.csv", dtype=str); T["text"] = T.Name.fillna("").map(norm)
for s in ["semaglutide", "nusinersen", "risdiplam", "tezacaftor", "elexacaftor", "ivacaftor", "pembrolizumab", "nivolumab", "sofosbuvir", "osimertinib", "venetoclax", "secukinumab", "dolutegravir", "ticagrelor"]:
    hit = T[T.text.str.contains(r"(?<![a-z0-9])" + re.escape(s) + r"(?![a-z0-9])")].copy(); hit["dt"] = pd.to_datetime(hit.RegistrationDate, errors="coerce")
    e = hit.sort_values("dt").head(1)
    print(f"   TGA {s:14s} n={len(hit):3d} earliest {e.dt.iloc[0].date() if len(e) else None} | {e.Name.iloc[0][:90] if len(e) else ''}")
# (3) provisional cases
P = pd.read_csv(RUN/"data/medsafe_products.csv", dtype=str); A = pd.read_csv(RUN/"data/medsafe_applications.csv", dtype=str)
print("\n(3) provisional-route substances (status or application text mentions Provisional):")
for r in d[d.t2.notna()].itertuples():
    pats = str(r.match_names).split("|")
    p = P[P.substance.isin(pats) & P.ingredients.map(lambda x: has_any(pats, x))]; a = A[A.substance.isin(pats) & A.ingredients.map(lambda x: has_any(pats, x))]
    pm = p.status.str.contains("Provisional", na=False); am = a.type.str.contains("Provisional", na=False) | a.change.str.contains("Provisional", na=False)
    if pm.any() or am.any():
        print(f"  {r.substance:28s} T0 {r.t0.date()} T2 {r.t2.date()} T3 {r.t3.date() if pd.notna(r.t3) else '-'}")
        for x in p[pm | p.status.notna()].drop_duplicates("product").head(4).itertuples(): print(f"      P {x.approval_date:>11} | {x.status:35s} | {x.product[:60]}")
        for x in a[am].drop_duplicates("product").head(4).itertuples(): print(f"      A {x.application_date:>11} | {x.type[:45]:45s} | {str(x.change)[:60]} | {x.product[:50]}")
