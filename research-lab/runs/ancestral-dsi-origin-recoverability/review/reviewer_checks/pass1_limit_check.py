"""Tests D5 s2's claim that no pass-1 record has a location value past the reading aid's own limits
(compact.py prints attributes[:500] and comment/other single-line fields [:300]).

For every gold record, find the earliest offset of an INSDC country/ocean name or a decimal coordinate inside
`attributes` and inside `comment`, and flag the records where that earliest hit sits past the aid's limit.
Also reports the same for the arms' evidence, and the LLM answers that were dropped because they did not resolve
to an INSDC name (llm == null but llm_conf > 0)."""
import json
import re
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RUN / "code"))
import countries  # noqa: E402

R = [json.loads(l) for l in open(RUN / "data" / "gold" / "records.jsonl")]
names = sorted((re.escape(v) for v in countries.VOCAB if v not in ("Gambia",)), key=len, reverse=True)
LOC = re.compile(r"\b(" + "|".join(names) + r")\b|\d+\.\d+\s*[NSEW]\b|\d+\.\d+\s*°")

print("=== records whose earliest location value in `attributes` sits past the pass-1 aid limit of 500 chars")
n = 0
for x in R:
    a = x.get("attributes") or ""
    hits = [m for m in LOC.finditer(a)]
    if hits and hits[0].start() >= 500:
        n += 1
        print(f"  {x['record']} offset={hits[0].start()} value={hits[0].group(0)!r} tail={a[480:600]!r}")
print(f"  -> {n} records")

print("\n=== records whose earliest location value in `comment` sits past the aid limit of 300 chars")
n = 0
for x in R:
    c = x.get("comment") or ""
    hits = [m for m in LOC.finditer(c)]
    if hits and hits[0].start() >= 300:
        n += 1
        print(f"  {x['record']} offset={hits[0].start()} value={hits[0].group(0)!r} tail={c[280:400]!r}")
print(f"  -> {n} records")

print("\n=== where in `attributes` the ENA country variant sits (D3 s2 / D5 s2's caught record)")
for x in R:
    a = x.get("attributes") or ""
    for key in ("geographic location, country and/or sea=", "geo_location=", "geographic location (country"):
        i = a.find(key)
        if i >= 0:
            print(f"  {x['record']} key={key!r} offset={i} (pass-1 aid cut 500) value={a[i:i+90]!r}")

print("\n=== LLM answers dropped because they did not resolve to an INSDC name (llm null but conf > 0)")
A = [json.loads(l) for l in open(RUN / "data" / "gold" / "arms.jsonl")]
drop = [a for a in A if a["llm"] is None and a["llm_conf"] > 0]
print(f"  {len(drop)} of {len(A)}:", [(a['record'], a['llm_conf']) for a in drop][:20])
print("  gazetteer null with conf>0:", sum(1 for a in A if a["gazetteer"] is None and a["gazetteer_conf"] > 0))
print("  classifier null:", sum(1 for a in A if a["classifier"] is None))
