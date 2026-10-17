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


GENERIC_FIRST = {"allogeneic", "angiotensin", "concentrate", "enriched", "matrix-applied", "spheroids", "prostatic", "retroviral",
                 "oestrogens", "uridine", "alpha1-proteinase", "pancreas", "acetylsalicylic"}   # D6: not INN stems


def patterns(s, aliases, old_tokens, cohort_names=frozenset(), first_counts=None):
    """D6: match the canonical name or any alias; also the first word alone when the name has several words, the first
    word has >= 7 letters, no substance first approved before 2010 starts with that word, the word is not itself another
    cohort substance, and no other cohort substance starts with it (so 'polatuzumab vedotin' matches Medsafe's
    'Polatuzumab', but 'aripiprazole lauroxil' never matches Abilify's 'Aripiprazole'). Canonical names only."""
    names = sorted(set(aliases.split("|")) | {s}) if isinstance(aliases, str) else [s]
    out = list(names)
    w = s.split()                       # the canonical name only, never an alias's first word
    if (len(w) > 1 and len(w[0]) >= 7 and w[0] not in old_tokens and w[0] not in cohort_names and w[0] not in GENERIC_FIRST
            and (first_counts or {}).get(w[0], 1) == 1):
        out.append(w[0])
    return sorted(set(out))


def has_any(pats, text):
    return any(has(p, text) for p in pats)


def main():
    c = pd.read_csv(RUN / "data" / "cohort.csv", parse_dates=["t0", "fda_first", "ema_first"])
    allf = pd.read_csv(RUN / "data" / "all_first_approvals.csv", index_col=0, parse_dates=["first"])
    old_tokens = {k.split()[0] for k, v in allf["first"].items() if pd.notna(v) and v < pd.Timestamp("2010-01-01") and isinstance(k, str) and k}
    cohort_names = set(c.substance)
    first_counts = c.substance.str.split().str[0].value_counts().to_dict()
    P = pd.read_csv(RUN / "data" / "medsafe_products.csv", dtype=str)
    A = pd.read_csv(RUN / "data" / "medsafe_applications.csv", dtype=str)
    L = pd.read_csv(RUN / "data" / "pharmac_listings.csv", dtype=str)
    L["ed"] = pd.to_datetime(L.edition)
    L["text"] = (L.chemical.fillna("") + " " + L.formulations.fillna("")).map(norm)
    first_ed = L[L.source == "schedule"].ed.min()
    # D4: the community-Schedule XML archive has no editions for Jan 2018 or Jun 2024 - Dec 2025; new listings
    # effective in those windows come from the Schedule Update PDFs (code/su_listings.py)
    SU = pd.read_csv(RUN / "data" / "su_listings.csv", dtype=str)
    SU["eff"] = pd.to_datetime(SU.effective, errors="coerce")
    SU = SU[((SU.eff >= "2018-01-01") & (SU.eff < "2018-02-01")) | ((SU.eff >= "2024-06-01") & (SU.eff < "2026-01-01"))].copy()
    SU["text"] = SU.chemical.map(norm)
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
        pats = patterns(s, r.aliases, old_tokens, cohort_names - {s}, first_counts)
        names = set(str(r.aliases).split("|")) | {s}
        p = P[P.substance.isin(names) & P.ingredients.map(lambda x: has_any(pats, x)) & P.status.isin(CONSENTED)]
        t2 = dmy(p.approval_date).min() if len(p) else pd.NaT
        # consent ended: every consented product has lapsed or been revoked; dated by the latest notification
        ended = (dmy(p.notification_date).max() if len(p) and p.status.isin({"Approval lapsed", "Revoked"}).all()
                 else pd.NaT)
        a = A[A.substance.isin(names) & A.ingredients.map(lambda x: has_any(pats, x)) & A.type.fillna("").str.match(NEW_APPL)]
        ad = dmy(a.application_date)
        t1 = ad[ad <= t2].min() if pd.notna(t2) else ad.min()
        pat = "|".join(r"(?<![a-z0-9])" + re.escape(x) + r"(?![a-z0-9])" for x in pats)
        hit = L[L.text.str.contains(pat, regex=True)]
        b = hit[(hit.source == "schedule") & (hit.section == "B")].ed.min()
        b_su = SU[SU.text.str.contains(pat, regex=True)].eff.min()
        if pd.notna(b_su) and (pd.isna(b) or b_su < b):
            b = b_su
        h = hit[hit.source == "HML"].ed.min()
        t3 = min([x for x in (b, h) if pd.notna(x)], default=pd.NaT)
        w = W[W.drug.map(lambda x: has_any(pats, x))]
        au = dmy(w.listed_date).min() if len(w) else pd.NaT
        pat_app = APP[APP.chem.str.contains(pat, regex=True)]
        t_app, t_dec = pat_app.received.min(), pat_app.approved.min()
        t_tga = TGA[TGA.text.str.contains(pat, regex=True)].date.min()
        old = ((pd.notna(t2) and t2 < r.t0 - pd.Timedelta(days=365)) or (pd.notna(b) and b <= first_ed)
               or (pd.notna(t3) and t3 < r.t0 - pd.Timedelta(days=365)))
        out.append(dict(substance=s, match_names="|".join(pats), t0=r.t0, t0_source=r.t0_source, t1=t1, t2=t2, consent_ended=ended,
                        t3b=b, t3h=h, t3=t3, t3_au=au,
                        au_any_record=bool(len(w)), t_app=t_app, t_dec=t_dec, t_tga=t_tga, n_applications=len(pat_app), n_medsafe_products=len(p), n_listing_rows=len(hit),
                        ema_orphan=r.ema_orphan, atc=r.atc, fda_priority=r.fda_priority, excluded_old=bool(old)))
    d = pd.DataFrame(out)
    d.to_csv(RUN / "data" / "linked.csv", index=False)
    print(len(d), "substances;", int(d.excluded_old.sum()), "excluded as old;", "cutoff (last community edition):",
          L[L.source == "schedule"].ed.max().date(), "; last HML edition:", L[L.source == "HML"].ed.max().date())


if __name__ == "__main__":
    sys.exit(main())
