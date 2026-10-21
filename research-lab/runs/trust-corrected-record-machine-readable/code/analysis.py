"""Plan section 3: H1-H3 and secondaries 1-6, from the fetched snapshot files.

  analysis.py parse   parse every fetched document once -> data/parsed.parquet
  analysis.py run     hypotheses and secondaries -> results/tables/primary.json, secondary.json

Intervals: cluster bootstrap over journals (ISSN from the XML, else the Retraction Watch journal name, else the
document itself), 2,000 resamples, seed 20261022, on per-journal sums.
"""
import concurrent.futures as cf
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import markers  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
FILES = RUN / "data" / "files"
TAB = RUN / "results" / "tables"
SEED, B = 20261022, 2000
S = pd.Timestamp("2026-10-21")


def journal_meta(data):
    try:
        root = etree.fromstring(data, parser=etree.XMLParser(recover=True, huge_tree=True, resolve_entities=False,
                                                              no_network=True))
    except Exception:
        return None, None
    if root is None:
        return None, None
    issn = pub = None
    for el in root.iter():
        t = markers._local(el.tag)
        if t == "issn" and issn is None and any(markers._local(a.tag) == "journal-meta" for a in el.iterancestors()):
            issn = (el.text or "").strip() or None
        elif t == "publisher-name" and pub is None:
            pub = " ".join(" ".join(el.itertext()).split()) or None
        if issn and pub:
            break
    return issn, pub


def parse_one(pmcid):
    out = {"pmcid": pmcid}
    jp, xp, tp = (FILES / f"{pmcid}.{e}" for e in ("json", "xml", "txt"))
    if jp.exists():
        m = json.loads(jp.read_bytes())
        out.update(json_present=True, sidecar_flag=bool(m.get("is_retracted")), is_manuscript=bool(m.get("is_manuscript")),
                   license=m.get("license_code"))
    else:
        out.update(json_present=False)
    if xp.exists():
        b = xp.read_bytes()
        x = markers.xml_markers(b)
        issn, pub = journal_meta(b)
        out.update(xml_present=True, xml_structured=x["structured"], xml_textual=x["textual"],
                   xml_kinds=";".join(x["kinds"]), article_type=x.get("article_type", ""), issn=issn, xml_publisher=pub)
    else:
        out.update(xml_present=False)
    if tp.exists():
        t = markers.txt_markers(tp.read_bytes().decode("utf-8", "replace"))
        out.update(txt_present=True, txt_textual=t["textual"], txt_kinds=";".join(t["kinds"]))
    else:
        out.update(txt_present=False)
    return out


def parse():
    d = pd.read_parquet(RUN / "data" / "cohort.parquet")
    d = d[d.in_snapshot & ~d.notice & d.stratum.isin(["primary", "recent", "undated"])]
    with cf.ProcessPoolExecutor(16) as ex:
        rows = list(ex.map(parse_one, d.pmcid, chunksize=200))
    p = pd.DataFrame(rows)
    p.to_parquet(RUN / "data" / "parsed.parquet", index=False)
    print(len(p), "parsed;", int(p.xml_present.sum()), "with XML;", int(p.txt_present.sum()), "with text")


def boot(cluster, k, n=None, seed=SEED):
    """Share sum(k)/sum(n) and its cluster-bootstrap 95% interval; k may be a difference (then n counts documents)."""
    df = pd.DataFrame({"c": cluster, "k": k, "n": np.ones(len(k)) if n is None else n})
    g = df.groupby("c")[["k", "n"]].sum()
    K, N = g.k.to_numpy(float), g.n.to_numpy(float)
    rng = np.random.default_rng(seed)
    w = rng.multinomial(len(g), np.full(len(g), 1 / len(g)), size=B).astype(float)
    est = K.sum() / N.sum()
    bs = (w @ K) / (w @ N)
    return {"estimate": round(float(est), 4), "ci": [round(float(np.percentile(bs, 2.5)), 4),
                                                     round(float(np.percentile(bs, 97.5)), 4)],
            "n": int(N.sum()), "clusters": int(len(g))}


def rule(r, thr, above=True):
    lo, hi = r["ci"]
    if above:
        return "Supported" if lo > thr else "Refuted" if hi < thr else "Inconclusive"
    return "Supported" if lo >= thr else "Refuted" if hi < thr else "Inconclusive"


def frame():
    c = pd.read_parquet(RUN / "data" / "cohort.parquet")
    p = pd.read_parquet(RUN / "data" / "parsed.parquet")
    d = c.merge(p, on="pmcid", how="inner")
    d["notice_type"] = d.article_type.fillna("").str.lower().eq("retraction")
    d["cluster"] = d.issn.fillna(d.journal).fillna("doc:" + d.pmcid)
    d["xml_marked"] = d.xml_structured.fillna(False) | d.xml_textual.fillna(False)
    d["publisher_name"] = d.publisher.fillna(d.xml_publisher).fillna("unknown")
    return d


