"""Second, small batch of live probes (cached like the first): is the VUW DOI registered in the handle system though absent from
DataCite's public index; does a general Zenodo rights-link query work; re3data totals; RAiD total count."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import probe_api as P   # reuses get() and the cache (the module body re-runs from cache, no new requests)
HERE = Path(__file__).resolve().parent
res = {}
for d in ["10.26686/wgtn.25790481", "10.26686/wgtn.28974539"]:
    r = P.get(f"https://doi.org/api/handles/{d}", label=f"handle_{d}")
    try:
        j = json.loads(r["body"]); res[f"handle_{d}"] = dict(status=r["status"], responseCode=j.get("responseCode"), url=[v["data"]["value"] for v in j.get("values", []) if v.get("type") == "URL"])
    except Exception:
        res[f"handle_{d}"] = dict(status=r["status"], body=r["body"][:200])
    r = P.get("https://api.datacite.org/dois", {"query": f'doi:"{d}"', "page[size]": 1}, label=f"dcq_{d}")
    try:
        res[f"datacite_query_doi_{d}"] = dict(status=r["status"], total=json.loads(r["body"])["meta"]["total"])
    except Exception:
        res[f"datacite_query_doi_{d}"] = dict(status=r["status"], body=r["body"][:200])
r = P.get("https://zenodo.org/api/records", {"q": "metadata.rights.link:*localcontexts*", "size": 5}, label="z8_rights_link_wild")
try:
    j = json.loads(r["body"]); res["z8_rights_link_wild"] = dict(status=r["status"], total=j["hits"]["total"], dois=[h.get("doi") for h in j["hits"]["hits"]])
except Exception:
    res["z8_rights_link_wild"] = dict(status=r["status"], body=r["body"][:200])
r = P.get("https://zenodo.org/api/records", {"q": "metadata.rights.link:*localcontexts*", "size": 5, "allversions": "true"}, label="z9_rights_link_wild_allv")
try:
    j = json.loads(r["body"]); res["z9_rights_link_wild_allversions"] = dict(status=r["status"], total=j["hits"]["total"], dois=[h.get("doi") for h in j["hits"]["hits"]])
except Exception:
    res["z9_rights_link_wild_allversions"] = dict(status=r["status"], body=r["body"][:200])
r = P.get("https://api.raid.org/raid/", {"limit": 1}, label="a2_raid_list")
res["raid_totalCount"] = json.loads(r["body"]).get("totalCount")
res["_n_live_requests_this_run"] = P.N
json.dump(res, open(HERE / "probes2.json", "w"), indent=1)
print(json.dumps(res, indent=1))
