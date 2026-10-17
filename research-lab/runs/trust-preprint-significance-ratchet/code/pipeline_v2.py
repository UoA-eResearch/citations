"""Exploratory v2 pipeline (deviations D3.2): pipeline.py with extract_v2 (text repair, η²p exclusion, lost
exponents) and each statistic's rank, sentence count, offset in sentence and matched text kept. Same pairs, sections,
boilerplate filter and aligner (align.py, unchanged). Writes data/aligned_v2/. Crossing tallies are not printed here.
"""
import gzip
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import align as AL  # noqa: E402
import extract_v2 as X  # noqa: E402
import parse_jats as PJ  # noqa: E402
from pipeline import BOILER, USE, version_of  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
OUT = RUN / "data" / "aligned_v2"
KEEP = ("section", "kind", "test", "df", "stat", "cmp", "p", "sig", "sentence", "rank", "n_in_sent", "pos", "raw")


def stats_of(rec):
    out = []
    if rec.get("abstract"):
        out += X.extract(rec["abstract"], "abstract")
    for s in rec.get("sections", []):
        if s["type"] in USE and s["type"] != "abstract":
            out += X.extract(s["text"], s["type"])
    return [x for x in out if not BOILER.search(x["sentence"])]


def one(args):
    pair, pre_rec, xml_path = args
    try:
        root = etree.parse(str(xml_path), etree.XMLParser(recover=True, huge_tree=True)).getroot()
        art = root if root.tag == "article" else root.find(".//article")
        pub_rec = PJ.parse_article(art)
    except Exception as e:
        return pair, None, f"parse_error {e}"
    a, b = stats_of(pre_rec), stats_of(pub_rec)
    aligned, dropped, added = AL.align(a, b)
    slim = lambda x: {k: x[k] for k in KEEP}
    rows = [dict(pair=pair["preprint_doi"], status="aligned", how=p["how"], sim=p["sim"], cls=p["cls"],
                 pre=slim(p["pre"]), pub=slim(p["pub"])) for p in aligned]
    rows += [dict(pair=pair["preprint_doi"], status="dropped", pre=slim(x)) for x in dropped]
    rows += [dict(pair=pair["preprint_doi"], status="added", pub=slim(x)) for x in added]
    return pair, rows, dict(n_pre=len(a), n_pub=len(b), n_aligned=len(aligned))


def main():
    pairs = [json.loads(l) for l in open(RUN / "data" / "pairs_candidates.jsonl")]
    pmc = {json.loads(l)["doi"]: json.loads(l)["pmcid"] for l in open(RUN / "data" / "raw" / "links" / "doi_pmcid.jsonl")}
    pubdir = RUN / "data" / "raw" / "published"
    keep = {}
    for p in pairs:
        if p["confirmed"] and pmc.get(p["published_doi"]) and (pubdir / f"{pmc[p['published_doi']]}.xml").exists():
            keep.setdefault(p["preprint_doi"], p)
    pre = {}
    for l in gzip.open(RUN / "data" / "parsed" / "preprints.jsonl.gz", "rt"):
        r = json.loads(l)
        if r.get("doi") in keep:
            pre.setdefault(r["doi"], r)
    jobs = [(keep[d], pre[d], pubdir / f"{pmc[keep[d]['published_doi']]}.xml") for d in keep if d in pre]
    OUT.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUT / "statistics.jsonl.gz", "wt") as fs, open(OUT / "pairs.jsonl", "w") as fp, \
            ProcessPoolExecutor(24) as ex:
        for k, (pair, rows, info) in enumerate(ex.map(one, jobs, chunksize=16)):
            fp.write(json.dumps(dict(pair, version_used=version_of(pre[pair["preprint_doi"]]),
                                     info=info if rows is not None else None, error=None if rows is not None else info)) + "\n")
            for r in rows or []:
                fs.write(json.dumps(r, ensure_ascii=False) + "\n")
            if k % 2000 == 0:
                print("pairs", k, "/", len(jobs), flush=True)
    print("done", len(jobs), "pairs")


if __name__ == "__main__":
    sys.exit(main())
