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


def su_mentions(sub):
    pat = re.compile(r"(?i)(?<![a-z])" + re.escape(sub) + r"(?![a-z])")
    for t in sorted((RUN / "data" / "su_text").glob("*.txt")):
        txt = t.read_text()
        if pat.search(txt):
            lines = [l.strip() for l in txt.splitlines() if pat.search(l)][:4]
            return t.stem, lines
    return None, []


def sample():
    d = pd.read_csv(RUN / "data" / "linked.csv")
    P = pd.read_csv(RUN / "data" / "medsafe_products.csv", dtype=str)
    A = pd.read_csv(RUN / "data" / "medsafe_applications.csv", dtype=str)
    L = pd.read_csv(RUN / "data" / "pharmac_listings.csv", dtype=str)
    chems = L.drop_duplicates(["source", "chemical"]).copy()
    first = L.groupby(["source", "chemical"]).edition.min()
    s = d.sample(150, random_state=20261020).reset_index(drop=True)
    (V / "evidence").mkdir(parents=True, exist_ok=True)
    keys = []
    for i, r in s.iterrows():
        sub, lid = r.substance, f"m{i:03d}"
        out = [f"SUBSTANCE: {sub}   T0 {r.t0} ({r.t0_source})", f"LINKED: T1 {r.t1}  T2 {r.t2}  T3B {r.t3b}  T3H {r.t3h}  "
               f"T3 {r.t3}  excluded_old {r.excluded_old}", "", "MEDSAFE PRODUCTS (+ = passed filter):"]
        for x in P[P.substance == sub].itertuples():
            out.append(f"  {'+' if has(sub, x.ingredients) else ' '} {x.approval_date:>11} | {x.status} | {x.product} | {x.ingredients}")
        out.append("MEDSAFE APPLICATIONS (New ... Medicine Application rows):")
        for x in A[(A.substance == sub) & A.type.fillna("").str.startswith("New")].itertuples():
            out.append(f"  {'+' if has(sub, x.ingredients) else ' '} {x.application_date:>11} | {x.status} | {x.change} | {x.product}")
        out.append("PHARMAC XML first editions (matched):")
        for (src, ch), ed in first.items():
            if has(sub, ch) or any(has(sub, f) for f in L[(L.source == src) & (L.chemical == ch)].formulations.dropna().head(3)):
                out.append(f"  {src:8} {ed} | {ch}")
        out.append("PHARMAC near-miss chemical names (not matched):")
        for x in chems.itertuples():
            if not has(sub, x.chemical) and fuzz.partial_ratio(sub, norm(x.chemical)) >= 90:
                out.append(f"  {x.source:8} {first[(x.source, x.chemical)]} | {x.chemical}")
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
