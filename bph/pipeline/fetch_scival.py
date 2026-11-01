"""Step 4: fetch the SciVal view of the landscape (Scopus + SciVal APIs, University subscription).

1. Scopus ID of each atlas work: DOI lookup in batches of 25, then an exact-title fallback
   (TITLE phrase + publication year +-1, accepted only when the normalised titles are equal).
2. SciVal Topic, Topic Cluster, FWCI and top-10% citation percentile of each matched work
   (publication metrics endpoint, 100 IDs per call).
3. UoA's SciVal portfolio: every Topic and Topic Cluster with UoA output (last 5 complete years),
   world output and Prominence percentile. (The API's keyContribOnly filter returned every Topic, so
   "key contributing Topics" are not used.)
4. UoA's SciVal metrics (output, FWCI, publication share and growth) for each Topic holding at least
   MIN_FOCUS Pacific-focused atlas works: the five criteria of the SRA dataset methodology.
5. The Topic portfolios of Pacific Island countries and territories (where Pacific research happens).

Writes intermediates to $BPH_WORK (els_*.json). Re-runs are free (responses cached by els.py).
"""

import json
import os
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import els  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
WORK = Path(os.environ.get("BPH_WORK", "/mnt/data/ubuntu/bph-work"))
YEARS = "5yrs"   # SciVal's last five complete years (2021-2025 at the October 2026 data release)
MIN_FOCUS = 2
# Pacific Island countries and territories as SciVal "countries" (Hawai'i is a US state: not separable).
PICS = ["FJI", "PNG", "WSM", "ASM", "TON", "VUT", "SLB", "KIR", "TUV", "COK", "NIU", "TKL", "MHL", "FSM",
        "PLW", "NRU", "GUM", "MNP", "NCL", "PYF", "WLF", "PCN"]
PIC_NAMES = {"FJI": "Fiji", "PNG": "Papua New Guinea", "WSM": "Samoa", "ASM": "American Samoa", "TON": "Tonga",
             "VUT": "Vanuatu", "SLB": "Solomon Islands", "KIR": "Kiribati", "TUV": "Tuvalu", "COK": "Cook Islands",
             "NIU": "Niue", "TKL": "Tokelau", "MHL": "Marshall Islands", "FSM": "Micronesia",
             "PLW": "Palau", "NRU": "Nauru", "GUM": "Guam", "MNP": "Northern Mariana Islands",
             "NCL": "New Caledonia", "PYF": "French Polynesia", "WLF": "Wallis and Futuna", "PCN": "Pitcairn"}


_APOS = re.compile(r"[’‘'`ʻ]")


def norm_title(s, apos=""):
    """Lower-case ASCII words. Apostrophes are dropped (for comparing) or spaced (for querying)."""
    s = unicodedata.normalize("NFKD", _APOS.sub(apos, s or ""))
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def scopus_by_doi(works):
    """{work id: scopus id} for works whose DOI is in Scopus."""
    out = {}
    todo = [(w["id"], w["doi"].replace("https://doi.org/", "").lower()) for w in works if w.get("doi")]
    for i in range(0, len(todo), 25):
        chunk = todo[i:i + 25]
        # Characters that break a quoted Scopus phrase are rare in DOIs; such DOIs fall back to title.
        ok = [(wid, d) for wid, d in chunk if '"' not in d and "\\" not in d]
        q = " OR ".join(f'DOI("{d}")' for _, d in ok)
        r = els.get("/content/search/scopus", {"query": q, "count": 25, "field": "dc:identifier,prism:doi"})
        found = {}
        for e in (r or {}).get("search-results", {}).get("entry", []):
            if "dc:identifier" in e and e.get("prism:doi"):
                found.setdefault(e["prism:doi"].lower(), e["dc:identifier"].split(":")[1])
        for wid, d in ok:
            if d in found:
                out[wid] = found[d]
    return out


def scopus_by_title(w):
    """Scopus ID for a work by exact (normalised) title and publication year +-1, or None.

    Two searches: the title as a phrase, then all its words of 4+ letters ANDed (the phrase search
    misses titles with apostrophes or odd punctuation). Either way a hit is accepted only when the
    normalised titles are identical, so a reply, protocol or erratum with a similar title is not taken.
    """
    t = norm_title(w["t"])
    if len(t) < 25:          # short titles match too loosely
        return None
    y = int(w["y"])
    years = f"PUBYEAR > {y - 2} AND PUBYEAR < {y + 2}"
    words = [x for x in norm_title(w["t"], " ").split() if len(x) > 3][:10]
    queries = [f'TITLE("{" ".join(t.split()[:30])}") AND {years}']
    if len(words) >= 3:
        queries.append(f"TITLE({' AND '.join(words)}) AND {years}")
    for q in queries:
        r = els.get("/content/search/scopus", {"query": q, "count": 25, "field": "dc:identifier,dc:title,prism:coverDate"})
        hits = [e for e in (r or {}).get("search-results", {}).get("entry", []) if "dc:identifier" in e]
        exact = [e for e in hits if norm_title(e.get("dc:title")) == t]
        exact.sort(key=lambda e: str(e.get("prism:coverDate", ""))[:4] != str(y))   # same year first
        if exact:
            return exact[0]["dc:identifier"].split(":")[1]
    return None


