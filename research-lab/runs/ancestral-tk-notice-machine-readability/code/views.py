"""Limb 2 crosswalk fidelity (plan section 3). Sample: up to 2,000 element-bearing DataCite DOIs - all non-Neotoma
(prefix != 10.21233) up to 1,500, then Neotoma at random to fill (seed 20261021). For each DOI, fetch nine machine
views and score each: preserve / degrade / drop / unavailable.
  views: doi.org content negotiation (DataCite XML, schema.org JSON-LD, Crosscite JSON, CSL-JSON, BibTeX, formatted
         citation), DataCite OAI-PMH oai_dc and oai_datacite, the OpenAIRE Graph record.
  preserve  the element's URI or name is in a rights/terms-type field, distinguishable from the licence
  degrade   present only merged into the licence field (e.g. JSON-LD 'license') or in free text
  drop      absent;   unavailable  no record returned (excluded from H2's denominator)
1 request at a time, 0.5 s apart. Writes data/views.jsonl (one row per DOI x view, raw body saved gzipped)."""
import gzip
import json
import random
import re
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from detect import any_element, detect  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
S = requests.Session(); S.headers["User-Agent"] = "research-lab metadata study (mailto:noreply@anthropic.com)"
CN = {"datacite_xml": "application/vnd.datacite.datacite+xml", "schemaorg_jsonld": "application/vnd.schemaorg.ld+json",
      "crosscite_json": "application/vnd.crosscite.crosscite+json", "csl_json": "application/vnd.citationstyles.csl+json",
      "bibtex": "application/x-bibtex", "citation_text": "text/x-bibliography"}
RIGHTS_FIELD = {"datacite_xml": r"<rights\b[^>]*>.*?</rights>|<rights\b[^>]*/>", "oai_datacite": r"<rights\b[^>]*>.*?</rights>|<rights\b[^>]*/>",
                "crosscite_json": r'"rights_?[lL]ist"\s*:\s*\[.*?\]', "oai_dc": r"<dc:rights>.*?</dc:rights>",
                "schemaorg_jsonld": r'"(?:license|usageInfo|conditionsOfAccess|copyrightNotice)"\s*:\s*(?:"[^"]*"|\[.*?\]|\{.*?\})',
                "csl_json": r'"(?:license|rights)"\s*:\s*(?:"[^"]*"|\[.*?\])', "openaire": r'"(?:bestAccessRight|license|rights|accessRights)".{0,800}'}
LICENCE_ONLY = {"schemaorg_jsonld"}     # JSON-LD carries rights only in 'license': present there = merged into the licence


def fetch(doi, view):
    try:
        if view in CN:
            r = S.get(f"https://doi.org/{doi}", headers={"Accept": CN[view]}, timeout=60, allow_redirects=True)
        elif view in ("oai_dc", "oai_datacite"):
            r = S.get("https://oai.datacite.org/oai", params={"verb": "GetRecord", "identifier": f"doi:{doi}", "metadataPrefix": view}, timeout=60)
        else:
            r = S.get("https://api.openaire.eu/graph/v1/researchProducts", params={"pid": doi}, timeout=60)
        return r.status_code, r.text
    except Exception as e:
        return None, str(e)[:200]


def json_rights(view, body):
    """D5: rights entries by parsing (regex windows mis-scored 3 views: a ']' inside rights text; an 800-character
    window after 'license' reaching instances[].urls)."""
    try:
        j = json.loads(body)
    except Exception:
        return None
    if view == "crosscite_json":
        return json.dumps(j.get("rights_list") or j.get("rightsList") or [], ensure_ascii=False)
    if view == "openaire":
        res = j.get("results") or []
        parts = []
        for x in res:
            parts.append(x.get("bestAccessRight"))
            for ins in x.get("instances") or []:
                parts += [ins.get("license"), ins.get("accessRight")]
        return json.dumps(parts, ensure_ascii=False)
    return None


def score(view, status, body):
    if status != 200 or not body or ("idDoesNotExist" in body) or (view == "openaire" and '"numFound":0' in body.replace(" ", "")):
        return "unavailable"
    if not any_element(detect(body)):
        return "drop"
    fld = RIGHTS_FIELD.get(view)
    jr = json_rights(view, body) if view in ("crosscite_json", "openaire") else None
    if jr is not None:
        in_rights = any_element(detect(jr))
    else:
        in_rights = bool(fld) and any(any_element(detect(m)) for m in re.findall(fld, body, re.S | re.I))
    if in_rights and view not in LICENCE_ONLY:
        return "preserve"
    return "degrade"


def sample():
    rows = [json.loads(l) for l in open(RUN / "data" / "census.jsonl")]
    dois = sorted({r["doi"].lower() for r in rows if r["platform"] == "datacite" and r["doi"]})
    non = [d for d in dois if not d.startswith("10.21233/")]
    neo = [d for d in dois if d.startswith("10.21233/")]
    rnd = random.Random(20261021)
    pick = (rnd.sample(non, min(1500, len(non))) if len(non) > 1500 else non)
    pick += rnd.sample(neo, min(len(neo), 2000 - len(pick)))
    return pick


def main():
    out = RUN / "data" / "views.jsonl"; raw = RUN / "data" / "raw" / "views"; raw.mkdir(parents=True, exist_ok=True)
    done = {(json.loads(l)["doi"], json.loads(l)["view"]) for l in open(out)} if out.exists() else set()
    views = list(CN) + ["oai_dc", "oai_datacite", "openaire"]
    with open(out, "a") as fh:
        for k, doi in enumerate(sample()):
            for v in views:
                if (doi, v) in done:
                    continue
                st, body = fetch(doi, v)
                (raw / f"{doi.replace('/', '_')}__{v}.gz").write_bytes(gzip.compress((body or "").encode()))
                warn = bool(re.search(r"(rights|licen[cs]e)[^.]{0,40}(omitted|removed|not (shown|included))", body or "", re.I))
                fh.write(json.dumps(dict(doi=doi, view=v, status=st, result=score(v, st, body), warning=warn)) + "\n"); fh.flush()
                time.sleep(0.5)
            if k % 100 == 0:
                print("views", k, flush=True)
    print("views done", flush=True)


if __name__ == "__main__":
    sys.exit(main())
