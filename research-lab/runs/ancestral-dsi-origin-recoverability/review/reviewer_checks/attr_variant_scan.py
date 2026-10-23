"""D3 s2 says 2,190 window samples (0.01%) give their country only under the ENA-style attribute
"geographic location, country and/or sea". Gold record R496 shows a second variant, "geo_location", that D3 did not
count. This scans the window's untagged samples for both variants and reports how many carry a value that resolves
to an INSDC country - i.e. samples the classifier calls placeholder/malformed/absent although their own record
states a country. Per-part, one column set at a time."""
import glob
import json
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RUN / "code"))
import countries  # noqa: E402

OUT = Path(__file__).resolve().parent
KEYS = {"ena_long": "geographic location, country and/or sea=", "geo_location": "geo_location=",
        "geographic_location_country": "geographic location (country"}
res = {k: {"rows": 0, "resolved": 0, "examples": []} for k in KEYS}
res["_window_untagged_rows"] = 0

for f in sorted(glob.glob(str(RUN / "data" / "samples" / "*.parquet"))):
    import pyarrow.parquet as pq
    if "attributes_text" not in pq.read_schema(f).names:
        continue
    d = pd.read_parquet(f, columns=["submission_date", "country_class", "attributes_text"])
    d = d[(d.submission_date >= "2021-06-01") & (d.submission_date <= "2025-05-31") & (d.country_class != "usable")]
    d = d[d.attributes_text.notna()]
    res["_window_untagged_rows"] += len(d)
    for name, key in KEYS.items():
        m = d.attributes_text.str.contains(key, regex=False, na=False)
        if not m.any():
            continue
        sub = d.attributes_text[m]
        res[name]["rows"] += int(m.sum())
        vals = sub.str.extract(re.escape(key) + r"([^;]*)", expand=False).fillna("")
        rv = vals.map(lambda v: countries.resolve(v.split(":")[0].strip()))
        res[name]["resolved"] += int(rv.notna().sum())
        # verbatim attribute values are deliberately not recorded; counts only
        res[name]["examples"] = "redacted (counts only)"
    del d

(OUT / "attr_variant_scan.json").write_text(json.dumps(res, indent=1))
print(json.dumps(res, indent=1))
tot = sum(res[k]["resolved"] for k in KEYS)
print(f"\nuntagged window samples whose own record states a resolvable country under a non-geo_loc_name attribute: "
      f"{tot} ({100 * tot / max(1, res['_window_untagged_rows']):.4f}% of {res['_window_untagged_rows']} untagged "
      f"window rows with stored attributes)")
