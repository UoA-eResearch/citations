"""Descriptive audit (G4, added at the pre-review gate) of the parsed conjectures contradicted by their own data: share
whose formula line carries a condition the parser ignores. Classes are keyword-based and non-exclusive; the line
text is not written out (data only). -> results/tables/contradicted_audit.json"""
import json
import re
import sys
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
from parse import SEQ, read_entry  # noqa: E402

C = pd.read_parquet(RUN / "data" / "interim" / "conjectures.parquet")
bad = C[(C.status == "parsed") & (C.data_ok == False)]                  # noqa: E712
PAT = {"parity or residue condition": r"\bn (is )?(even|odd)\b|\bfor (even|odd) n\b|\bn ?== ?\d|mod \d",
       "index restriction (for n > k, n >= k)": r"for n ?(>|>=|≥) ?\d+|\bn ?(>|>=|≥) ?\d+",
       "exponential g.f.": r"e\.g\.f\.|egf|exponential generating",
       "if and only if / membership statement": r"if and only if|\biff\b|\bin the sequence\b",
       "offset or alternative indexing mentioned": r"offset|shifted|a\(n-?\d*\) ?= ?a\(n\+"}
counts = {k: 0 for k in PAT}
none = 0
for anum, line_no in zip(bad.anum, bad.line_no):
    e = read_entry(SEQ / anum[:4] / f"{anum}.seq")
    text = e["F"][int(line_no)] if int(line_no) < len(e["F"]) else ""
    hit = False
    for k, p in PAT.items():
        if re.search(p, text, re.I):
            counts[k] += 1; hit = True
    none += not hit
out = {"contradicted_lines": int(len(bad)), "with_condition_keyword": counts,
       "any_condition_keyword": int(len(bad) - none), "no_keyword": int(none)}
(RUN / "results" / "tables" / "contradicted_audit.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
