"""Fetch the registry layers that are not downloaded as files (plan section 1), all on one day.

  Crossref   retraction notices (filter update-type:retraction) with their update-to targets
  PubMed     PMIDs of "Retracted Publication" [pt], split by publication year (E-utilities caps a query at 9,999)
  OpenAlex   works with is_retracted = true (id, doi, pmid, pmcid)

Writes data/raw/crossref_notices.jsonl, data/raw/pubmed_retracted.txt, data/raw/openalex_retracted.jsonl and
data/raw/registry_fetch_log.json. Retraction Watch is the Crossref Labs CSV in data/raw/retraction_watch.csv.
"""
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
MAILTO = "noreply@anthropic.com"


def get(url, tries=6):
    for t in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": f"research (mailto:{MAILTO})"}),
                                        timeout=120) as r:
                return json.loads(r.read())
        except Exception as e:
            print("retry", t, repr(e)[:120], flush=True)
            time.sleep(5 * (t + 1))
    raise RuntimeError(f"failed: {url[:120]}")


def crossref():
    out, cursor, n = open(RAW / "crossref_notices.jsonl", "w"), "*", 0
    while True:
        u = ("https://api.crossref.org/works?filter=update-type:retraction&rows=1000&select=DOI,update-to,created,type"
             f"&cursor={urllib.parse.quote(cursor)}&mailto={MAILTO}")
        m = get(u)["message"]
        for it in m["items"]:
            out.write(json.dumps(it) + "\n")
        n += len(m["items"])
        print("crossref", n, "/", m["total-results"], flush=True)
        if not m["items"]:
            break
        cursor = m["next-cursor"]
    out.close()
    return n


def pubmed():
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&retmax=9999&term="
    ids = set()

    def q(lo, hi):
        term = urllib.parse.quote(f'retracted publication[pt] AND ("{lo}"[dp] : "{hi}"[dp])')
        r = get(base + term)["esearchresult"]
        time.sleep(0.4)
        return int(r["count"]), r["idlist"]

    for y in range(1940, 2027):
        c, idl = q(f"{y}/01/01", f"{y}/12/31")
        if c > 9999:
            for mth in range(1, 13):
                c2, idl2 = q(f"{y}/{mth:02d}/01", f"{y}/{mth:02d}/31")
                assert c2 <= 9999, (y, mth, c2)
                ids.update(idl2)
        else:
            ids.update(idl)
    total = int(get(base.replace("retmax=9999", "retmax=0") + urllib.parse.quote("retracted publication[pt]"))
                ["esearchresult"]["count"])
    open(RAW / "pubmed_retracted.txt", "w").write("\n".join(sorted(ids, key=int)) + "\n")
    print("pubmed", len(ids), "of", total, flush=True)
    return len(ids), total


def openalex():
    key = open(Path.home() / ".config" / "openalex" / "api_key").read().strip()
    out, cursor, n = open(RAW / "openalex_retracted.jsonl", "w"), "*", 0
    while cursor:
        u = ("https://api.openalex.org/works?filter=is_retracted:true&per-page=200&select=id,doi,ids,publication_year"
             f"&cursor={urllib.parse.quote(cursor)}&api_key={key}")
        m = get(u)
        for it in m["results"]:
            ids = it.get("ids") or {}
            out.write(json.dumps({"id": it["id"], "doi": it.get("doi"), "pmid": ids.get("pmid"),
                                  "pmcid": ids.get("pmcid"), "year": it.get("publication_year")}) + "\n")
        n += len(m["results"])
        if n % 10000 < 200:
            print("openalex", n, "/", m["meta"]["count"], flush=True)
        cursor = m["meta"].get("next_cursor") if m["results"] else None
    out.close()
    return n


def main():
    log = {"fetched_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    log["crossref_notices"] = crossref()
    log["pubmed_ids"], log["pubmed_total"] = pubmed()
    log["openalex_works"] = openalex()
    json.dump(log, open(RAW / "registry_fetch_log.json", "w"), indent=1)
    print(log)


if __name__ == "__main__":
    main()
