"""Step 3: classify, aggregate and lay out the University of Auckland's Pacific research -> data/landscape.json.

Inputs: <WORK>/works_raw.jsonl, institutions.json, awards_raw.jsonl (fetch_works.py, fetch_awards.py).
Every candidate is re-checked with tagging.classify(); see that docstring for the tiers and lenses.
Metrics follow SciVal's vocabulary where OpenAlex has an equivalent: scholarly output, growth,
Field-Weighted Citation Impact (OpenAlex fwci) and share of outputs in the top 10% most cited
(OpenAlex citation_normalized_percentile). Complete years are 2020-2025; 2026 is partial.
"""

import hashlib
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import networkx as nx
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from tagging import (FACULTIES, PLACES, abstract_text, classify, faculty_of, fold,  # noqa: E402
                     uoa_affiliation_strings)

ROOT = Path(__file__).resolve().parents[1]
WORK = Path(os.environ.get("BPH_WORK", "/mnt/data/ubuntu/bph-work"))
OUT = ROOT / "data" / "landscape.json"
UOA = "I154130895"
PI_CC = set("AS CK FJ FM GU KI MH MP NC NR NU PF PG PN PW SB TK TO TV VU WF WS".split())
TODAY = date.today().isoformat()
COMPLETE = (2020, 2025)
TIER_CODE = {"focus": "f", "population": "p", "mention": "m", None: ""}
LENS_BIT = {"P": 1, "O": 2, "A": 4}


def short(oid):
    return str(oid or "").rsplit("/", 1)[-1]


def region_of(cc, lat=None, lng=None):
    if cc in PI_CC:
        return "Pacific Islands"
    if cc == "NZ":
        return "Aotearoa NZ"
    if cc == "AU":
        return "Australia"
    if cc in ("US", None) and lat is not None and 18 < lat < 23 and -161 < (lng or 0) < -154:
        return "Hawaiʻi"
    return "Elsewhere"


def is_uoa(authorship):
    for i in authorship.get("institutions") or []:
        if short(i.get("id")) == UOA or any(short(x) == UOA for x in i.get("lineage") or []):
            return True
    return False


