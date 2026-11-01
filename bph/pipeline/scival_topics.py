"""Step 5: place every atlas work in SciVal and test it against the SRA3 Topic / Topic Cluster list.

A SciVal research area defined by Topics and Topic Clusters contains every publication in those
Topics plus every publication in those Clusters. So for a work with a SciVal Topic T in Cluster C:
  c  in the SRA dataset   T is an included Topic or C is an included Topic Cluster
  s  screened out         not included, but T or C was on the screened list and marked "n"
  n  never screened       neither T nor C was on the screened list (outside UoA's highest-performing
                          areas in 2020-2024, so the SRA screening never saw it)
  x  not in SciVal        no Scopus record (or no SciVal Topic yet), so SciVal cannot see it
The SRA3 workbook lists names only; they are matched to SciVal IDs by exact (normalised) name
against UoA's SciVal portfolio and the Topics of the works.

Also builds: the SciVal Topics holding the atlas's Pacific research (with UoA's SciVal metrics), the
Topics where Pacific Island countries publish most (with UoA's output in each), and Pacific-named
Topics in UoA's portfolio. Writes data/scival_live.json and $BPH_WORK/els_sra_ids.json.
"""

import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import els  # noqa: E402
from tagging import fold, ocean_hits, place_hits  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
WORK = Path(os.environ.get("BPH_WORK", "/mnt/data/ubuntu/bph-work"))
PIC_TABLE = 200   # Pacific Island country Topics kept for the opportunities table (by Pacific output)


