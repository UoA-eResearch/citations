"""Reviewer's live API probes (gentle: one request at a time, 1 s apart, cached). Writes probes.json and probes.md.
Run: venv/bin/python -I review/reviewer_checks/probe_api.py   (from the run directory)"""
import hashlib, json, sys, time
from pathlib import Path
import requests

HERE = Path(__file__).resolve().parent
CACHE = HERE / "cache"; CACHE.mkdir(exist_ok=True)
RUN = HERE.parents[1]
S = requests.Session(); S.headers["User-Agent"] = "research-lab review (mailto:noreply@anthropic.com)"
N = 0

def get(url, params=None, headers=None, label=""):
    global N
    key = hashlib.sha1(json.dumps([url, params, headers], sort_keys=True).encode()).hexdigest()[:16]
    f = CACHE / f"{key}.json"
    if f.exists():
        return json.load(open(f))
    N += 1
    try:
        r = S.get(url, params=params, headers=headers, timeout=60)
        out = dict(label=label, url=r.url, status=r.status_code, body=r.text[:400000])
    except Exception as e:
        out = dict(label=label, url=url, params=params, status=None, body=str(e)[:300])
    json.dump(out, open(f, "w"))
    time.sleep(1.0)
    return out

def dc_total(q, size=1, label=""):
    r = get("https://api.datacite.org/dois", {"query": q, "page[size]": size}, label=label or q)
    try:
        j = json.loads(r["body"]); return r["status"], j["meta"]["total"], [d["id"] for d in j["data"]]
    except Exception:
        return r["status"], None, r["body"][:200]

census_dois = {json.loads(l)["doi"].lower() for l in open(RUN / "data" / "census.jsonl") if json.loads(l)["doi"]}
raw_dc = set()
for l in open(RUN / "data" / "raw" / "datacite" / "records.jsonl"):
    raw_dc.add(json.loads(l)["id"].lower())
res = {}

# ---- DataCite query variants ------------------------------------------------------------
NOTNEO = " AND NOT prefix:10.21233"
dcq = [("d1_rightsUri_wild", "rightsList.rightsUri:*localcontexts*", 1),
       ("d2_rightsUri_wild_notneo", "rightsList.rightsUri:*localcontexts*" + NOTNEO, 200),
       ("d3_token_localcontexts", "localcontexts", 1),
       ("d4_phrase_hub_domain", '"localcontextshub.org"', 200),
       ("d5_phrase_lc_domain", '"localcontexts.org"' + NOTNEO, 200),
       ("d6_any_wild_notneo", "*localcontexts*" + NOTNEO, 200),
       ("d7_desc_wild_notneo", "descriptions.description:*localcontexts*" + NOTNEO, 200),
       ("d8_related_wild", "relatedIdentifiers.relatedIdentifier:*localcontexts*", 200),
       ("d9a_identifiers_wild", "identifiers.identifier:*localcontexts*", 200),
       ("d9b_altid_wild", "alternateIdentifiers.alternateIdentifier:*localcontexts*", 200),
       ("d10_subjects_wild", "subjects.subject:*localcontexts*", 200),
       ("d11_rights_text_wild_notneo", "rightsList.rights:*localcontexts*" + NOTNEO, 200),
       ("d12_scheme_LC_notneo", 'rightsList.rightsIdentifierScheme:"Local Contexts"' + NOTNEO, 200),
       ("d12b_scheme_LC_all", 'rightsList.rightsIdentifierScheme:"Local Contexts"', 1),
       ("d13_BC_Provenance", '"BC Provenance"', 200),
       ("d14_TK_Attribution", '"TK Attribution"', 200),
       ("d15_Attribution_Incomplete", '"Attribution Incomplete"', 200),
       ("d16_Open_to_Collaborate_notneo", '"Open to Collaborate"' + NOTNEO, 200),
       ("d17_subjects_phrase_LC", 'subjects.subject:"Local Contexts"', 200),
       ("d18_token_hub", "localcontextshub", 200),
       ("d19_phrase_LC_total", '"Local Contexts"', 1),
       ("d20_BC_Notice_phrase_notneo", '"BC Notice"' + NOTNEO, 1),
       ]
for k, q, size in dcq:
    st, tot, ids = dc_total(q, size, k)
    novel = sorted(i for i in (ids if isinstance(ids, list) else []) if i.lower() not in raw_dc)
    res[k] = dict(query=q, status=st, total=tot, n_returned=len(ids) if isinstance(ids, list) else 0,
                  not_in_raw_census=novel[:50], n_not_in_raw=len(novel), in_census=sum(1 for i in (ids if isinstance(ids, list) else []) if i.lower() in census_dois))
    print(k, st, tot, "novel:", len(novel), novel[:5], flush=True)

