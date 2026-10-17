"""D4: replace the refitted networks' records in data/fits.jsonl with data/fits_refit.jsonl (first run kept as
data/fits_v1.jsonl)."""
import json
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
new = {json.loads(l)["record"]: l.rstrip("\n") for l in open(RUN / "data" / "fits_refit.jsonl")}
out = []
for l in open(RUN / "data" / "fits_v1.jsonl"):
    r = json.loads(l)["record"]
    out.append(new.pop(r, l.rstrip("\n")))
assert not new, f"refit records not in the first run: {sorted(new)}"
(RUN / "data" / "fits.jsonl").write_text("\n".join(out) + "\n")
print(len(out), "records written")