def pub_metrics(ids):
    out = {}
    ids = sorted(set(ids))
    for i in range(0, len(ids), 100):
        r = els.get("/analytics/scival/publication/metrics", {
            "metricTypes": "FieldWeightedCitationImpact,OutputsInTopCitationPercentiles,CitationCount",
            "publicationIds": ",".join(ids[i:i + 100]), "byYear": "false"})
        for x in (r or {}).get("results", []):
            p = x["publication"]
            m = {k["metricType"]: k for k in x["metrics"]}
            top = {v["threshold"]: v.get("value") for v in m.get("OutputsInTopCitationPercentiles", {}).get("values", [])}
            out[str(p["id"])] = dict(
                topic=p.get("topicId"), topic_name=p.get("topicName"), cluster=p.get("topicClusterId"),
                cluster_name=p.get("topicClusterName"), year=p.get("publicationYear"), type=p.get("type"),
                source=p.get("sourceTitle"), fwci=m.get("FieldWeightedCitationImpact", {}).get("value"),
                top10=top.get(10), cites=m.get("CitationCount", {}).get("value"))
    return out


def listing(path, key, **params):
    rows, off = [], 0
    while True:
        r = els.get(path, dict(params, limit=100, offset=off))
        page = (r or {}).get(key, [])
        rows += page
        off += 100
        if not page or off >= (r or {}).get("totalCount", 0):
            return rows


def main():
    land = json.loads((ROOT / "data" / "landscape.json").read_text())
    works = land["works"]

    by_doi = scopus_by_doi(works)       # cached calls: re-runs are free
    ids = {}
    for w in works:
        if w["id"] in by_doi:
            ids[w["id"]] = [by_doi[w["id"]], "doi"]
        else:
            s = scopus_by_title(w)
            ids[w["id"]] = [s, "title"] if s else [None, None]
    (WORK / "els_scopus_ids.json").write_text(json.dumps(ids))
    print("Scopus match:", Counter(v[1] for v in ids.values()))

    pubs = pub_metrics([v[0] for v in ids.values() if v[0]])
    (WORK / "els_pubs.json").write_text(json.dumps(pubs))
    print("SciVal pubs:", len(pubs), "with topic:", sum(1 for p in pubs.values() if p["topic"] is not None))

    uoa_t = listing(f"/analytics/scival/topic/institutionId/{els.UOA_SCIVAL}", "topics", yearRange=YEARS)
    uoa_c = listing(f"/analytics/scival/topicCluster/institutionId/{els.UOA_SCIVAL}", "topicClusters", yearRange=YEARS)
    (WORK / "els_uoa_portfolio.json").write_text(json.dumps(dict(years=YEARS, topics=uoa_t, clusters=uoa_c)))
    print("UoA portfolio: topics", len(uoa_t), "clusters", len(uoa_c))

    # UoA metrics per Topic for topics holding >= MIN_FOCUS Pacific-focused works.
    focus_topics = Counter()
    for w in works:
        s = ids.get(w["id"], [None])[0]
        if w["tier"] == "f" and s and pubs.get(s, {}).get("topic") is not None:
            focus_topics[pubs[s]["topic"]] += 1
    tm, source = {}, None
    for tid, n in focus_topics.items():
        if n < MIN_FOCUS:
            continue
        r = els.get(f"/analytics/scival/topic/metrics/institutionId/{els.UOA_SCIVAL}", {
            "topicId": tid, "yearRange": YEARS,
            "metricTypes": "ScholarlyOutput,FieldWeightedCitationImpact,PublicationShare,PublicationShareGrowth,CitationCount"})
        source = source or (r or {}).get("dataSource")
        for x in (r or {}).get("results", []):
            m = {k["metricType"]: k.get("value") for k in x["metrics"]}
            tm[str(tid)] = dict(m, prominence=x["topic"].get("prominencePercentile"), world=x["topic"].get("overallScholarlyOutput"))
    (WORK / "els_uoa_topic_metrics.json").write_text(json.dumps(tm))
    (WORK / "els_meta.json").write_text(json.dumps(dict(source=source, years=YEARS)))   # e.g. Scopus, lastUpdated, 2021-2025
    print("UoA topic metrics for", len(tm), "topics with >=", MIN_FOCUS, "focus works")

    countries = {}
    for iso in PICS:
        r = els.get("/analytics/scival/country/search", {"query": f"name({PIC_NAMES[iso]})", "limit": 10})
        hit = [c for c in (r or {}).get("results", []) if c.get("countryCode") == iso]
        if not hit:
            print("  no SciVal country for", iso)
            continue
        cid = hit[0]["id"]
        countries[iso] = dict(id=cid, name=hit[0]["name"],
                              topics=listing(f"/analytics/scival/topic/countryId/{cid}", "topics", yearRange=YEARS))
        print(f"  {iso} {hit[0]['name']}: {len(countries[iso]['topics'])} topics")
    (WORK / "els_pic_topics.json").write_text(json.dumps(countries))
    print("Elsevier calls:", els.stats())


if __name__ == "__main__":
    main()