# the two figshare (VUW) DOIs as DataCite records
for d in ["10.26686/wgtn.25790481", "10.26686/wgtn.28974539"]:
    r = get(f"https://api.datacite.org/dois/{d}", label=f"dc_record_{d}")
    try:
        a = json.loads(r["body"])["data"]["attributes"]
        s = json.dumps(a, ensure_ascii=False)
        res[f"dc_record_{d}"] = dict(status=r["status"], has_localcontexts=("localcontexts" in s.lower()), has_phrase=("local contexts" in s.lower()),
                                      subjects=[x.get("subject") for x in a.get("subjects", [])][:30], rightsList=a.get("rightsList"),
                                      n_descriptions=len(a.get("descriptions", [])), desc_has_lc=any("local contexts" in (x.get("description") or "").lower() for x in a.get("descriptions", [])))
    except Exception:
        res[f"dc_record_{d}"] = dict(status=r["status"], body=r["body"][:300])
    print(f"dc_record_{d}", res[f"dc_record_{d}"].get("status"), res[f"dc_record_{d}"].get("has_localcontexts"), res[f"dc_record_{d}"].get("subjects"), flush=True)

# ---- Local Contexts Hub projects: what is actually applied there? ------------------------
us = json.load(open(RUN / "data" / "uri_status.json"))
projects = [u.split("/projects/")[1].strip("/") for u in us if "/projects/" in u]
hub = {}
for i, p in enumerate(projects):
    r = get(f"https://localcontextshub.org/api/v1/projects/{p}/", headers={"Accept": "application/json"}, label=f"hub_{p}")
    entry = dict(status=r["status"], uri_status=us.get(f"https://localcontextshub.org/projects/{p}/"))
    try:
        j = json.loads(r["body"])
        entry.update(title=j.get("title"), project_privacy=j.get("project_privacy"), date_added=j.get("date_added"),
                     notices=[(n.get("notice_type") or n.get("name")) for n in (j.get("notice") or [])],
                     bc_labels=[(l.get("label_type") or l.get("name")) for l in (j.get("bc_labels") or [])],
                     tk_labels=[(l.get("label_type") or l.get("name")) for l in (j.get("tk_labels") or [])],
                     created_by=[(c.get("institution") or {}).get("institution_name") or (c.get("community") or {}).get("community_name") or (c.get("researcher") or {}).get("user", {}).get("username") for c in (j.get("created_by") or [])],
                     keys=sorted(j.keys())[:40])
    except Exception:
        entry["body"] = r["body"][:300]
    hub[p] = entry
    print("hub", p[:8], entry.get("status"), entry.get("title"), "notices", entry.get("notices"), "bc", entry.get("bc_labels"), "tk", entry.get("tk_labels"), flush=True)
res["hub_projects"] = hub

# ---- Harvard Dataverse ---------------------------------------------------------------------
r = get("https://dataverse.harvard.edu/api/metadatablocks", label="dv_blocks")
try:
    blocks = [b["name"] + ":" + b.get("displayName", "") for b in json.loads(r["body"])["data"]]
except Exception:
    blocks = r["body"][:300]
res["dv_metadatablocks"] = dict(status=r["status"], blocks=blocks)
print("dv blocks", blocks, flush=True)
for k, q in [("dv_q_hubdomain", "localcontextshub.org"), ("dv_q_wild", "localcontexts*"), ("dv_q_phrase", '"Local Contexts"'), ("dv_q_token", "localcontexts"), ("dv_q_hubtoken", "localcontextshub")]:
    r = get("https://dataverse.harvard.edu/api/search", {"q": q, "type": "dataset", "per_page": 10}, label=k)
    try:
        j = json.loads(r["body"])["data"]; res[k] = dict(q=q, status=r["status"], total=j["total_count"], items=[(x.get("global_id"), x.get("name")) for x in j["items"]][:10])
    except Exception:
        res[k] = dict(q=q, status=r["status"], body=r["body"][:200])
    print(k, res[k].get("total"), flush=True)

# ---- Zenodo --------------------------------------------------------------------------------
for k, params in [("z1_token", {"q": "localcontexts", "size": 1}), ("z2_hubdomain", {"q": '"localcontextshub.org"', "size": 1}),
                  ("z3_rights_link", {"q": 'metadata.rights.link:"https://localcontextshub.org/projects/54be05d7-aa5c-4886-abd9-dc45b2fa8df4"', "size": 1}),
                  ("z4_rights_title", {"q": 'metadata.rights.title.en:"BC-Notice"', "size": 1}),
                  ("z5_token_allversions", {"q": "localcontexts", "size": 1, "allversions": "true"})]:
    r = get("https://zenodo.org/api/records", params, label=k)
    try:
        j = json.loads(r["body"]); res[k] = dict(params=params, status=r["status"], total=j["hits"]["total"], first=[h.get("doi") for h in j["hits"]["hits"]])
    except Exception:
        res[k] = dict(params=params, status=r["status"], body=r["body"][:200])
    print(k, res[k].get("total"), res[k].get("status"), flush=True)
r = get("https://zenodo.org/api/records/10381317", headers={"Accept": "application/vnd.inveniordm.v1+json"}, label="z6_record_rdm")
try:
    j = json.loads(r["body"]); res["z6_record_10381317_rdm"] = dict(status=r["status"], rights=j.get("metadata", {}).get("rights"), has_lc=("localcontextshub" in r["body"]))