def run():
    d = frame()
    out = {"documents_parsed": len(d), "notice_type_excluded": int(d.notice_type.sum())}
    d = d[~d.notice_type]
    C = d[(d.stratum == "primary") & d.xml_present.fillna(False)]
    out["primary_cohort"] = len(C)
    out["primary_without_xml"] = int(((d.stratum == "primary") & ~d.xml_present.fillna(False)).sum())
    h1 = boot(C.cluster, (~C.xml_marked).astype(float))
    out["H1_unmarked_share"], out["H1"] = h1, rule(h1, 0.50, above=True)
    Cj = C[C.json_present.fillna(False)]
    h2 = boot(Cj.cluster, Cj.sidecar_flag.astype(float))
    out["H2_sidecar_flag_share"], out["H2"] = h2, rule(h2, 0.90, above=False)
    Ct = C[C.txt_present.fillna(False)]
    diff = Ct.xml_marked.astype(float) - Ct.txt_textual.fillna(False).astype(float)
    h3 = boot(Ct.cluster, diff)
    h3["xml_marked_share"] = round(float(Ct.xml_marked.mean()), 4)
    h3["txt_marked_share"] = round(float(Ct.txt_textual.fillna(False).mean()), 4)
    out["H3_xml_minus_txt"], out["H3"] = h3, rule(h3, 0.05, above=False)
    json.dump(out, open(TAB / "primary.json", "w"), indent=1)
    sec = {}
    # 1. marker kinds, publishers, retraction years
    kinds = C.xml_kinds.fillna("").str.split(";").explode()
    sec["marker_kinds_share_of_C"] = (kinds[kinds != ""].value_counts() / len(C)).round(4).to_dict()
    sec["structured_share"] = round(float(C.xml_structured.mean()), 4)
    sec["textual_only_share"] = round(float((C.xml_textual & ~C.xml_structured).mean()), 4)
    top = C.publisher_name.value_counts().head(15).index
    sec["by_publisher"] = {pb: {"n": int((C.publisher_name == pb).sum()),
                                "unmarked": round(float((~C[C.publisher_name == pb].xml_marked).mean()), 4),
                                "sidecar_flag": round(float(C[C.publisher_name == pb].sidecar_flag.fillna(False).mean()), 4)}
                           for pb in top}
    C = C.assign(year=C.date.dt.year)
    sec["by_retraction_year"] = C.groupby("year").agg(n=("pmcid", "size"), unmarked=("xml_marked", lambda s: round(float((~s).mean()), 4)),
                                                      sidecar=("sidecar_flag", lambda s: round(float(s.fillna(False).mean()), 4))) \
        .to_dict(orient="index")
    hind = C.publisher_name.str.contains("Hindawi", case=False)
    sec["hindawi_vs_rest"] = {"hindawi": boot(C[hind].cluster, (~C[hind].xml_marked).astype(float)) if hind.any() else None,
                              "rest": boot(C[~hind].cluster, (~C[~hind].xml_marked).astype(float))}
    # 2. latency for recent retractions
    R = d[(d.stratum == "recent") & d.xml_present.fillna(False)].copy()
    R["months"] = ((S - R.date).dt.days // 30).clip(0, 5)
    sec["recent_by_months_since_retraction"] = R.groupby("months").agg(
        n=("pmcid", "size"), xml_marked=("xml_marked", lambda s: round(float(s.mean()), 4)),
        sidecar=("sidecar_flag", lambda s: round(float(s.fillna(False).mean()), 4))).to_dict(orient="index")
    # 3. undated stratum
    U = d[(d.stratum == "undated") & d.xml_present.fillna(False)]
    sec["undated"] = {"n": len(U), "unmarked": round(float((~U.xml_marked).mean()), 4) if len(U) else None,
                      "sidecar_flag": round(float(U.sidecar_flag.fillna(False).mean()), 4) if len(U) else None,
                      "layers": U[["rw", "crossref", "pubmed", "openalex"]].sum().astype(int).to_dict(),
                      "openalex_only": int((U.openalex & ~U.pubmed).sum())}
    # 4. registry composition in C
    lay = C[["rw", "crossref", "pubmed", "openalex"]]
    sec["layers_in_C"] = lay.sum().astype(int).to_dict()
    sec["layer_patterns_in_C"] = lay.astype(int).astype(str).agg("".join, axis=1).value_counts().head(16).to_dict()
    # 5. versions
    sec["version_in_C"] = C.version.value_counts().sort_index().astype(int).to_dict()
    sec["unmarked_by_version"] = C.groupby(C.version.clip(upper=3)).xml_marked.apply(lambda s: round(float((~s).mean()), 4)).to_dict()
    # 6. sidecar x XML
    sec["sidecar_by_xml"] = pd.crosstab(C.sidecar_flag.fillna(False), C.xml_marked).to_dict()
    sec["neither_marker_nor_flag"] = int((~C.xml_marked & ~C.sidecar_flag.fillna(False)).sum())
    sec["is_manuscript_in_C"] = int(C.is_manuscript.fillna(False).sum())
    json.dump(sec, open(TAB / "secondary.json", "w"), indent=1, default=str)
    keep = ["pmcid", "doi", "pmid", "stratum", "date", "rw", "crossref", "pubmed", "openalex", "version", "publisher_name",
            "issn", "xml_present", "xml_structured", "xml_textual", "xml_kinds", "txt_present", "txt_textual", "txt_kinds",
            "json_present", "sidecar_flag", "is_manuscript"]
    d[keep].to_csv(TAB / "documents.csv.gz", index=False)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    {"parse": parse, "run": run}[sys.argv[1]]()
