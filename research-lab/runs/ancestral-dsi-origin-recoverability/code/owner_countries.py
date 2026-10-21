"""Country of each gold record's submitter, for the asymmetric-error secondary of limb 2 only (never evidence).

The BioSample owner and BioProject submitter names are matched to organisations with the ROR affiliation API (the
match ROR marks "chosen"); the organisation's country is mapped to the INSDC vocabulary. Unmatched names stay blank.
Writes data/gold/owner_countries.csv; the raw responses are cached in data/gold/ror_cache.json.
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import countries  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
GOLD = RUN / "data" / "gold"
CACHE = GOLD / "ror_cache.json"


def ror(name, cache):
    if name in cache:
        return cache[name]
    url = "https://api.ror.org/v2/organizations?affiliation=" + urllib.parse.quote(name)
    res = None
    for t in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "research"}), timeout=60) as r:
                res = json.loads(r.read())
            break
        except Exception as e:
            if "429" in str(e):
                time.sleep(120)
            else:
                time.sleep(5 * (t + 1))
    hit = None
    for it in (res or {}).get("items", []):
        if it.get("chosen"):
            loc = (it["organization"].get("locations") or [{}])[0].get("geonames_details", {})
            hit = {"ror": it["organization"]["id"], "country": loc.get("country_name")}
            break
    cache[name] = hit
    json.dump(cache, open(CACHE, "w"), indent=0)
    time.sleep(6.5)                     # unauthenticated ROR clients: 50 requests per 5 minutes
    return hit


def main():
    cache = json.load(open(CACHE)) if CACHE.exists() else {}
    o = pd.read_csv(GOLD / "owners.csv", keep_default_na=False)
    out = []
    for r in o.itertuples():
        row = {"record": r.record}
        for col, key in (("biosample_owner", "owner_country"), ("bioproject_submitter", "submitter_country")):
            name = (getattr(r, col) or "").strip()
            h = ror(name, cache) if name else None
            row[key] = (countries.resolve(h["country"]) or "") if h and h.get("country") else ""
        out.append(row)
    pd.DataFrame(out).to_csv(GOLD / "owner_countries.csv", index=False)
    d = pd.DataFrame(out)
    print(len(d), "records;", int((d.owner_country != "").sum()), "owner countries;",
          int(((d.owner_country != "") | (d.submitter_country != "")).sum()), "with either")


if __name__ == "__main__":
    main()
