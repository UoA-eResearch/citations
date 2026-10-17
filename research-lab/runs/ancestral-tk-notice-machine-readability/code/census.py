"""Limb 1 census (plan section 2). For each platform, every search term is queried and every returned record's full
metadata is saved (data/raw/<platform>/records.jsonl), then scanned with detect.py. Writes data/census.jsonl, one row
per element-bearing record: platform, id, doi, publisher/client, year, type, detected elements, channel
(structured = a URI in a rights field; text = anywhere else). Polite: 1 request at a time, 0.5-1 s apart."""
import json
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from detect import any_element, detect  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
S = requests.Session(); S.headers["User-Agent"] = "research-lab metadata study (mailto:noreply@anthropic.com)"
TERMS = ["localcontexts", "\"Local Contexts\"", "\"TK Notice\"", "\"Traditional Knowledge Notice\"", "\"BC Notice\"",
         "\"Biocultural Notice\"", "\"TK Label\"", "\"Traditional Knowledge Label\"", "\"Biocultural Label\"", "\"BC Label\""]


def get(url, **kw):
    for k in range(5):
        try:
            r = S.get(url, timeout=120, **kw)
            if r.status_code == 200:
                return r
            if r.status_code in (404, 400):
                return r
        except Exception:
            pass
        time.sleep(3 * (k + 1))
    return None


def save(platform, recs):
    d = RAW / platform; d.mkdir(parents=True, exist_ok=True)
    with open(d / "records.jsonl", "w") as fh:
        for r in recs.values():
            fh.write(json.dumps(r) + "\n")
    return recs


def datacite():
    recs = {}
    queries = ["rightsList.rightsUri:*localcontexts*"] + TERMS
    for q in queries:
        url = "https://api.datacite.org/dois"
        params = {"query": q, "page[size]": 1000, "page[cursor]": 1}
        while url:
            r = get(url, params=params)
            if r is None or r.status_code != 200:
                break
            j = r.json()
            for x in j["data"]:
                recs.setdefault(x["id"], dict(platform="datacite", id=x["id"], query=q, meta=x))
            url = j.get("links", {}).get("next"); params = None
            time.sleep(0.5)
    return save("datacite", recs)


def zenodo():
    recs = {}
    for q in TERMS:
        page = 1
        while True:
            r = get("https://zenodo.org/api/records", params={"q": q, "size": 100, "page": page})
            if r is None or r.status_code != 200:
                break
            hits = r.json()["hits"]["hits"]
            for x in hits:
                recs.setdefault(str(x["id"]), dict(platform="zenodo", id=str(x["id"]), query=q, meta=x))
            if len(hits) < 100 or page >= 100:
                break
            page += 1; time.sleep(1)
    return save("zenodo", recs)


def dryad():
    recs = {}
    for q in TERMS:
        page = 1
        while True:
            r = get("https://datadryad.org/api/v2/search", params={"q": q, "per_page": 100, "page": page})
            if r is None or r.status_code != 200:
                break
            items = r.json().get("_embedded", {}).get("stash:datasets", [])
            for x in items:
                recs.setdefault(x["identifier"], dict(platform="dryad", id=x["identifier"], query=q, meta=x))
            if len(items) < 100:
                break
            page += 1; time.sleep(1)
    return save("dryad", recs)


def dataverse():
    recs = {}
    for q in TERMS:
        start = 0
        while True:
            r = get("https://dataverse.harvard.edu/api/search", params={"q": q, "type": "dataset", "per_page": 100, "start": start})
            if r is None or r.status_code != 200:
                break
            items = r.json()["data"]["items"]
            for x in items:
                pid = x.get("global_id")
                if pid and pid not in recs:
                    full = get("https://dataverse.harvard.edu/api/datasets/:persistentId/", params={"persistentId": pid})
                    recs[pid] = dict(platform="dataverse", id=pid, query=q, meta=x, full=full.json() if full is not None and full.status_code == 200 else None)
                    time.sleep(0.5)
            if len(items) < 100:
                break
            start += 100; time.sleep(1)
    return save("dataverse", recs)


def figshare():
    recs = {}
    for q in TERMS:
        page = 1
        while True:
            try:
                r = S.post("https://api.figshare.com/v2/articles/search", json={"search_for": q, "page_size": 100, "page": page}, timeout=120)
            except Exception:
                break
            if r.status_code != 200:
                break
            items = r.json()
            for x in items:
                k = str(x["id"])
                if k not in recs:
                    full = get(x["url_public_api"])
                    recs[k] = dict(platform="figshare", id=k, query=q, meta=full.json() if full is not None and full.status_code == 200 else x)
                    time.sleep(0.5)
            if len(items) < 100 or page >= 50:
                break
            page += 1; time.sleep(1)
    return save("figshare", recs)


