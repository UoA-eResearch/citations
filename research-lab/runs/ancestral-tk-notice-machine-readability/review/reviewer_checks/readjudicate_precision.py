"""Reviewer's independent re-adjudication of all 69 name-only census hits (precision.csv). For each record the exact
JSON path(s) of every vocabulary-name match in the saved raw record are located; a hit is genuine only if the name
is applied to the record (not an empty template field name, and not prose about Local Contexts). Writes
precision_readjudication.csv and prints agreement with the study's precision.csv."""
import csv, json, re, sys
from collections import Counter
from pathlib import Path
HERE = Path(__file__).resolve().parent; RUN = HERE.parents[1]
sys.path.insert(0, str(RUN / "code"))
from detect import LABEL_RES, NOTICE_RES  # the preregistered name patterns

def walk(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items(): yield from walk(v, f"{path}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o): yield from walk(v, f"{path}[{i}]")
    elif isinstance(o, str): yield path, o

study = {(r["platform"], str(r["record"])): r for r in csv.DictReader(open(RUN / "results" / "tables" / "precision.csv"))}
pats = list(LABEL_RES.values()) + list(NOTICE_RES.values())
raw = {}
for p in {k[0] for k in study}:
    for l in open(RUN / "data" / "raw" / p / "records.jsonl"):
        x = json.loads(l); raw[(p, str(x["id"]))] = x.get("full") or x["meta"]
out = []
for key, s in study.items():
    obj = raw[key]; hits = []
    for path, txt in walk(obj):
        for rx in pats:
            m = rx.search(txt)
            if m: hits.append((re.sub(r"\[\d+\]", "[]", path), txt[max(0, m.start() - 80):m.end() + 80].replace("\n", " ")))
    paths = sorted({h[0] for h in hits})
    # reviewer rule
    if paths and all(p.endswith(".custom_fields[].name") or p.endswith(".custom_fields[].settings.placeholder") for p in paths):
        # a figshare custom-field *name*; genuine only if that field has a value
        vals = [f.get("value") for f in obj.get("custom_fields", []) if any(rx.search(f.get("name", "")) for rx in pats)]
        filled = [v for v in vals if v not in (None, "", [], [""])]
        rev, why = (1 if filled else 0), ("custom field named for a Notice/Label; value=" + (json.dumps(filled)[:60] if filled else "empty") )
    else:
        ctx = " ".join(h[1] for h in hits)
        if re.search(r"applied\W+the\W+Open to Collaborate Notice", ctx):
            rev, why = 0, "conference abstract describing Neotoma's use of the Notice"
        elif re.search(r"TK Verified\), \(4\) that non-commercial", ctx):
            rev, why = 0, "journal abstract explaining what the Labels mean"
        elif re.search(r"The BC Notice recognizes the rights of Indigenous peoples", ctx) and key[0] in ("gbif", "datacite"):
            rev, why = 1, "BC Notice text applied in the dataset description (Landcare Research / GBIF)"
        else:
            rev, why = -1, "needs manual look: " + ctx[:120]
    out.append(dict(platform=key[0], record=key[1], study_genuine=int(s["genuine"]), reviewer_genuine=rev, agree=int(rev == int(s["genuine"])),
                    match_paths="|".join(paths), reviewer_note=why, study_note=s["note"]))
with open(HERE / "precision_readjudication.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
print(len(out), "re-adjudicated;", sum(o["agree"] for o in out), "agree;", Counter((o["platform"], o["reviewer_genuine"]) for o in out))
for o in out:
    if not o["agree"] or o["reviewer_genuine"] == -1: print("DISAGREE/UNSURE", o)
