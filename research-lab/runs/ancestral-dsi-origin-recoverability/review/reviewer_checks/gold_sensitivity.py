"""Sensitivity of the limb-2 headline numbers to the gold-country labels that rest on a collecting-agency
identifier rather than on a stated place.

plan.md section 3: "The submitter's institution is **not** evidence of origin"; the plan's fixed adjudication rule
gives a country only on "an explicit sampling-site statement". For the records below the only origin cue in the
evidence is `collected_by` / `sequenced_by` (a US state postal code, or a provincial CDC's name) plus the PulseNet
programme name - there is no stated place, and the only country words in the text are reagent-supplier addresses.

Recomputes: the test ceiling, the 497-record label shares, the stratified projection, and the arms' any-confidence
precision/recall on the test split and on D7's natural subset, with those labels moved to "not stated"."""
import json
import math
import sys
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RUN / "code"))
from score import ND, wilson  # noqa: E402

OUT = Path(__file__).resolve().parent
ARMS = ["gazetteer", "classifier", "llm"]
# country label rests only on a collecting-agency identifier (no stated place anywhere in the evidence)
AGENCY = ["R240", "R241", "R242", "R243", "R244", "R475", "R477"]

rows = pd.read_csv(RUN / "results" / "tables" / "limb2_rows.csv", keep_default_na=False)
R = {x["record"]: x for x in (json.loads(l) for l in open(RUN / "data" / "gold" / "records.jsonl"))}

print("=== evidence check: does any country word in these records' evidence come from a stated place?")
for i in AGENCY:
    x = R[i]
    ev = " ; ".join(str(x.get(f) or "") for f in ("sample_title", "isolation_source", "attributes", "comment",
                                                  "bioproject_title", "bioproject_description"))
    ev += " ; " + " ; ".join(f"{p['title']} {p['abstract']} {p.get('methods_sentences', '')}" for p in x["publications"])
    for w in ("USA", "United States", "U.S.", "China"):
        if w in ev:
            k = ev.find(w)
            print(f"  {i}: {w!r} appears -> ...{ev[max(0, k - 70):k + 30]!r}")
    print(f"  {i}: collected_by/sequenced_by -> "
          f"{[kv for kv in (x.get('attributes') or '').split('; ') if kv.startswith(('collected_by', 'sequenced_by'))]}")


def summarise(df, tag):
    out = {"tag": tag}
    test = df[df.split == "test"]
    det = int((test.gold != ND).sum())
    out["test_determinable"] = det
    out["test_ceiling"] = round(det / len(test), 4)
    out["test_ceiling_ci"] = wilson(det, len(test))
    out["labels_497"] = df.label.map(lambda l: l if l in ("inapplicable", "not stated") else "country").value_counts().to_dict()
    # stratified projection of the label shares (score.py population counts)
    pop = {True: 456061, False: 1201362}
    N = pop[True] + pop[False]
    proj = {}
    for cls in ("inapplicable", "not stated", "country"):
        tot = var = 0.0
        for h in (True, False):
            s = df[df.has_pub == (h if df.has_pub.dtype != object else str(h))]
            if not len(s):
                s = df[df.has_pub.astype(str) == str(h)]
            p = (s.label.map(lambda l: (l if l in ("inapplicable", "not stated") else "country")) == cls).mean()
            tot += pop[h] * p
            var += pop[h] ** 2 * p * (1 - p) / len(s)
        se = math.sqrt(var)
        proj[cls] = {"samples": round(tot), "share": round(tot / N, 4),
                     "share_ci": [round(max(0, tot - 1.96 * se) / N, 4), round((tot + 1.96 * se) / N, 4)]}
    out["projection"] = proj
    for scope, sub in (("test", test), ("natural_all", df[df.label != "inapplicable"]),
                       ("natural_test", test[test.label != "inapplicable"])):
        d = int((sub.gold != ND).sum())
        out[f"{scope}_arms_any_conf"] = {}
        for a in ARMS:
            m = sub[sub[a] != ""]
            ok = int((m[a] == m.gold).sum())
            out[f"{scope}_arms_any_conf"][a] = {
                "calls": len(m), "correct": ok,
                "precision": round(ok / len(m), 4) if len(m) else None,
                "precision_ci": wilson(ok, len(m)),
                "recall_of_determinable": round(ok / d, 4) if d else None}
    return out


base = summarise(rows, "as reported")
alt = rows.copy()
hit = alt.record.isin(AGENCY)
alt.loc[hit, "label"] = "not stated"
alt.loc[hit, "gold"] = ND
sens = summarise(alt, f"agency-derived country labels ({len(AGENCY)}) moved to 'not stated'")
res = {"records_moved": AGENCY, "as_reported": base, "sensitivity": sens}
(OUT / "gold_sensitivity.json").write_text(json.dumps(res, indent=1))
print("\n" + json.dumps(res, indent=1))
