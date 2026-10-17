"""New-active-substance cohort (plan section 3): substances whose FIRST approval anywhere in the FDA (Drugs@FDA, any
application type) or the EU (EMA centralised, non-generic non-biosimilar human medicines) falls in 2010-2024.
T0 = the earlier of the two first approvals. Diagnostics, vaccines and allergens are excluded. Writes
data/cohort.csv (substance, t0, t0_source, fda_first, ema_first, ema_orphan, atc, fda_priority, n_fda_appl)."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from names import DIAG_RE, components, norm  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
R = RUN / "data" / "raw"
LO, HI = pd.Timestamp("2010-01-01"), pd.Timestamp("2024-12-31")
# D5: not new active substances, found when Medsafe searches failed on them
EXCLUDE = {s: "subcutaneous co-formulation of an existing antibody with hyaluronidase" for s in (
               "atezolizumab and hyaluronidase", "daratumumab and hyaluronidase", "efgartigimod alfa and hyaluronidase",
               "ocrelizumab and hyaluronidase", "pertuzumab trastuzumab and hyaluronidase", "trastuzumab and hyaluronidase")}
# D6: one substance under FDA and EMA name variants (salts, esters, moiety vs prodrug, combination strings, a typo)
ALIAS = {"afatinib dimaleate": "afatinib", "cabozantinib s": "cabozantinib", "elexacaftor ivacaftor tezacaftor": "elexacaftor",
         "ivacaftor tezacaftor": "tezacaftor", "lutetium lu-177 dotatate": "lutetium oxodotreotide",
         "ombitasvir paritaprevir ritonavir": "ombitasvir", "pasireotide diaspartate": "pasireotide", "patiromer sorbitex": "patiromer",
         "rucaparib camsylate": "rucaparib", "trametinib dimethyl sulfoxide": "trametinib", "vilanterol trifenatate": "vilanterol",
         "isavuconazonium": "isavuconazole", "ledispavir": "ledipasvir", "azilsartan kamedoxomil": "azilsartan medoxomil",
         "telotristat etiprate": "telotristat ethyl", "radium ra-223 dichloride": "radium ra223 dichloride",
         # D8 (review issue 5): more FDA/EMA variants, and multi-component products counted once
         "ado-trastuzumab emtansine": "trastuzumab emtansine", "fam-trastuzumab deruxtecan": "trastuzumab deruxtecan",
         "lutetium lu-177 vipivotide tetraxetan": "lutetium vipivotide tetraxetan", "dalfampridine": "fampridine",
         "ezogabine": "retigabine", "voxilaprevi": "voxilaprevir", "birch triterpenes": "birch bark extract",
         "autologous peripheral-blood mononuclear cells activated": "sipuleucel-t",
         "prostatic acid phosphatase granulocyte-macrophage colony-stimulating factor": "sipuleucel-t",
         "a retroviral vector encoding for a truncated form of the human low affinity nerve growth factor receptor": "allogeneic t cells genetically modified",
         "the herpes simplex i virus thymidine kinase": "allogeneic t cells genetically modified",
         "cells transduced": "autologous cd34", "enriched cell fraction that contains cd34": "autologous cd34",
         "retroviral vector that encodes for the human ada cdna sequence": "autologous cd34",
         "oteracil": "gimeracil", "piperaquine tetraphosphate": "artenimol"}
# D8: CBER biologics are absent from Drugs@FDA; their first US licensure comes from the FDA Purple Book (CBER rows),
# matched by proper name, by brand, or by this map where the US and EU brands differ (dates always from the file)
CBER_BRAND = {"nonacog beta pegol": "rebinyn", "efmoroctocog alfa": "eloctate", "efanesoctocog alfa": "altuviiio",
              "eptacog beta": "sevenfact", "vonicog alfa": "vonvendi", "andexanet alfa": "andexxa",
              "fidanacogene elaparvovec": "beqvez", "rurioctocog alfa pegol": "adynovate"}
# D8: CBER-only new active substances (never EMA-approved, or EMA-approved after 2024), absent from both of the
# plan's sources. Rule: CBER 351(a) licence first granted 2010-2024 to a concept no earlier product had; vaccines,
# allergen extracts, diagnostics, antivenoms, cord blood, immune globulins and plasma products of established concepts
# are out, as for the rest of the cohort. Canonical name -> Purple Book proper-name stems (suffix removed); dates from
# the file. Two faecal microbiota products count once.
CBER_ONLY = {"acellular tissue engineered vessel": ["acellular tissue engineered vessel"],
             "afamitresgene autoleucel": ["afamitresgene autoleucel"],
             "allogeneic cultured keratinocytes and dermal fibroblasts in murine collagen":
                 ["allogeneic cultured keratinocytes and dermal fibroblasts in murine collagen"],
             "allogeneic cultured keratinocytes and fibroblasts in bovine collagen":
                 ["allogeneic cultured keratinocytes and fibroblasts in bovine collagen"],
             "allogeneic processed thymus tissue": ["allogeneic processed thymus tissue"], "azficel-t": ["azficel-t"],
             "donislecel": ["donislecel"], "omidubicel": ["omidubicel"], "remestemcel-l": ["remestemcel-l"],
             "lifileucel": ["lifileucel"], "delandistrogene moxeparvovec": ["delandistrogene moxeparvovec"],
             "lovotibeglogene autotemcel": ["lovotibeglogene autotemcel"],
             "fecal microbiota": ["fecal microbiota, live", "fecal microbiota spores, live"], "plasminogen": ["plasminogen, human"]}
CBER_ONLY_ALIAS = {"fecal microbiota": {"faecal microbiota"}}
# D6: FDA approvals under a proper or brand name the INN match cannot see
T0_OVERRIDE = {"rurioctocog alfa pegol": ("2015-11-13", "FDA Adynovate, proper name antihemophilic factor (recombinant), pegylated"),
               "sucroferric oxyhydroxide": ("2013-11-27", "FDA Velphoro, listed as ferric oxyhydroxide")}
EXCLUDE.update({"hydrogen": "salt-stripping artefact of potassium hydrogen carbonate (Sibnayal)",
                "air polymer a": "diagnostic ultrasound contrast agent (ExEm Foam)",
                "brilliant blue g": "surgical stain (TissueBlue)",
                "gemtuzumab ozogamicin": "first FDA approval 2000 (Mylotarg; withdrawn 2010, re-approved 2017) - not new in 2010-2024",
                # D8 (review issue 5): old substance concepts under new names, and diagnostics or precursors
                "asparaginase erwinia chrysanthemi": "Erwinia asparaginase in use since the 1980s (Erwinase)",
                "crisantaspase": "Erwinia asparaginase in use since the 1980s (Erwinase)",
                "c1 inhibitor": "FDA Cinryze 2008 (CBER); not new in 2010-2024", "chlormethine": "mechlorethamine, 1949",
                "human coagulation factor viii": "plasma factor VIII (Voncento); Humate-P 1986",
                "human von willebrand factor": "plasma von Willebrand factor (Voncento); Humate-P 1986",
                "alpha1-proteinase inhibitor": "alpha-1 antitrypsin; Prolastin 1987", "pancreas powder": "pancreatin",
                "para-aminosalicylic acid": "PAS, 1940s", "polidocanol": "sclerosant in use since the 1960s",
                "xenon xe-129 hyperpolarized": "MRI contrast agent (Xenoview)", "c-11": "PET diagnostic (choline C-11)",
                "lutetium": "radiolabelling precursor (Lumark), not a medicine"})


def fda():
    rd = lambda f: pd.read_csv(R / "fda" / f, sep="\t", dtype=str, encoding="latin-1")
    sub, prod, app = rd("Submissions.txt"), rd("Products.txt"), rd("Applications.txt")
    o = sub[(sub.SubmissionType == "ORIG") & (sub.SubmissionStatus == "AP")].copy()
    o["date"] = pd.to_datetime(o.SubmissionStatusDate, errors="coerce")
    o = o.merge(app[["ApplNo", "ApplType"]], on="ApplNo")
    ing = prod[["ApplNo", "ActiveIngredient", "DrugName"]].drop_duplicates()
    rows = []
    for r in o.merge(ing, on="ApplNo").itertuples():
        for c in components(r.ActiveIngredient, sep=r";"):
            rows.append(dict(substance=c, date=r.date, appl=r.ApplNo, appltype=r.ApplType, cls=r.SubmissionClassCodeID,
                             priority=r.ReviewPriority, name=r.DrugName))
    d = pd.DataFrame(rows).dropna(subset=["date"]).sort_values("date")
    first = d.groupby("substance").first()
    # NME/BLA entry: ANY original approval on the first-approval date that is an NDA Type 1 or 1/4, or a BLA (an
    # application often carries several same-day ORIG rows, e.g. ORIG-1 Type 1 and ORIG-2 efficacy)
    d["nme_row"] = d.cls.isin(["7", "8"]) | (d.appltype == "BLA")
    on_first = d[d.date == d.substance.map(first.date)]
    first["nme"] = on_first.groupby("substance").nme_row.any()
    return first.rename(columns={"date": "fda_first"}), d.groupby("substance").appl.nunique()


def ema():
    x = pd.read_excel(R / "ema" / "medicines_output.xlsx", header=8)
    h = x[(x.Category == "Human") & (x.Generic != "Yes") & (x.Biosimilar != "Yes")].copy()
    h["date"] = pd.to_datetime(h["Marketing authorisation date"], dayfirst=True, errors="coerce")
    inn_col = "International non-proprietary name (INN) / common name"
    rows = []
    for _, r in h.dropna(subset=["date"]).iterrows():
        inn = r[inn_col] if isinstance(r[inn_col], str) else r["Active substance"]
        for c in components(inn):
            rows.append(dict(substance=c, date=r["date"], orphan=r["Orphan medicine"], atc=r["ATC code (human)"],
                             name=r["Name of medicine"]))
    d = pd.DataFrame(rows).sort_values("date")
    return d.groupby("substance").first().rename(columns={"date": "ema_first"})


def canon(df):
    """Merge alias rows into their canonical substance: earliest date wins, names kept as aliases (D6)."""
    df = df.copy()
    df["canonical"] = [ALIAS.get(x, x) for x in df.index]
    df["alias"] = df.index
    return df


def main():
    f, napp = fda()
    e = ema()
    f, e = canon(f), canon(e)
    aliases = {}
    for x in (f, e):
        for a, cn in zip(x.alias, x.canonical):
            aliases.setdefault(cn, set()).add(a)
    f = f.sort_values("fda_first").groupby("canonical").first()
    e = e.sort_values("ema_first").groupby("canonical").first()
    napp = napp.groupby(lambda k: ALIAS.get(k, k)).sum()
    sub = sorted(set(f.index) | set(e.index))
    c = pd.DataFrame(index=pd.Index(sub, name="substance"))
    c["fda_first"] = f.fda_first; c["fda_priority"] = f.priority; c["fda_name"] = f.name; c["n_fda_appl"] = napp
    c["fda_nme"] = f.nme
    c["ema_first"] = e.ema_first; c["ema_orphan"] = e.orphan; c["atc"] = e.atc; c["ema_name"] = e.name
    # D8: CBER first licensure (Purple Book)
    pb = pd.read_csv(R / "purplebook" / "purplebook.csv", skiprows=3, dtype=str, encoding="utf-8-sig")
    pb = pb[pb.Center == "CBER"].copy()
    pb["date"] = pd.to_datetime(pb["Approval Date"], format="mixed", errors="coerce")
    pb["proper"] = pb["Proper Name"].fillna("").map(lambda x: norm(x))
    pb["brand"] = pb["Proprietary Name"].fillna("").str.lower().str.split().str[0]
    pb["stem"] = pb["Proper Name"].fillna("").str.lower().str.replace(r"-[a-z]{4}$", "", regex=True).str.strip()
    for k, stems in CBER_ONLY.items():
        m = pb[pb.stem.isin(stems)].sort_values("date")
        assert len(m), k
        x = m.iloc[0]
        c.loc[k, ["fda_first", "fda_name", "fda_nme"]] = [x.date, f"CBER {x['Proprietary Name']} ({x['Proper Name']})", True]
        aliases[k] = {k} | CBER_ONLY_ALIAS.get(k, set())
    c["fda_first"] = pd.to_datetime(c.fda_first)
    cber = {}
    for k in c.index:
        names = aliases.get(k, {k}) | {k}
        ema_brand = str(c.loc[k, "ema_name"]).lower().split()[0] if isinstance(c.loc[k, "ema_name"], str) else "@@"
        m = pb[pb.proper.isin(names) | (pb.brand == ema_brand) | (pb.brand == CBER_BRAND.get(k, "@@"))]
        if len(m) and m.date.notna().any():
            x = m.sort_values("date").iloc[0]
            cber[k] = (x.date, f"CBER {x['Proprietary Name']} ({x['Proper Name']})")
    for k, (dt, why) in cber.items():
        if pd.isna(c.loc[k, "fda_first"]) or dt < c.loc[k, "fda_first"]:
            c.loc[k, "fda_first"] = dt; c.loc[k, "fda_name"] = why; c.loc[k, "fda_nme"] = True
    c["cber_t0"] = c.index.isin(list(cber))
    for k, (dt, why) in T0_OVERRIDE.items():
        if k in c.index:
            c.loc[k, "fda_first"] = pd.Timestamp(dt); c.loc[k, "fda_name"] = why; c.loc[k, "fda_nme"] = True
    # every substance's first approval (any year), for link.py's first-word rule (D6)
    allf = pd.concat([f.fda_first.rename("first"), e.ema_first.rename("first")]).groupby(level=0).min()
    allf.to_frame().to_csv(RUN / "data" / "all_first_approvals.csv")
    c["t0"] = c[["fda_first", "ema_first"]].min(axis=1)
    c["t0_source"] = (c.fda_first <= c.ema_first.fillna(pd.Timestamp.max)).map({True: "FDA", False: "EMA"})
    c["aliases"] = ["|".join(sorted(aliases.get(k, {k}) | {k})) for k in c.index]
    c = c[(c.t0 >= LO) & (c.t0 <= HI)]
    diag = c.index.to_series().map(lambda x: bool(DIAG_RE.search(x))) | c.atc.fillna("").str.match(r"^(J07|V04|V08|V09|V01)")
    c = c[~diag]
    c = c[c.index.str.len() > 3]
    c = c[~c.index.isin(list(EXCLUDE))]
    # FDA-first substances must enter through a new-molecular-entity NDA (Type 1, Type 1/4) or a BLA, so old
    # substances first marketed in the US inside a nutrition kit or a new formulation are not "new"
    nme = (c.t0_source == "EMA") | (c.fda_nme == True)  # noqa: E712
    print("dropped as not NME/BLA:", sorted(c[~nme].index)[:60], int((~nme).sum()))
    c = c[nme]
    c.to_csv(RUN / "data" / "cohort.csv")
    print(len(c), "substances;", c.t0_source.value_counts().to_dict(), "; by year", c.t0.dt.year.value_counts().sort_index().to_dict())


if __name__ == "__main__":
    sys.exit(main())
