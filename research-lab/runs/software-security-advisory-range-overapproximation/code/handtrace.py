"""G3 hand traces (written after the results). For one tight, one over-approximated and one undetermined advisory:
re-download the earliest in-range release and (if any) the first present release, and count, with plain substring
search on whitespace-stripped file text (not the pipeline's line normalisation), how many of the fix's deleted or
context lines occur. -> results/tables/handtrace.json"""
import json
import re
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
import audit_packets as A  # noqa: E402
import classify as C  # noqa: E402
import presence as P  # noqa: E402
import pandas as pd  # noqa: E402

T, D = RUN / "results" / "tables", RUN / "data"
K = pd.read_csv(T / "classes.csv")
picks = {"tight": "GHSA-h3h8-3v2v-rg7m", "over-approximated": "GHSA-m6hv-x64c-27mm", "undetermined": "GHSA-2qjp-fg8c-g878"}
out = {}
for cls, aid in picks.items():
    r = K[K.id == aid].iloc[0].to_dict()
    eco = r["ecosystem"]
    diff = (D / "commits" / f"{aid}.diff").read_text(errors="ignore")
    files = P.parse_diff(diff, eco)
    raw_sig = [l[1:].strip() for l in diff.splitlines() if l.startswith("-") and not l.startswith("---") and len(l.strip()) > 9]
    rel = C.in_range_sorted(r)
    idx = [0] + ([int(r["fp"])] if cls == "over-approximated" else [])
    res = {"id": aid, "pipeline_class": cls, "n_in_range": len(rel), "releases": []}
    for i in idx:
        picked, listing = A.files_for(rel[i]["url"], eco, list(files))
        text = re.sub(r"\s+", "", "\n".join((picked or {}).values()))
        hits = sum(re.sub(r"\s+", "", s) in text for s in raw_sig) if raw_sig else None
        res["releases"].append({"index": i, "version": rel[i]["version"], "matched_files": sorted(picked or {}),
                                "deleted_lines_found_by_substring": hits, "deleted_lines": len(raw_sig), "source_files": len(listing)})
    out[cls] = res
    print(json.dumps(res), flush=True)
(T / "handtrace.json").write_text(json.dumps(out, indent=1) + "\n")
