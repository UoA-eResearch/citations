"""Linking validation (plan section 4).

  sample  150 random cohort substances (seed 20261020). For each, an evidence file lists everything the adjudicator
          needs, side by side with the linked dates:
            - every Medsafe product and new-medicine application the search returned (marked if it passed the
              ingredient filter);
            - the first community-Schedule and HML editions that matched, and near-miss chemical names (fuzzy
              partial ratio >= 90) that did not match;
            - INDEPENDENT check: the first Schedule Update PDF whose text mentions the substance, with the lines.
          Writes data/validation/evidence/<id>.txt and data/validation/link_key.csv.
  merge   reads results/tables/link_validation_raw.csv (id, t1_ok, t2_ok, t3_ok, note; 1 = correct within 31 days
          or correctly absent, 0 = wrong, blank = cannot tell) -> results/tables/link_validation.csv and precision.
"""
import re
import sys
from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz

sys.path.insert(0, str(Path(__file__).resolve().parent))
from link import has  # noqa: E402
from names import norm  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
V, TAB = RUN / "data" / "validation", RUN / "results" / "tables"


SU_TEXT = None


def su_mentions(sub):
    global SU_TEXT
    if SU_TEXT is None:
        SU_TEXT = [(t.stem, t.read_text()) for t in sorted((RUN / "data" / "su_text").glob("*.txt"))]
    pat = re.compile(r"(?i)(?<![a-z])" + re.escape(sub) + r"(?![a-z])")
    for stem, txt in SU_TEXT:
        if pat.search(txt):
            return stem, [l.strip() for l in txt.splitlines() if pat.search(l)][:4]
    return None, []


def sample():
    d = pd.read_csv(RUN / "data" / "linked.csv")
    P = pd.read_csv(RUN / "data" / "medsafe_products.csv", dtype=str)
    A = pd.read_csv(RUN / "data" / "medsafe_applications.csv", dtype=str)
    L = pd.read_csv(RUN / "data" / "pharmac_listings.csv", dtype=str)
    # one row per (source, chemical): first edition and normalised chemical + formulation text, computed once
    U = (L.assign(text=(L.chemical.fillna("") + " " + L.formulations.fillna("")))
          .groupby(["source", "chemical"]).agg(first=("edition", "min"), text=("text", "first")).reset_index())
    U["ntext"] = U.text.map(norm); U["nchem"] = U.chemical.fillna("").map(norm)
    s = d.sample(150, random_state=20261020).reset_index(drop=True)
    (V / "evidence").mkdir(parents=True, exist_ok=True)
    keys = []
    for i, r in s.iterrows():
        sub, lid = r.substance, f"m{i:03d}"
        out = [f"SUBSTANCE: {sub}   T0 {r.t0} ({r.t0_source})", f"LINKED: T1 {r.t1}  T2 {r.t2}  T3B {r.t3b}  T3H {r.t3h}  "
               f"T3 {r.t3}  excluded_old {r.excluded_old}", "", "MEDSAFE PRODUCTS (+ = passed filter):"]
        for x in P[P.substance == sub].head(40).itertuples():
            out.append(f"  {'+' if has(sub, x.ingredients) else ' '} {x.approval_date:>11} | {x.status} | {x.product} | {x.ingredients}")
        out.append("MEDSAFE APPLICATIONS (New ... Medicine Application rows):")
        for x in A[(A.substance == sub) & A.type.fillna("").str.startswith("New")].head(20).itertuples():
            out.append(f"  {'+' if has(sub, x.ingredients) else ' '} {x.application_date:>11} | {x.status} | {x.change} | {x.product}")
        pat = re.compile(r"(?<![a-z0-9])" + re.escape(sub) + r"(?![a-z0-9])")
        hit = U[U.ntext.str.contains(pat)]
        out.append("PHARMAC XML first editions (matched):")
        out += [f"  {x.source:8} {x.first} | {x.chemical}" for x in hit.itertuples()]
        out.append("PHARMAC near-miss chemical names (not matched):")
        near = U[~U.index.isin(hit.index)]
        near = near[[fuzz.partial_ratio(sub, c) >= 90 for c in near.nchem]]
        out += [f"  {x.source:8} {x.first} | {x.chemical}" for x in near.head(10).itertuples()]
        f, lines = su_mentions(sub)
        out.append(f"SCHEDULE UPDATE PDFs, first mention: {f}")
        out += [f"  > {l[:200]}" for l in lines]
        (V / "evidence" / f"{lid}.txt").write_text("\n".join(out) + "\n")
        keys.append(dict(id=lid, substance=sub))
    pd.DataFrame(keys).to_csv(V / "link_key.csv", index=False)
    print(len(keys), "evidence files")


def merge():
    m = pd.read_csv(TAB / "link_validation_raw.csv").merge(pd.read_csv(V / "link_key.csv"), on="id")
    m.to_csv(TAB / "link_validation.csv", index=False)
    for c in ("t1_ok", "t2_ok", "t3_ok"):
        x = m[c].dropna()
        print(c, f"{x.mean():.3f}", f"({int(x.sum())}/{len(x)}; {m[c].isna().sum()} cannot tell)")


if __name__ == "__main__":
    {"sample": sample, "merge": merge}[sys.argv[1]]()