def gbif():
    recs = {}
    for q in TERMS:
        off = 0
        while True:
            r = get("https://api.gbif.org/v1/dataset/search", params={"q": q, "limit": 100, "offset": off})
            if r is None or r.status_code != 200:
                break
            res = r.json()["results"]
            for x in res:
                if x["key"] not in recs:
                    full = get(f"https://api.gbif.org/v1/dataset/{x['key']}")
                    recs[x["key"]] = dict(platform="gbif", id=x["key"], query=q, meta=full.json() if full is not None and full.status_code == 200 else x)
                    time.sleep(0.3)
            if len(res) < 100:
                break
            off += 100; time.sleep(1)
    return save("gbif", recs)


def raid():
    r = get("https://api.raid.org/raid/")
    recs = {}
    if r is not None and r.status_code == 200:
        for x in r.json().get("raids", []):
            k = (x.get("identifier") or {}).get("id")
            recs[k] = dict(platform="raid", id=k, query="all", meta=x)
    return save("raid", recs)


def osf():
    recs = {}
    for q in TERMS:
        r = get("https://share.osf.io/api/v3/index-card-search", params={"cardSearchText": q, "page[size]": 100}, headers={"Accept": "application/json"})
        if r is None or r.status_code != 200:
            recs.setdefault("_unavailable", dict(platform="osf", id="_unavailable", query=q, meta=dict(status=None if r is None else r.status_code)))
            continue
        for x in r.json().get("data", []):
            recs.setdefault(str(x.get("id")), dict(platform="osf", id=str(x.get("id")), query=q, meta=x))
        time.sleep(1)
    return save("osf", recs)


def re3data():
    recs = {}
    for q in ["localcontexts", "\"Local Contexts\"", "\"Traditional Knowledge\" Label"]:
        r = get("https://www.re3data.org/api/beta/repositories", params={"query": q})
        if r is not None and r.status_code == 200:
            import re as _re
            for rid in _re.findall(r"<id>(r3d\d+)</id>", r.text):
                if rid not in recs:
                    full = get(f"https://www.re3data.org/api/beta/repository/{rid}")
                    recs[rid] = dict(platform="re3data", id=rid, query=q, meta=dict(xml=full.text if full is not None else None))
                    time.sleep(0.5)
    return save("re3data", recs)


PLATFORMS = dict(datacite=datacite, zenodo=zenodo, dryad=dryad, dataverse=dataverse, figshare=figshare, gbif=gbif,
                 raid=raid, osf=osf, re3data=re3data)


def scan():
    out = []
    for p in PLATFORMS:
        f = RAW / p / "records.jsonl"
        if not f.exists():
            continue
        for l in open(f):
            r = json.loads(l)
            if r["id"] == "_unavailable":
                continue
            m = r["meta"]
            text = json.dumps(r.get("full") or m, ensure_ascii=False)
            det = detect(text)
            if not any_element(det):
                continue
            rights = json.dumps(((m.get("attributes") or {}).get("rightsList")) if p == "datacite" else
                                (m.get("license") or m.get("rights") or m.get("metadata", {}).get("rights") or ""), ensure_ascii=False)
            a = m.get("attributes") or {}
            out.append(dict(platform=p, id=r["id"], doi=(a.get("doi") or m.get("doi") or ""),
                            publisher=(a.get("publisher") if isinstance(a.get("publisher"), str) else (a.get("publisher") or {}).get("name") if a else m.get("publisher") or ""),
                            client=((m.get("relationships") or {}).get("client") or {}).get("data", {}).get("id") if p == "datacite" else "",
                            year=a.get("publicationYear") or str(m.get("publication_date") or m.get("published_date") or m.get("publicationDate") or "")[:4],
                            rtype=((a.get("types") or {}).get("resourceTypeGeneral") or ""), structured=bool(detect(rights)["uri_labels"] or detect(rights)["uri_notices"] or detect(rights)["hub_projects"]),
                            **det))
    with open(RUN / "data" / "census.jsonl", "w") as fh:
        for x in out:
            fh.write(json.dumps(x) + "\n")
    from collections import Counter
    print(len(out), "element-bearing records", dict(Counter(x["platform"] for x in out)))


if __name__ == "__main__":
    if sys.argv[1] == "scan":
        sys.exit(scan())
    for p in sys.argv[1:]:
        recs = PLATFORMS[p](); print(p, len(recs), "records fetched", flush=True)
