"""Build the evaluation corpus: real DataCite records, each with every rights condition swapped into one slot.

Base records: a seeded random sample of Neotoma records (48,332 of the 48,353 DataCite records carrying a Local
Contexts URI are Neotoma's) plus all 21 non-Neotoma records. From each, any existing Local Contexts element is
removed, leaving its other metadata verbatim; then each CONDITION is appended to its rightsList (after the record's
CC BY entry). The pilot uses a disjoint Neotoma sample.

Conditions (Local Contexts wording and URIs from localcontexts.org, retrieved 2026-10-17):
  NONE        no extra element
  LC_CB       "TK Open to Collaboration (TK CB)", URI .../notice/open-to-collaborate/   (Neotoma's real form)
  LC_NC       "TK Non-Commercial (TK NC)", URI .../label/tk-non-commercial/
  LC_BC       "Local Contexts Biocultural (BC) Notice", URI .../notice/bc-notice/
  LC_TK       "Local Contexts Traditional Knowledge (TK) Notice", URI .../notice/tk-notice/
  LC_CO       "TK Community Use Only (TK CO)", URI .../label/tk-community-use-only/
  CV_NC       "Creative Commons Attribution Non Commercial 4.0 International", URI creativecommons.org/.../by-nc/4.0/
  CV_DUA      "A data use agreement is required before reuse." (no URI)
  CV_CONTACT  "Users are asked to contact the data providers before reuse; collaboration is welcome." (no URI)
  LC_CB_NOURI LC_CB without its URI (sensitivity: is the localcontexts.org URI the cue?)
Matched pairs: LC_NC ~ CV_NC (the same restriction), LC_CB ~ CV_CONTACT (the same invitation).

Writes data/corpus/{main,pilot}.jsonl: one line per (record, condition) with the rendered metadata JSON.
"""
import json
import random
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
RAW, OUT = RUN / "data" / "raw" / "datacite", RUN / "data" / "corpus"
SEED = 20261017
N_MAIN_NEOTOMA, N_PILOT = 200, 20
LC = "https://localcontexts.org"
CONDITIONS = {
    "NONE": None,
    "LC_CB": {"rights": "TK Open to Collaboration (TK CB)", "rightsUri": f"{LC}/notice/open-to-collaborate/"},
    "LC_NC": {"rights": "TK Non-Commercial (TK NC)", "rightsUri": f"{LC}/label/tk-non-commercial/"},
    "LC_BC": {"rights": "Local Contexts Biocultural (BC) Notice", "rightsUri": f"{LC}/notice/bc-notice/"},
    "LC_TK": {"rights": "Local Contexts Traditional Knowledge (TK) Notice", "rightsUri": f"{LC}/notice/tk-notice/"},
    "LC_CO": {"rights": "TK Community Use Only (TK CO)", "rightsUri": f"{LC}/label/tk-community-use-only/"},
    "CV_NC": {"rights": "Creative Commons Attribution Non Commercial 4.0 International",
              "rightsUri": "https://creativecommons.org/licenses/by-nc/4.0/legalcode"},
    "CV_DUA": {"rights": "A data use agreement is required before reuse."},
    "CV_CONTACT": {"rights": "Users are asked to contact the data providers before reuse; collaboration is welcome."},
    "LC_CB_NOURI": {"rights": "TK Open to Collaboration (TK CB)"},
}
KEEP = ["doi", "titles", "creators", "publisher", "publicationYear", "types", "subjects", "descriptions",
        "geoLocations", "dates", "rightsList", "relatedIdentifiers", "fundingReferences", "language", "version"]


def is_lc(x):
    return "localcontexts" in (x.get("rightsUri") or "").lower() or "local contexts" in (x.get("rights") or "").lower() \
        or (x.get("rights") or "").startswith(("TK ", "BC ", "The TK", "The BC"))


def strip(rec):
    a = rec["attributes"]
    m = {k: a[k] for k in KEEP if a.get(k) not in (None, [], "")}
    m["rightsList"] = [{k: v for k, v in x.items() if k in ("rights", "rightsUri")} for x in a.get("rightsList") or []
                       if not is_lc(x)]
    if isinstance(m.get("publisher"), dict):
        m["publisher"] = m["publisher"].get("name")
    # long lists are capped so every record fits the context window; the cap is the same for every condition
    for k, cap in (("relatedIdentifiers", 10), ("creators", 15), ("geoLocations", 5), ("subjects", 15),
                   ("fundingReferences", 5), ("dates", 8), ("titles", 3)):
        if isinstance(m.get(k), list) and len(m[k]) > cap:
            m[k] = m[k][:cap]
    for c in m.get("creators", []):
        c.pop("affiliation", None) if not c.get("affiliation") else None
    for d in m.get("descriptions", []):                     # very long abstracts are trimmed, identically per record
        if len(d.get("description", "")) > 1500:
            d["description"] = d["description"][:1500] + " ..."
    return m


def render(meta, cond):
    m = json.loads(json.dumps(meta))
    if CONDITIONS[cond] is not None:
        m["rightsList"] = m.get("rightsList", []) + [CONDITIONS[cond]]
    return json.dumps(m, ensure_ascii=False, indent=1)


def main():
    recs = [json.loads(l) for l in open(RAW / "lc_records.jsonl")]
    neo = [r for r in recs if "neotoma" in str(r["attributes"].get("publisher")).lower()]
    # the 21 records outside Neotoma's DOI prefix, fetched in one query (lc_other_records.jsonl)
    other = [json.loads(l) for l in open(RAW / "lc_other_records.jsonl")]
    rnd = random.Random(SEED)
    rnd.shuffle(neo)
    main_recs, pilot_recs = neo[:N_MAIN_NEOTOMA] + other, neo[N_MAIN_NEOTOMA:N_MAIN_NEOTOMA + N_PILOT]
    OUT.mkdir(parents=True, exist_ok=True)
    for name, rs in (("main", main_recs), ("pilot", pilot_recs)):
        with open(OUT / f"{name}.jsonl", "w") as fh:
            for r in rs:
                meta = strip(r)
                cc = [x for x in meta["rightsList"] if "creativecommons" in (x.get("rightsUri") or "").lower()
                      or "cc" in (x.get("rights") or "").lower()]
                for cond in CONDITIONS:
                    fh.write(json.dumps(dict(doi=r["attributes"]["doi"], neotoma=r in neo, condition=cond,
                                             has_cc=bool(cc), metadata=render(meta, cond)), ensure_ascii=False) + "\n")
        print(name, len(rs), "records x", len(CONDITIONS), "conditions")
    print("non-Neotoma records:", len(other))


if __name__ == "__main__":
    sys.exit(main())
