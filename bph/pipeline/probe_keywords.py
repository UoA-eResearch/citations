"""Step 6: keyword probes for the gap check: which SciVal Topics do these keywords land in?

For each probe in bph/probes.local.txt if present (the SRA's own list; kept out of the repository), else
bph/probes.txt ("Label: term | term"), using Scopus for 2021-2025 (SciVal's
current five-year window):
  uoa_all    UoA (Scopus affiliation) publications whose title/abstract/keywords match any term
  uoa_pac    ... that also name the Pacific (the P and O lens terms)
  world_pac  publications anywhere matching the terms AND the Pacific terms
  share      uoa_pac / world_pac
  topics     SciVal Topics of the most relevant world_pac publications (up to SAMPLE) and of UoA's
             own publications on the theme (uoa_all, up to SAMPLE), each with its status against the SRA3 list
  in_sra     share of each sample that falls inside the SRA dataset (Topic or Cluster included)
  corpus     works in this atlas's verified corpus matching the terms (all years, any lens)
Scopus counts are search-level (not re-checked like the atlas), so UoA and world compare like with like.

Writes data/probes.json.
"""

import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import els  # noqa: E402
from lenses import LENS_O, LENS_P  # noqa: E402
from tagging import fold  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
WORK = Path(os.environ.get("BPH_WORK", "/mnt/data/ubuntu/bph-work"))
YEARS = "PUBYEAR > 2020 AND PUBYEAR < 2026"
YEARS_LABEL = "2021-2025"
SAMPLE = 200


def read_probes(path):
    probes = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        label, _, terms = line.partition(":")
        terms = [t.strip() for t in (terms or label).split("|") if t.strip()]
        probes.append(dict(label=label.strip(), terms=terms))
    return probes


def tak(terms):
    return "TITLE-ABS-KEY(" + " OR ".join(t if t.startswith('"') else f'"{t}"' for t in terms) + ")"


def search(q, count):
    r = els.get("/content/search/scopus", {"query": q, "count": count, "sort": "relevancy", "field": "dc:identifier"})
    sr = (r or {}).get("search-results", {})
    ids = [e["dc:identifier"].split(":")[1] for e in sr.get("entry", []) if "dc:identifier" in e]
    return int(sr.get("opensearch:totalResults", 0)), ids


def topics_of(ids):
    out = {}
    for i in range(0, len(ids), 100):
        r = els.get("/analytics/scival/publication/metrics", {"metricTypes": "CitationCount",
                    "publicationIds": ",".join(ids[i:i + 100]), "byYear": "false"})
        for x in (r or {}).get("results", []):
            p = x["publication"]
            if p.get("topicId") is not None:
                out[str(p["id"])] = (p["topicId"], p.get("topicName"), p.get("topicClusterId"), p.get("topicClusterName"))
    return out


def main():
    local = ROOT / "probes.local.txt"
    probes = read_probes(local if local.exists() else ROOT / "probes.txt")
    land = json.loads((ROOT / "data" / "landscape.json").read_text())
    live = json.loads((ROOT / "data" / "scival_live.json").read_text())
    sra_ids = json.loads((WORK / "els_sra_ids.json").read_text())
    sra = json.loads((ROOT / "data" / "scival_sra3.json").read_text())
    st_t = {int(k): sra[v]["final"] for k, v in sra_ids["topic"].items()}
    st_c = {int(k): sra[v]["final"] for k, v in sra_ids["cluster"].items()}
    tix = {t["id"]: k for k, t in enumerate(live["topics"])}

    def status(tid, cid):
        if st_t.get(tid) == "y" or st_c.get(cid) == "y":
            return "c"
        return "s" if (tid in st_t or cid in st_c) else "n"

    uoa_out = {t["id"]: t["uoa"] for t in live["topics"]}
    port = json.loads((WORK / "els_uoa_portfolio.json").read_text())
    for t in port["topics"]:
        uoa_out[t["id"]] = t["scholarlyOutput"]
    corpus_text = {}
    for line in open(WORK / "works_raw.jsonl"):
        w = json.loads(line)
        kw = " ; ".join(k.get("display_name") or "" for k in w.get("keywords") or [])
        inv = w.get("abstract_inverted_index") or {}
        words = sorted(((i, wd) for wd, idxs in inv.items() for i in idxs))
        corpus_text[w["id"].rsplit("/", 1)[-1]] = fold(f"{w.get('display_name') or ''} {' '.join(x for _, x in words)} {kw}")
    pac = tak(LENS_P + LENS_O)
    uoa = f"AF-ID({els.UOA_SCOPUS})"
    out = []
    for p in probes:
        terms = tak(p["terms"])
        uoa_all, uoa_ids = search(f"{uoa} AND {terms} AND {YEARS}", SAMPLE)
        uoa_pac, _ = search(f"{uoa} AND {terms} AND {pac} AND {YEARS}", 1)
        world_pac, world_ids = search(f"{terms} AND {pac} AND {YEARS}", SAMPLE)
        tw, tu = topics_of(world_ids), topics_of(uoa_ids)
        agg = {}
        for src, tt in (("w", tw), ("u", tu)):
            for tid, tname, cid, cname in tt.values():
                a = agg.setdefault(tid, dict(id=tid, name=tname, cluster=cname, w=0, u=0, st=status(tid, cid),
                                            uoa=uoa_out.get(tid, 0), ix=tix.get(tid, -1)))
                a[src] += 1
        top = sorted(agg.values(), key=lambda a: (-a["u"], -a["w"]))[:10]   # by UoA papers, then world
        in_w = sum(1 for tid, _, cid, _ in tw.values() if status(tid, cid) == "c")
        in_u = sum(1 for tid, _, cid, _ in tu.values() if status(tid, cid) == "c")
        rx = re.compile("|".join(r"\b" + re.escape(fold(t)) + r"(?:s|es)?\b" for t in p["terms"]))
        hits = [i for i, w in enumerate(land["works"]) if rx.search(corpus_text.get(w["id"], ""))]
        out.append(dict(
            label=p["label"], terms=p["terms"], uoa_all=uoa_all, uoa_pac=uoa_pac, world_pac=world_pac,
            share=round(100 * uoa_pac / world_pac, 2) if world_pac else None,
            n_w=len(tw), n_u=len(tu), in_w=in_w, in_u=in_u, topics=top,
            corpus=len(hits), corpus_focus=sum(1 for i in hits if land["works"][i]["tier"] == "f"),
            works=sorted(hits, key=lambda i: -land["works"][i]["c"])[:40]))
        print(f"{p['label']:36s} uoa={uoa_all:5d} uoa_pac={uoa_pac:4d} world_pac={world_pac:6d} "
              f"in SRA: world {in_w}/{len(tw)}, UoA {in_u}/{len(tu)} | top: {top[0]['name'][:50] if top else '-'}")
    (ROOT / "data" / "probes.json").write_text(json.dumps(dict(years=YEARS_LABEL, sample=SAMPLE, probes=out, local=local.exists()),
                                                          ensure_ascii=False, separators=(",", ":")))
    print("Elsevier calls:", els.stats())


if __name__ == "__main__":
    main()
