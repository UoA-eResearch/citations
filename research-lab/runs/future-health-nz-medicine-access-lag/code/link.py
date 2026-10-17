"""Link the cohort to Medsafe, PHARMAC and the PBS Medicine Status Website (plan section 4, D2). Writes data/linked.csv:
  T0  first FDA/EMA approval                 T1  first Medsafe new-medicine application (<= T2)
  T2  first Medsafe product approval         T3B / T3H  first community Schedule / HML edition listing it
  T3  min(T3B, T3H)                          T3_AU  first "Medicine listed on the PBS" date
  excluded_old  D2.2 (Medsafe consent or a PHARMAC listing more than a year before T0, or listed in the 2006 Schedule)
  T_app / T_dec  (D3) first PHARMAC funding application received / first decision recorded as an approval to fund,
                 from the UoA-eResearch/pharmac application tracker data; T_TGA (D3) earliest ARTG registration
Matching: the substance's normalised name as a whole-word sequence inside the normalised ingredient / chemical /
formulation / drug-name text."""
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from names import norm  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
CONSENTED = {"Consent given", "Approval lapsed", "Revoked", "Not available", "Provisional consent",
             "Not available - Provisional consent", "Consent suspended"}
NEW_APPL = re.compile(r"^New .*Medicine Application", re.I)


def has(sub, text):
    return bool(re.search(r"(?<![a-z0-9])" + re.escape(sub) + r"(?![a-z0-9])", norm(text) if isinstance(text, str) else ""))


def dmy(s):
    return pd.to_datetime(s, dayfirst=True, errors="coerce")


def main():
    c = pd.read_csv(RUN / "data" / "cohort.csv", parse_dates=["t0", "fda_first", "ema_first"])
    P = pd.read_csv(RUN / "data" / "medsafe_products.csv", dtype=str)
    A = pd.read_csv(RUN / "data" / "medsafe_applications.csv", dtype=str)
    L = pd.read_csv(RUN / "data" / "pharmac_listings.csv", dtype=str)
    L["ed"] = pd.to_datetime(L.edition)
    L["text"] = (L.chemical.fillna("") + " " + L.formulations.fillna("")).map(norm)
    first_ed = L[L.source == "schedule"].ed.min()
    W = pd.read_csv(RUN / "data" / "msw.csv", dtype=str) if (RUN / "data" / "msw.csv").exists() else pd.DataFrame(columns=["drug", "listed_date"])
    U = RUN / "data" / "raw" / "uoa_pharmac"
    APP = pd.read_csv(U / "pharmac_approvals.csv", dtype=str)
    APP["chem"] = APP.Chemical_Name__c.fillna("").map(norm)
    APP["received"] = pd.to_datetime(APP["Application Received date"], errors="coerce")
    APP["approved"] = [min((pd.Timestamp(d) for d, t in re.findall(r"(\d{4}-\d{2}-\d{2}):([^\n]*)", x)
                            if re.search(r"has been approved", t, re.I)), default=pd.NaT) if isinstance(x, str) else pd.NaT
                       for x in APP["Decision dates"]]
    TGA = pd.read_csv(U / "tga_artg.csv", dtype=str)
    TGA["text"] = TGA.Name.fillna("").map(norm)
    TGA["date"] = pd.to_datetime(TGA.RegistrationDate, errors="coerce")
    out = []
    for r in c.itertuples():
        s = r.substance
        p = P[(P.substance == s) & P.ingredients.map(lambda x: has(s, x)) & P.status.isin(CONSENTED)]
        t2 = dmy(p.approval_date).min() if len(p) else pd.NaT
        # consent ended: every consented product has lapsed or been revoked; dated by the latest notification
        ended = (dmy(p.notification_date).max() if len(p) and p.status.isin({"Approval lapsed", "Revoked"}).all()
                 else pd.NaT)
        a = A[(A.substance == s) & A.ingredients.map(lambda x: has(s, x)) & A.type.fillna("").str.match(NEW_APPL)]
        ad = dmy(a.application_date)
        t1 = ad[ad <= t2].min() if pd.notna(t2) else ad.min()
        pat = r"(?<![a-z0-9])" + re.escape(s) + r"(?![a-z0-9])"
        hit = L[L.text.str.contains(pat, regex=True)]
        b = hit[(hit.source == "schedule") & (hit.section == "B")].ed.min()
        h = hit[hit.source == "HML"].ed.min()
        t3 = min([x for x in (b, h) if pd.notna(x)], default=pd.NaT)
        w = W[W.drug.map(lambda x: has(s, x))]
        au = dmy(w.listed_date).min() if len(w) else pd.NaT
        pat_app = APP[APP.chem.str.contains(pat, regex=True)]
        t_app, t_dec = pat_app.received.min(), pat_app.approved.min()
        t_tga = TGA[TGA.text.str.contains(pat, regex=True)].date.min()
        old = ((pd.notna(t2) and t2 < r.t0 - pd.Timedelta(days=365)) or (pd.notna(b) and b <= first_ed)
               or (pd.notna(t3) and t3 < r.t0 - pd.Timedelta(days=365)))
        out.append(dict(substance=s, t0=r.t0, t0_source=r.t0_source, t1=t1, t2=t2, consent_ended=ended,
                        t3b=b, t3h=h, t3=t3, t3_au=au,
                        au_any_record=bool(len(w)), t_app=t_app, t_dec=t_dec, t_tga=t_tga, n_applications=len(pat_app), n_medsafe_products=len(p), n_listing_rows=len(hit),
                        ema_orphan=r.ema_orphan, atc=r.atc, fda_priority=r.fda_priority, excluded_old=bool(old)))
    d = pd.DataFrame(out)
    d.to_csv(RUN / "data" / "linked.csv", index=False)
    print(len(d), "substances;", int(d.excluded_old.sum()), "excluded as old;", "cutoff (last community edition):",
          L[L.source == "schedule"].ed.max().date(), "; last HML edition:", L[L.source == "HML"].ed.max().date())


if __name__ == "__main__":
    sys.exit(main())
