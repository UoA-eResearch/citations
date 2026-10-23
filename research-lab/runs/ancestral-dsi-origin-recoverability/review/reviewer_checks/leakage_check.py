"""Submitter-institution text inside the evidence the arms (and the gold passes) read; arm agreement with the owner
country on those records. Also the D5 s3 attribute-cap records and D8's cap claim."""
import json, re, sys, collections
from pathlib import Path
import pandas as pd
RUN = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RUN / "code")); import countries  # noqa
R = {x["record"]: x for x in (json.loads(l) for l in open(RUN / "data" / "gold" / "records.jsonl"))}
rows = pd.read_csv(RUN / "results" / "tables" / "limb2_rows.csv", keep_default_na=False).set_index("record")
oc = pd.read_csv(RUN / "data" / "gold" / "owner_countries.csv", keep_default_na=False).set_index("record")
owners = pd.read_csv(RUN / "data" / "gold" / "owners.csv", keep_default_na=False).set_index("record")
INST = ("insdc center name", "insdc center alias", "collected_by", "sequenced_by", "biomaterial_provider", "biomaterial_rpovider", "center", "submitter id", "lab_host")
def inst_fields(x):
    out = {}
    for kv in (x.get("attributes") or "").split("; "):
        k, _, v = kv.partition("=")
        if k.strip().lower() in INST and v.strip():
            out[k.strip().lower()] = v.strip()
    return out
have = {i: inst_fields(x) for i, x in R.items() if inst_fields(x)}
print("records with institution-type attributes in the evidence:", len(have), "of", len(R))
print(" by key:", collections.Counter(k for v in have.values() for k in v))
# does the owner's name itself appear verbatim in the evidence text?
def evidence(x):
    return " ; ".join(str(x.get(f) or "") for f in ("sample_title", "isolation_source", "attributes", "comment", "bioproject_title", "bioproject_description")) + " ; " + " ; ".join(f"{p['title']} {p['abstract']} {p.get('methods_sentences','')}" for p in x["publications"])
own_in_ev = []
for i, x in R.items():
    o = (owners.loc[i, "biosample_owner"] or "").strip()
    if len(o) >= 6 and o.lower() in evidence(x).lower():
        own_in_ev.append(i)
print("records whose BioSample owner name appears verbatim in the evidence:", len(own_in_ev), own_in_ev[:15])
# among records with an institution attribute, how often does each arm's wrong call equal the owner country?
for arm in ("gazetteer", "classifier", "llm"):
    for grp, ids in (("inst-attr", [i for i in have if i in rows.index]), ("no-inst-attr", [i for i in R if i not in have and i in rows.index])):
        sub = rows.loc[ids]
        err = sub[(sub[arm] != "") & (sub[arm] != sub.gold)]
        known = err[[bool(oc.loc[i, "owner_country"] or oc.loc[i, "submitter_country"]) for i in err.index]]
        hit = sum(known.loc[i, arm] == (oc.loc[i, "owner_country"] or oc.loc[i, "submitter_country"]) for i in known.index)
        calls = (sub[arm] != "").sum()
        print(f"{arm:10s} {grp:12s} n={len(sub):3d} calls={calls:3d} errors={len(err):3d} errors_with_known_owner={len(known):3d} naming_owner_country={hit}")
# gold countries: does any coincide with an institution-type attribute value's country?
print("\nGold-country records carrying institution-type attributes:")
for i in rows.index[rows.gold != "not determinable"]:
    if i in have: print(" ", i, rows.loc[i, "gold"], have[i])
# D5 s3: attribute cap
cap = [i for i, x in R.items() if len(x.get("attributes") or "") >= 600]
print("\nrecords at the 600-char attribute cap:", len(cap))
for i in cap:
    tail = R[i]["attributes"][-90:]
    lab = rows.loc[i, "label"] if i in rows.index else "excluded"
    print(f"  {i} label={lab:14s} tail=...{tail!r}")
# D8: publications and the 12-sentence cap
nfull = [i for i, x in R.items() if any(p.get("methods_sentences") for p in x["publications"])]
at12 = [i for i in nfull if any(len(p.get("methods_sentences", "").split(" | ")) >= 12 for p in R[i]["publications"])]
print("\nrecords with any full-text sampling sentences:", len(nfull), "| with a publication at the 12-sentence cap:", len(at12))
print("records with_pub but no full-text sentences (abstract only):", sum(1 for i, x in R.items() if x["has_pub"] and i not in nfull))