except Exception:
    res["z6_record_10381317_rdm"] = dict(status=r["status"], body=r["body"][:200])
print("z6", res["z6_record_10381317_rdm"], flush=True)
r = get("https://zenodo.org/api/records/10381317", label="z7_record_legacy")
res["z7_record_10381317_legacy"] = dict(status=r["status"], has_lc_hub=("localcontextshub" in r["body"]), has_bc_notice=("BC-Notice" in r["body"]))
print("z7", res["z7_record_10381317_legacy"], flush=True)

# ---- GBIF ----------------------------------------------------------------------------------
for k, url, params in [("g1_mt_ns_lc", "https://api.gbif.org/v1/dataset", {"machineTagNamespace": "localcontexts.org", "limit": 1}),
                       ("g2_mt_ns_hub", "https://api.gbif.org/v1/dataset", {"machineTagNamespace": "localcontextshub.org", "limit": 1}),
                       ("g3_q_hub", "https://api.gbif.org/v1/dataset/search", {"q": "localcontextshub", "limit": 5}),
                       ("g4_q_tk_label", "https://api.gbif.org/v1/dataset/search", {"q": "Traditional Knowledge Label", "limit": 5})]:
    r = get(url, params, label=k)
    try:
        j = json.loads(r["body"]); res[k] = dict(status=r["status"], count=j.get("count"), titles=[x.get("title") for x in j.get("results", [])][:5])
    except Exception:
        res[k] = dict(status=r["status"], body=r["body"][:200])
    print(k, res[k], flush=True)

# ---- RAiD ----------------------------------------------------------------------------------
r = get("https://api.raid.org/raid/10.26259/488751", label="a1_raid_single")
try:
    j = json.loads(r["body"]); res["a1_raid_single_keys"] = dict(status=r["status"], keys=sorted(j.keys()), has_tk=("traditionalKnowledgeLabel" in j))
except Exception:
    res["a1_raid_single_keys"] = dict(status=r["status"], body=r["body"][:200])
print("a1", res["a1_raid_single_keys"], flush=True)
r = get("https://api.raid.org/raid/", {"limit": 1}, label="a2_raid_list")
try:
    j = json.loads(r["body"]); res["a2_raid_list"] = dict(status=r["status"], pageInfo=j.get("pageInfo"), keys=sorted(j.keys()))
except Exception:
    res["a2_raid_list"] = dict(status=r["status"], body=r["body"][:200])
print("a2", res["a2_raid_list"], flush=True)

# ---- re3data -------------------------------------------------------------------------------
import re as _re
for k, q in [("e1_neotoma", "Neotoma"), ("e2_pollen", "pollen"), ("e3_indigenous", "Indigenous"), ("e4_localcontexts", "localcontexts")]:
    r = get("https://www.re3data.org/api/beta/repositories", {"query": q}, label=k)
    ids = _re.findall(r"<id>(r3d\d+)</id>", r["body"]); names = _re.findall(r"<name>([^<]{0,80})</name>", r["body"])
    res[k] = dict(q=q, status=r["status"], n=len(ids), names=names[:8])
    print(k, res[k], flush=True)

# ---- OSF -----------------------------------------------------------------------------------
r = get("https://share.osf.io/api/v3/index-card-search", {"cardSearchText": "localcontexts", "page[size]": 5}, headers={"Accept": "application/vnd.api+json"}, label="o1_share")
res["o1_share"] = dict(status=r["status"], body=r["body"][:300])
print("o1", r["status"], flush=True)
r = get("https://api.osf.io/v2/search/", {"q": "localcontexts"}, label="o2_osf_search")
res["o2_osf_v2_search"] = dict(status=r["status"], body=r["body"][:300])
print("o2", r["status"], r["body"][:150], flush=True)
r = get("https://api.osf.io/v2/nodes/", {"filter[description]": "localcontexts", "page[size]": 5}, label="o3_osf_nodes_desc")
res["o3_osf_nodes_desc"] = dict(status=r["status"], body=r["body"][:300])
print("o3", r["status"], r["body"][:150], flush=True)

# ---- OpenAIRE: are the 'unavailable' Neotoma DOIs still not indexed? -----------------------
V = [json.loads(l) for l in open(RUN / "data" / "views.jsonl")]
unav = [v["doi"] for v in V if v["view"] == "openaire" and v["result"] == "unavailable"]
import random
rnd = random.Random(7); pick = rnd.sample(unav, 3)
oa = {}
for d in pick:
    r = get("https://api.openaire.eu/graph/v1/researchProducts", {"pid": d}, label=f"oa_{d}")
    try:
        oa[d] = dict(status=r["status"], numFound=json.loads(r["body"])["header"]["numFound"])
    except Exception:
        oa[d] = dict(status=r["status"], body=r["body"][:200])
    print("oa", d, oa[d], flush=True)
res["openaire_unavailable_recheck"] = oa

res["_n_live_requests_this_run"] = N
json.dump(res, open(HERE / "probes.json", "w"), indent=1, default=str)
print("live requests this run:", N)