def main():
    raw = [json.loads(l) for l in open(WORK / "works_raw.jsonl")]
    insts_geo = json.loads((WORK / "institutions.json").read_text())
    awards_raw = [json.loads(l) for l in open(WORK / "awards_raw.jsonl")]

    # ------------------------------------------------------------ classify works
    works, dropped, no_abs_dropped = [], 0, 0
    seen = set()
    for w in raw:
        wid = short(w["id"])
        if wid in seen:
            continue
        seen.add(wid)
        aus = w.get("authorships") or []
        partner = any(i.get("country_code") in PI_CC for a in aus for i in a.get("institutions") or [])
        kw = " ; ".join(k.get("display_name") or "" for k in w.get("keywords") or [])
        pt = w.get("primary_topic") or {}
        field = (pt.get("field") or {}).get("display_name")
        abstract = abstract_text(w.get("abstract_inverted_index"))
        c = classify(w.get("display_name"), abstract, kw, field, len(aus), partner)
        if not c["tier"] and "A" not in c["lenses"]:
            dropped += 1
            no_abs_dropped += not abstract
            continue
        w["_c"], w["_abstract"], w["_partner"] = c, abstract, partner
        works.append(w)
    print(f"{len(works)} works kept, {dropped} candidates dropped ({no_abs_dropped} had no abstract)")

    # ------------------------------------------------------------ vocabularies
    topics, topic_idx = [], {}
    def topic_i(pt):
        if not pt:
            return -1
        tid = short(pt["id"])
        if tid not in topic_idx:
            topic_idx[tid] = len(topics)
            topics.append(dict(id=tid, name=pt["display_name"], sub=(pt.get("subfield") or {}).get("display_name"),
                               field=(pt.get("field") or {}).get("display_name"),
                               domain=(pt.get("domain") or {}).get("display_name")))
        return topic_idx[tid]

    insts, inst_idx = [], {}
    def inst_i(iid):
        if iid not in inst_idx:
            g = insts_geo.get(iid) or {}
            inst_idx[iid] = len(insts)
            insts.append(dict(id=iid, name=g.get("name") or iid, cc=g.get("country"), city=g.get("city"),
                              lat=g.get("lat"), lng=g.get("lng"), type=g.get("type"),
                              region=region_of(g.get("country"), g.get("lat"), g.get("lng"))))
        return inst_idx[iid]
    uoa_i = inst_i(UOA)

    authors, auth_idx = [], {}
    funders, funder_idx = [], {}

    # ------------------------------------------------------------ awards (public records)
    awards = []
    award_idx = {}
    for a in awards_raw:
        text_desc = a.get("description") or ""
        c = classify(a.get("display_name"), text_desc, "", None, 0, False)
        li = a.get("lead_investigator") or {}
        name = " ".join(x for x in [li.get("given_name"), li.get("family_name")] if x) or None
        end = a.get("end_date") or (f"{a['end_year']}-12-31" if a.get("end_year") else None)
        status = "active" if end and end >= TODAY else ("ended" if end else "unknown")
        award_idx[short(a["id"])] = len(awards)
        awards.append(dict(
            id=short(a["id"]), t=a.get("display_name") or "(untitled award)", d=(text_desc[:420] + "…") if len(text_desc) > 420 else text_desc,
            f=(a.get("funder") or {}).get("display_name"), scheme=a.get("funder_scheme"), amt=a.get("amount"),
            cur=a.get("currency"), usd=a.get("amount_usd"), y0=a.get("start_year"), end=end, status=status,
            lead=name, url=a.get("landing_page_url"), fid=a.get("funder_award_id"),
            tier=TIER_CODE[c["tier"]], lens=sum(LENS_BIT[l] for l in c["lenses"]), ev=c["evidence"],
            places=sorted(c["places"]), outputs=a.get("funded_outputs_count") or 0, route=a.get("_route")))

    # ------------------------------------------------------------ works -> records
    out_works = []
    unit_fac_pairs = Counter()
    for w in works:
        c = w["_c"]
        aus = w.get("authorships") or []
        uoa_auth, ext = [], set()
        for a in aus:
            au = a.get("author") or {}
            for i in a.get("institutions") or []:
                iid = short(i.get("id"))
                if iid and iid != UOA and not any(short(x) == UOA for x in i.get("lineage") or []):
                    ext.add(inst_i(iid))
            if not is_uoa(a) or not au.get("id"):
                continue
            aid = short(au["id"])
            if aid not in auth_idx:
                auth_idx[aid] = len(authors)
                authors.append(dict(id=aid, name=au.get("display_name") or a.get("raw_author_name") or aid,
                                    orcid=au.get("orcid"), works=[], fac=Counter(), unit=Counter()))
            ai = auth_idx[aid]
            raws = uoa_affiliation_strings(a, UOA)
            fac, unit = faculty_of(raws)
            if fac:
                authors[ai]["fac"][fac] += 1
            if unit:
                authors[ai]["unit"][unit] += 1
            for s in raws:
                f = fold(s)
                m = re.search(r"faculty of [a-z &]+", f)
                if m and unit:
                    unit_fac_pairs[(unit, m.group(0).strip())] += 1
            if ai not in uoa_auth:
                uoa_auth.append(ai)
                authors[ai]["works"].append(len(out_works))
        fids = []
        for f in w.get("funders") or []:
            fid = short(f.get("id"))
            if fid not in funder_idx:
                funder_idx[fid] = len(funders)
                funders.append(dict(id=fid, name=f.get("display_name"), n=0))
            fids.append(funder_idx[fid])
            funders[funder_idx[fid]]["n"] += 1
        aw = [award_idx[short(x.get("id"))] for x in w.get("awards") or [] if short(x.get("id")) in award_idx]
        cnp = w.get("citation_normalized_percentile") or {}
        ab = w["_abstract"]
        # Aotearoa on the places map: Pasifika communities here (only generic Pacific terms + an NZ
        # mention) and Aotearoa environment / hazards (lens A), counted separately.
        places = sorted(c["places"])
        generic_only = c["tier"] in ("focus", "population") and places and all(p in ("PPPL", "PREG", "OCEA") for p in places)
        if generic_only and c["nz"]:
            places.append("NZP")
        if "A" in c["lenses"]:
            places.append("NZA")
        out_works.append(dict(
            id=short(w["id"]), t=w.get("display_name") or "(untitled)", y=w.get("publication_year"),
            ty=w.get("type"), c=w.get("cited_by_count") or 0, fwci=w.get("fwci"),
            top10=bool(cnp.get("is_in_top_10_percent")), v=((w.get("primary_location") or {}).get("source") or {}).get("display_name"),
            doi=w.get("doi"), oa=(w.get("open_access") or {}).get("oa_url"),
            ab=(ab[:320].rsplit(" ", 1)[0] + "…") if len(ab) > 320 else ab,
            tier=TIER_CODE[c["tier"]], lens=sum(LENS_BIT[l] for l in c["lenses"]), ev=c["evidence"],
            places=places, tp=topic_i(w.get("primary_topic")),
            sdg=[short(s["id"]) for s in w.get("sustainable_development_goals") or []],
            a=uoa_auth, na=len(aus), ext=sorted(ext), pi=w["_partner"], fu=fids, aw=aw))

    # ------------------------------------------------------------ awards: keep Pacific-related + linked
    linked = Counter(i for w in out_works for i in w["aw"])
    for i, a in enumerate(awards):
        # Pacific-related: the award text is Pacific-focused, or Aotearoa environment & hazards. Awards that only
        # name Pacific peoples within a wider project (tier p) are kept separately: a review of 18 found many were
        # general projects naming Māori and Pacific peoples as groups at risk.
        a["pacp"] = a["tier"] == "p" and not (a["lens"] & 4)
        a["pac"] = bool(a["tier"] == "f" or a["lens"] & 4)
        a["linked"] = linked.get(i, 0)
    award_stats = defaultdict(lambda: [0, 0])
    for a in awards:
        key = (a["f"] if a["f"] in ("Health Research Council of New Zealand", "Marsden Fund",
                                    "Ministry of Business, Innovation and Employment") else "Other funders", a["y0"])
        award_stats[key][0] += 1
        award_stats[key][1] += a["pac"]
    keep_aw = [i for i, a in enumerate(awards) if a["pac"] or a["pacp"] or a["linked"]]
    remap = {old: new for new, old in enumerate(keep_aw)}
    for w in out_works:
        w["aw"] = [remap[i] for i in w["aw"] if i in remap]
    awards_all_n = len(awards)
    awards = [awards[i] for i in keep_aw]

    # ------------------------------------------------------------ authors: faculty, unit, metrics
    for a in authors:
        a["faculty"] = a["fac"].most_common(1)[0][0] if a["fac"] else None
        a["unit_name"] = a["unit"].most_common(1)[0][0] if a["unit"] else None
        ws = [out_works[i] for i in a["works"]]
        a["n"] = len(ws)
        a["nf"] = sum(1 for x in ws if x["tier"] == "f")
        a["cites"] = sum(x["c"] for x in ws)
        fw = [x["fwci"] for x in ws if x["fwci"] is not None]
        a["fwci"] = round(float(np.mean(fw)), 2) if fw else None
        ys = [x["y"] for x in ws]
        a["y0"], a["y1"] = min(ys), max(ys)
        tc = Counter(x["tp"] for x in ws if x["tp"] >= 0)
        a["topics"] = [t for t, _ in tc.most_common(3)]
        a["lens"] = 0
        for x in ws:
            a["lens"] |= x["lens"]
    # co-authorship among UoA authors (teams of <= 50 so consortia do not swamp ties)
    G = nx.Graph()
    G.add_nodes_from(range(len(authors)))
    for i, w in enumerate(out_works):
        if w["na"] > 50:
            continue
        au = w["a"]
        for x in range(len(au)):
            for y in range(x + 1, len(au)):
                G.add_edge(au[x], au[y], weight=G.get_edge_data(au[x], au[y], {"weight": 0})["weight"] + 1)
    net_nodes = [i for i in range(len(authors)) if authors[i]["n"] >= 2 and G.degree(i) > 0]
    H = G.subgraph(net_nodes)
    comms = sorted(nx.community.louvain_communities(H, seed=7, weight="weight"), key=len, reverse=True)
    comm_of = {v: k for k, c in enumerate(comms) for v in c}
    bt = nx.betweenness_centrality(H, k=min(600, len(net_nodes)), seed=11, weight=None) if net_nodes else {}
    sig = hashlib.sha1(json.dumps(["strong_gravity", [authors[i]["id"] for i in net_nodes], sorted(H.edges())]).encode()).hexdigest()
    cache = WORK / "fa2_people.json"
    cached = json.loads(cache.read_text()) if cache.exists() else {}
    if cached.get("sig") == sig:
        pos = {int(k): v for k, v in cached["pos"].items()}
    else:
        pos = {int(k): [float(v[0]), float(v[1])] for k, v in nx.forceatlas2_layout(H, seed=3, max_iter=400, weight="weight", strong_gravity=True).items()}
        cache.write_text(json.dumps({"sig": sig, "pos": pos}))
    if pos:
        P = np.array([pos[v] for v in net_nodes])
        P -= np.median(P, axis=0)
        r = np.linalg.norm(P, axis=1)
        P /= (float(np.percentile(r, 97)) or 1.0)
        r = np.linalg.norm(P, axis=1)
        P[r > 1.1] *= (1.1 / r[r > 1.1])[:, None]
        for v, p in zip(net_nodes, P):
            pos[v] = [round(float(p[0]), 4), round(float(p[1]), 4)]
    communities = []
    for k, c in enumerate(comms[:10]):
        fac = Counter(authors[v]["faculty"] for v in c if authors[v]["faculty"]).most_common(2)
        tc = Counter(t for v in c for t in authors[v]["topics"]).most_common(3)
        lead = max(c, key=lambda v: (authors[v]["n"], authors[v]["cites"]))
        communities.append(dict(k=k, size=len(c), lead=lead, faculties=[f for f, _ in fac],
                                topics=[topics[t]["name"] for t, _ in tc]))
    out_authors = []
    for i, a in enumerate(authors):
        out_authors.append(dict(
            i=i, id=a["id"], name=a["name"], orcid=a["orcid"], faculty=a["faculty"], unit=a["unit_name"],
            n=a["n"], nf=a["nf"], cites=a["cites"], fwci=a["fwci"], y0=a["y0"], y1=a["y1"],
            topics=a["topics"], lens=a["lens"], deg=G.degree(i), com=comm_of.get(i, -1),
            bt=round(bt.get(i, 0.0), 5), x=pos.get(i, [None, None])[0], yv=pos.get(i, [None, None])[1]))

    # ------------------------------------------------------------ institutions: counts
    inst_n = Counter(); inst_nf = Counter()
    for w in out_works:
        for e in w["ext"]:
            inst_n[e] += 1
            inst_nf[e] += w["tier"] == "f"
    for k, it in enumerate(insts):
        it["i"], it["n"], it["nf"] = k, inst_n.get(k, 0), inst_nf.get(k, 0)

    # ------------------------------------------------------------ topic strength tables (complete years)
    def strength(group_key, label_of):
        rows = defaultdict(lambda: dict(n=0, early=0, late=0, fw=[], top10=0, focus=0))
        for w in out_works:
            if not (COMPLETE[0] <= w["y"] <= COMPLETE[1]) or w["tp"] < 0:
                continue
            k = group_key(topics[w["tp"]])
            r = rows[k]
            r["n"] += 1
            r["early"] += w["y"] <= 2022
            r["late"] += w["y"] >= 2023
            r["top10"] += w["top10"]
            r["focus"] += w["tier"] == "f"
            if w["fwci"] is not None:
                r["fw"].append(w["fwci"])
        out = []
        for k, r in rows.items():
            out.append(dict(key=k, label=label_of(k), n=r["n"], focus=r["focus"],
                            growth=round((r["late"] - r["early"]) / r["early"] * 100, 1) if r["early"] else None,
                            early=r["early"], late=r["late"],
                            fwci=round(float(np.mean(r["fw"])), 2) if r["fw"] else None, fwci_n=len(r["fw"]),
                            top10=round(100 * r["top10"] / r["n"], 1)))
        return sorted(out, key=lambda x: -x["n"])
    sub_strength = strength(lambda t: t["sub"], lambda k: k)
    topic_strength = strength(lambda t: t["name"], lambda k: k)

    # ------------------------------------------------------------ places studied
    place_rows = []
    extra = {"NZP": ("Pasifika communities in Aotearoa", None, -36.85, 174.76),
             "NZA": ("Aotearoa environment & hazards", None, -41.0, 174.0)}
    for code, (label, _, lat, lng) in list(PLACES.items()) + list(extra.items()):
        ws = [w for w in out_works if code in w["places"]]
        if ws:
            place_rows.append(dict(code=code, label=label, lat=lat, lng=lng, n=len(ws),
                                   nf=sum(w["tier"] == "f" for w in ws)))

    coverage = dict(
        candidates=len({short(w['id']) for w in raw}), kept=len(out_works), dropped=dropped, dropped_no_abstract=no_abs_dropped,
        tiers=dict(Counter(w["tier"] or "-" for w in out_works)),
        lens=dict(P=sum(1 for w in out_works if w["lens"] & 1), O=sum(1 for w in out_works if w["lens"] & 2),
                  A=sum(1 for w in out_works if w["lens"] & 4)),
        no_abstract=sum(1 for w in works if not w["_abstract"]),
        authors=len(out_authors), authors_with_faculty=sum(1 for a in out_authors if a["faculty"]),
        fwci_known=sum(1 for w in out_works if w["fwci"] is not None),
        awards=awards_all_n, awards_pacific=sum(1 for a in awards if a["pac"]),
        awards_kept=len(awards), awards_pacific_peoples=sum(1 for a in awards if a["pacp"]),
        awards_linked_only=sum(1 for a in awards if not a["pac"] and not a["pacp"]),
        award_stats=sorted([k[0], k[1], v[0], v[1]] for k, v in award_stats.items() if k[1] is not None),
    )
    doc = dict(
        meta=dict(built=TODAY, uoa=UOA, years=[2020, 2026], complete=list(COMPLETE),
                  source="OpenAlex API (works, institutions, awards)"),
        works=out_works, authors=out_authors, insts=insts, uoa_inst=uoa_i, topics=topics,
        communities=communities, coauth=[[a, b, d["weight"]] for a, b, d in H.edges(data=True)],
        awards=awards, funders=sorted(funders, key=lambda f: -f["n"]),
        places=place_rows, sub_strength=sub_strength, topic_strength=topic_strength,
        faculties=FACULTIES, coverage=coverage,
    )
    OUT.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")))
    print(f"wrote {OUT} ({OUT.stat().st_size / 1e6:.1f} MB)")
    print("coverage:", json.dumps(coverage, ensure_ascii=False))
    print("communities:", [(c["size"], c["faculties"], c["topics"][:2]) for c in communities[:8]])
    # faculty-rule check: units whose explicit faculty disagrees with the unit rule
    (WORK / "unit_faculty_pairs.json").write_text(json.dumps([[u, f, n] for (u, f), n in unit_fac_pairs.most_common()], ensure_ascii=False))


if __name__ == "__main__":
    main()
