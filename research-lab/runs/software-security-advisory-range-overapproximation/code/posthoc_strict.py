"""Post hoc (after the G4 audit failed its 80% bar): a strict reading of over-approximation. An over-approximated
advisory counts as strict only if release A (the earliest in-range release) has no source file with the same file
name as any file the fix touches, i.e. the module itself is missing. -> results/tables/posthoc_strict.json"""
import json
import math
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
import audit_packets as A  # noqa: E402
import classify as C  # noqa: E402
import presence as P  # noqa: E402

T, D = RUN / "results" / "tables", RUN / "data"
K = pd.read_csv(T / "classes.csv")
ov = K[K.cls == "over-approximated"].to_dict("records")


def one(r):
    diff = (D / "commits" / f"{r['id']}.diff").read_text(errors="ignore")
    names = {p.split("/")[-1] for p in P.parse_diff(diff, r["ecosystem"])}
    rel = C.in_range_sorted(r)
    _, listing = A.files_for(rel[0]["url"], r["ecosystem"], []) if rel[0].get("url") else (None, None)
    if listing is None or not listing:
        return r["id"], None
    have = {p.split("/")[-1] for p in listing}
    return r["id"], not (names & have)


with ThreadPoolExecutor(8) as ex:
    res = dict(ex.map(one, ov))
K["strict"] = K.id.map(res)
key = pd.DataFrame(json.loads(Path(sys.argv[1]).read_text()))
lab = pd.DataFrame(json.loads((D / "audit" / "labels.json").read_text()))
m = key.merge(lab, on="packet").merge(K[["id", "strict"]], on="id")
mo = m[m.pipeline_class == "over-approximated"]
k = int((K.strict == True).sum())  # noqa: E712
n = int(k + (K.cls == "tight").sum())


def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 4), round(c + h, 4)]


out = {"over_approximated": len(ov), "strict": k, "not_strict": int((K.strict == False).sum()), "unknown": int(K.strict.isna().sum() - (K.cls != "over-approximated").sum()),  # noqa: E712
       "strict_share_of_strict_plus_tight": round(k / n, 4), "wilson": wilson(k, n),
       "audited_strict": {"n": int((mo.strict == True).sum()), "auditor_absent": int(((mo.strict == True) & (mo.A == "absent")).sum()),  # noqa: E712
                          "auditor_present": int(((mo.strict == True) & (mo.A == "present")).sum()), "auditor_cannot_tell": int(((mo.strict == True) & (mo.A == "cannot tell")).sum())},  # noqa: E712
       "audited_not_strict": {"n": int((mo.strict == False).sum()), "auditor_absent": int(((mo.strict == False) & (mo.A == "absent")).sum()),  # noqa: E712
                              "auditor_present": int(((mo.strict == False) & (mo.A == "present")).sum()), "auditor_cannot_tell": int(((mo.strict == False) & (mo.A == "cannot tell")).sum())}}  # noqa: E712
K[["id", "cls", "strict"]].to_csv(T / "classes_strict.csv", index=False)
(T / "posthoc_strict.json").write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps(out, indent=1))