def nname(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def pacific_named(name):
    hits, _ = place_hits(fold(name))
    return bool(hits) or ocean_hits(fold(name)) > 0


def load(name):
    return json.loads((WORK / name).read_text())


def main():
    land = json.loads((ROOT / "data" / "landscape.json").read_text())
    sra = json.loads((ROOT / "data" / "scival_sra3.json").read_text())
    ids, pubs = load("els_scopus_ids.json"), load("els_pubs.json")
    port, tmet, pics = load("els_uoa_portfolio.json"), load("els_uoa_topic_metrics.json"), load("els_pic_topics.json")
    works = land["works"]

    # ---- topic / cluster registries
    topics, clusters = {}, {}
    for t in port["topics"]:
        topics[t["id"]] = dict(name=t["name"], uoa=t["scholarlyOutput"], world=t["overallScholarlyOutput"],
                               prom=t["prominencePercentile"], cl=None)
    for c in port["clusters"]:
        clusters[c["id"]] = dict(name=c["name"], uoa=c["scholarlyOutput"], world=c["overallScholarlyOutput"],
                                 prom=c["prominencePercentile"], nt=c.get("topicCount"))
    for p in pubs.values():
        if p["topic"] is None:
            continue
        t = topics.setdefault(p["topic"], dict(name=p["topic_name"], uoa=0, world=None, prom=None, cl=None))
        t["cl"] = p["cluster"]
        if p["cluster"] is not None:
            clusters.setdefault(p["cluster"], dict(name=p["cluster_name"], uoa=0, world=None, prom=None, nt=None))
    pic_out = defaultdict(dict)   # topic -> {iso: output}
    for iso, c in pics.items():
        for t in c["topics"]:
            pic_out[t["id"]][iso] = t["scholarlyOutput"]
            topics.setdefault(t["id"], dict(name=t["name"], uoa=0, world=t["overallScholarlyOutput"],
                                            prom=t["prominencePercentile"], cl=None))
            if topics[t["id"]]["world"] is None:
                topics[t["id"]]["world"] = t["overallScholarlyOutput"]
                topics[t["id"]]["prom"] = t["prominencePercentile"]

    # ---- SRA3 names -> SciVal IDs
    t_by_name, c_by_name = defaultdict(list), defaultdict(list)
    for tid, t in topics.items():
        t_by_name[nname(t["name"])].append(tid)
    for cid, c in clusters.items():
        c_by_name[nname(c["name"])].append(cid)
    sra_topic, sra_cluster, unmatched, ambiguous = {}, {}, [], 0
    for j, r in enumerate(sra):
        pool = t_by_name if r["kind"] == "topic" else c_by_name
        reg = topics if r["kind"] == "topic" else clusters
        cand = pool.get(nname(r["name"]), [])
        if not cand:
            unmatched.append(j)
            r["sid"] = None
            continue
        if len(cand) > 1:
            ambiguous += 1
        sid = max(cand, key=lambda i: reg[i]["uoa"] or 0)   # the screening used UoA's own topics
        r["sid"] = sid
        (sra_topic if r["kind"] == "topic" else sra_cluster)[sid] = j
    print(f"SRA3 matched: topics {sum(1 for r in sra if r['kind'] == 'topic' and r['sid'] is not None)}/"
          f"{sum(1 for r in sra if r['kind'] == 'topic')}, clusters {sum(1 for r in sra if r['kind'] == 'cluster' and r['sid'] is not None)}/"
          f"{sum(1 for r in sra if r['kind'] == 'cluster')}; ambiguous {ambiguous}")
    for j in unmatched:
        print("  unmatched:", sra[j]["kind"], sra[j]["final"], sra[j]["name"])

    # Clusters of the Topics that matter but whose Cluster is not yet known (SRA3 Topics, PIC table).
    def status(tid, cid):
        jt, jc = sra_topic.get(tid), sra_cluster.get(cid)
        if (jt is not None and sra[jt]["final"] == "y") or (jc is not None and sra[jc]["final"] == "y"):
            return "c"
        if jt is not None or jc is not None:
            return "s"
        return "n"

    pic_rank = sorted(pic_out, key=lambda t: -sum(pic_out[t].values()))[:PIC_TABLE]
    need_cl = [t for t in set(pic_rank) | set(sra_topic) if topics[t]["cl"] is None]
    for tid in need_cl:
        r = els.get(f"/analytics/scival/topic/{tid}")
        tc = ((r or {}).get("topic") or {}).get("topicCluster")
        if tc:
            topics[tid]["cl"] = tc["id"]
            clusters.setdefault(tc["id"], dict(name=tc["name"], uoa=0, world=tc.get("scholarlyOutput"),
                                               prom=tc.get("prominencePercentile"), nt=tc.get("topicCount")))
    print("cluster lookups:", len(need_cl), els.stats())
    # World output and prominence for Topics known only through a work (e.g. Topics of 2026 papers
    # outside UoA's 2021-2025 portfolio).
    need_w = sorted(t for t in {p["topic"] for p in pubs.values() if p["topic"] is not None} if topics[t]["world"] is None)
    for i in range(0, len(need_w), 100):
        r = els.get("/analytics/scival/topic/metrics", {"topicIds": ",".join(map(str, need_w[i:i + 100])),
                                                       "metricTypes": "ScholarlyOutput", "yearRange": "5yrs"})
        for x in (r or {}).get("results", []):
            t = x["topic"]
            if t["id"] in topics:
                topics[t["id"]]["world"] = t.get("overallScholarlyOutput", t.get("scholarlyOutput"))
                topics[t["id"]]["prom"] = t.get("prominencePercentile")
    print("world output filled for", len(need_w), "Topics;", sum(1 for t in need_w if topics[t]["world"] is None), "still missing")

    # ---- per work
    wsv = []
    for w in works:
        sid, how = ids.get(w["id"], [None, None])
        p = pubs.get(sid) if sid else None
        if not p or p["topic"] is None:
            wsv.append(dict(sid=sid, how=how, t=None, st="x", fwci=p["fwci"] if p else None, top10=p["top10"] if p else None))
            continue
        wsv.append(dict(sid=sid, how=how, t=p["topic"], st=status(p["topic"], p["cluster"]), fwci=p["fwci"], top10=p["top10"]))
    focus = [k for k, w in enumerate(works) if w["tier"] == "f"]
    print("Scopus record:", sum(1 for x in wsv if x["sid"]), "/", len(works), "| focus:", sum(1 for k in focus if wsv[k]["sid"]), "/", len(focus))
    print("status (all):", Counter(x["st"] for x in wsv))
    print("status (focus):", Counter(wsv[k]["st"] for k in focus))
    print("status (A only):", Counter(x["st"] for x, w in zip(wsv, works) if not w["tier"]))

    # ---- compact tables for the page: topics referenced by works, SRA3, PIC table, Pacific-named UoA topics
    pac_named_uoa = [t for t in topics if topics[t]["uoa"] and pacific_named(topics[t]["name"])]
    keep_t = sorted({x["t"] for x in wsv if x["t"] is not None} | set(sra_topic) | set(pic_rank) | set(pac_named_uoa))
    tix = {t: k for k, t in enumerate(keep_t)}
    keep_c = sorted({topics[t]["cl"] for t in keep_t if topics[t]["cl"] is not None} | set(sra_cluster))
    cix = {c: k for k, c in enumerate(keep_c)}
    out_topics = []
    for t in keep_t:
        x = topics[t]
        m = tmet.get(str(t), {})
        po = pic_out.get(t, {})
        out_topics.append(dict(
            id=t, name=x["name"], cl=cix.get(x["cl"], -1), uoa=x["uoa"], world=x["world"],
            prom=round(x["prom"], 1) if x["prom"] is not None else None,
            sra=sra_topic.get(t, -1), st=status(t, x["cl"]), pac=pacific_named(x["name"]),
            fwci=m.get("FieldWeightedCitationImpact"), share=m.get("PublicationShare"),
            growth=m.get("PublicationShareGrowth") if (m.get("PublicationShareGrowth") or 0) < 1e30 else None,
            pic=sum(po.values()), picc=sorted(po.items(), key=lambda kv: -kv[1])[:4]))
    out_clusters = [dict(id=c, name=clusters[c]["name"], uoa=clusters[c]["uoa"], world=clusters[c]["world"],
                         prom=round(clusters[c]["prom"], 1) if clusters[c]["prom"] is not None else None,
                         sra=sra_cluster.get(c, -1)) for c in keep_c]
    sra_ids = [dict(j=j, kind=r["kind"], sid=r["sid"],
                    ix=(tix.get(r["sid"], -1) if r["kind"] == "topic" else cix.get(r["sid"], -1)) if r["sid"] is not None else -1)
               for j, r in enumerate(sra)]
    (WORK / "els_sra_ids.json").write_text(json.dumps(dict(topic={str(k): v for k, v in sra_topic.items()},
                                                          cluster={str(k): v for k, v in sra_cluster.items()})))
    pic_tot = {iso: dict(name=c["name"], n=sum(t["scholarlyOutput"] for t in c["topics"]), topics=len(c["topics"])) for iso, c in pics.items()}
    out = dict(
        years=port["years"], works=[[x["sid"], tix.get(x["t"], -1), x["st"], x["fwci"], x["top10"], x["how"]] for x in wsv],
        topics=out_topics, clusters=out_clusters, sra=sra_ids, pic_rank=[tix[t] for t in pic_rank],
        pac_named=[tix[t] for t in pac_named_uoa], pic_countries=pic_tot,
        uoa=dict(topics=len(port["topics"]), clusters=len(port["clusters"])),
        unmatched=[sra[j]["name"] for j in unmatched])
    (ROOT / "data" / "scival_live.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    print(f"wrote scival_live.json: {len(out_topics)} topics, {len(out_clusters)} clusters, "
          f"{len(pac_named_uoa)} Pacific-named UoA topics")


if __name__ == "__main__":
    main()
