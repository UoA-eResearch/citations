"""Step 3: network analysis of the corpus -> data/corpus.json for the explorer.

Citation network analysis (works):
  - in-corpus citation edges from OpenAlex reference lists
  - PageRank and in-corpus citations (influence within this field, not global fame)
  - Louvain communities (schools of thought), labelled by concept and anchor work
  - main path (search path count, Hummon & Doreian 1989): the backbone of the genealogy
  - two layouts: force-directed, and a genealogy timeline (x = year, lanes = community)
Situational network analysis (people, places, events):
  - authors: works, in-field citations, author PageRank, bridging (betweenness over
    co-authorship + citation ties), co-author degree, career span, institutions by year
  - institutions with coordinates; co-location of scholars by 5-year window
  - collaboration arcs (co-authorship between institutions) and citation-flow arcs (where
    ideas travel: citing institution -> cited institution), both by year
  - curated events (events.json)
Coverage: seeds not in OpenAlex, works without reference lists or affiliations.
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
from queries import CONCEPTS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
WORK = Path(os.environ.get("PACIFIC_WORK", "/mnt/data/ubuntu/pacific-work"))
OUT = ROOT / "data" / "corpus.json"

PACIFIC_ISLANDS = set("FJ WS TO PG SB VU KI TV NR PW FM MH CK NU TK WF PF NC AS GU MP".split())
REASON_BITS = {"seed": 1, "cites": 2, "cites+pac": 4, "term": 8}


def short(oid):
    return str(oid or "").rsplit("/", 1)[-1]


def abstract(inv, limit=320):
    if not inv:
        return ""
    pos = {}
    for word, idxs in inv.items():
        for i in idxs:
            pos[i] = word
    text = " ".join(pos[i] for i in sorted(pos))
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + "…"


def region(inst):
    cc, lat, lng = inst.get("country"), inst.get("lat"), inst.get("lng")
    hawaii = lat is not None and 18 < lat < 23 and -161 < lng < -154
    if cc in PACIFIC_ISLANDS:
        return "Pacific Islands"
    if cc == "NZ":
        return "Aotearoa NZ"
    if cc == "AU":
        return "Australia"
    if cc in ("US", None) and hawaii:
        return "Hawaiʻi"
    # A few records (e.g. Solomon Islands National University) lack a country code.
    if cc is None and lat is not None and -25 < lat < 15 and (lng > 150 or lng < -140):
        return "Pacific Islands"
    return "Elsewhere"


STOP = set("""a an and the of in on for to with from by at as is are be or its their our we us
this that these those into through between within about among toward towards using use case
study studies new zealand aotearoa pacific pasifika research perspectives perspective approach
experiences experience people peoples islands island indigenous""".split())


def title_terms(title):
    t = re.sub(r"[^a-zāēīōū' -]", " ", title.lower())
    return {w.strip("'-") for w in t.split() if len(w.strip("'-")) >= 4 and w.strip("'-") not in STOP}


def main():
    seeds_doc = json.loads((ROOT / "data/seeds_resolved.json").read_text())
    seeds = seeds_doc["seeds"]
    raw = [json.loads(l) for l in open(WORK / "works.jsonl")]
    insts_geo = json.loads((WORK / "institutions.json").read_text())
    events = json.loads((Path(__file__).parent / "events.json").read_text())

    # Seed record -> seed key; a seed text's display year is the seed's year, not the record's
    # (OpenAlex dates Decolonizing Methodologies as a 2024 chapter, for example).
    seed_of = {r["id"]: s for s in seeds for r in s["records"]}

    # ---------- works ----------
    works = []
    idx = {}
    for w in raw:
        wid = short(w["id"])
        if wid in idx:
            continue
        s = seed_of.get(wid)
        year = s["year"] if s else w.get("publication_year")
        if not year:
            continue
        text = ((w.get("display_name") or "") + " " + abstract(w.get("abstract_inverted_index"), 4000)).lower()
        text = text.replace("ā", "a").replace("ʻ", "'").replace("‘", "'").replace("’", "'")
        concepts = [k for k, pats in CONCEPTS.items() if any(p in text for p in pats)]
        idx[wid] = len(works)
        works.append(dict(
            # Seed texts show their curated title: OpenAlex has e.g. "8 Decolonizing Methodologies".
            id=wid, title=(s["title"] if s else w.get("display_name")) or "(untitled)", year=int(year), type=w.get("type"),
            cites=w.get("cited_by_count") or 0, fwci=w.get("fwci"), doi=w.get("doi"),
            venue=((w.get("primary_location") or {}).get("source") or {}).get("display_name"),
            oa_url=(w.get("open_access") or {}).get("oa_url"), xpac=bool(w.get("is_xpac")),
            refs=[short(r) for r in w.get("referenced_works") or []],
            authorships=w.get("authorships") or [], abstract=abstract(w.get("abstract_inverted_index")),
            reasons=w.get("_reasons", []), seed=s["key"] if s else None, strand=s["strand"] if s else None,
            concepts=concepts, topic=((w.get("primary_topic") or {}).get("display_name")),
            field=(((w.get("primary_topic") or {}).get("field") or {}).get("display_name")),
        ))
    n = len(works)
    print(f"{n} works")

    # Collapse duplicate records of one seed text onto its most cited record, so editions do
    # not appear as separate nodes and citations to any edition count once.
    canon = {}
    for s in seeds:
        ids = [r["id"] for r in s["records"] if r["id"] in idx]
        if ids:
            primary = max(ids, key=lambda i: works[idx[i]]["cites"])
            for i in ids:
                canon[i] = primary
            works[idx[primary]]["cites"] = sum(works[idx[i]]["cites"] for i in ids)
    keep = [w for w in works if canon.get(w["id"], w["id"]) == w["id"]]
    works = keep
    idx = {w["id"]: i for i, w in enumerate(works)}
    n = len(works)

    # ---------- citation graph ----------
    G = nx.DiGraph()
    G.add_nodes_from(range(n))
    for i, w in enumerate(works):
        for r in w["refs"]:
            j = idx.get(canon.get(r, r))
            if j is not None and j != i:
                G.add_edge(i, j)  # citing -> cited
    print(f"{G.number_of_edges()} in-corpus citation edges")
    local_in = dict(G.in_degree())
    pr = nx.pagerank(G, alpha=0.85)

    # Main path analysis on the knowledge-flow DAG (cited -> citing), cycles broken by year.
    F = nx.DiGraph()
    F.add_nodes_from(range(n))
    for i, j in G.edges():
        if works[j]["year"] <= works[i]["year"]:
            F.add_edge(j, i)
    while True:
        try:
            cyc = nx.find_cycle(F)
        except nx.NetworkXNoCycle:
            break
        F.remove_edge(*cyc[-1])
    topo = list(nx.topological_sort(F))
    n_minus = {v: 1 if F.in_degree(v) == 0 else 0 for v in F}
    for v in topo:
        for u in F.predecessors(v):
            n_minus[v] += n_minus[u]
    n_plus = {v: 1 if F.out_degree(v) == 0 else 0 for v in F}
    for v in reversed(topo):
        for u in F.successors(v):
            n_plus[v] += n_plus[u]
    spc = {(u, v): n_minus[u] * n_plus[v] for u, v in F.edges()}
    # Global main path: the source-to-sink path with the largest total log-SPC.
    best, nxt = {}, {}
    for v in reversed(topo):
        cand = [(math.log(spc[(v, u)]) + best[u], u) for u in F.successors(v)]
        if cand:
            best[v], nxt[v] = max(cand)
        else:
            best[v] = 0.0
    sources = [v for v in F if F.in_degree(v) == 0 and F.out_degree(v) > 0]
    main_path = []
    if sources:
        v = max(sources, key=lambda s: best[s])
        main_path = [v]
        while v in nxt:
            v = nxt[v]
            main_path.append(v)
    mp_edges = set(zip(main_path, main_path[1:]))
    print(f"main path: {len(main_path)} works")

    # Communities on the undirected citation graph (connected works only).
    U = G.to_undirected()
    connected = [v for v in U if U.degree(v) > 0]
    comms = nx.community.louvain_communities(U.subgraph(connected), seed=7, resolution=1.0)
    comms = sorted(comms, key=len, reverse=True)
    comm_of = {}
    for k, c in enumerate(comms):
        for v in c:
            comm_of[v] = k
    # Label each community by the title words most distinctive of it (share in the community
    # x inverse document frequency in the corpus), alongside its most cited work.
    terms = [title_terms(w["title"]) for w in works]
    df = Counter(t for ts in terms for t in ts)
    communities = []
    for k, c in enumerate(comms[:12]):
        anchor = max(c, key=lambda v: local_in[v])
        tf = Counter(t for v in c for t in terms[v])
        scored = sorted(((cnt / len(c)) * math.log(n / df[t]), t) for t, cnt in tf.items() if cnt >= 4)
        words = [t for _, t in sorted(scored, reverse=True)[:3]]
        con = Counter(x for v in c for x in works[v]["concepts"])
        aw = works[anchor]
        first = (aw["authorships"][0].get("author") or {}).get("display_name", "") if aw["authorships"] else ""
        communities.append(dict(k=k, size=len(c), label=", ".join(words),
                                anchor=f"{first.split(' ')[-1]} {aw['year']}".strip(), anchor_i=anchor,
                                year=round(float(np.median([works[v]["year"] for v in c])), 1),
                                concepts=[x for x, _ in con.most_common(4)]))
    print("communities:", [(c["size"], c["label"], c["anchor"]) for c in communities[:8]])

    # Layouts: force-directed for connected works; unconnected works sit on an outer ring.
    # ForceAtlas2 separates the schools of thought far better than a spring layout (~4 min);
    # cached by work ids + edges so re-runs that change nothing else skip it.
    sig = hashlib.sha1(json.dumps([[w["id"] for w in works], sorted(U.subgraph(connected).edges())]).encode()).hexdigest()
    cache = WORK / "fa2_layout.json"
    cached = json.loads(cache.read_text()) if cache.exists() else {}
    if cached.get("sig") == sig:
        pos = {int(k): v for k, v in cached["pos"].items()}
    else:
        pos = nx.forceatlas2_layout(U.subgraph(connected), seed=3, max_iter=300)
        pos = {int(k): [float(v[0]), float(v[1])] for k, v in pos.items()}
        cache.write_text(json.dumps({"sig": sig, "pos": pos}))
    xy = np.zeros((n, 2))
    for v, p in pos.items():
        xy[v] = p
    if connected:
        # Scale by the 97th-percentile radius so a few far-flung works cannot squash the core,
        # then pull those few in to just outside it.
        xy[connected] -= np.median(xy[connected], axis=0)
        r = np.linalg.norm(xy[connected], axis=1)
        xy[connected] /= (float(np.percentile(r, 97)) or 1.0)
        r = np.linalg.norm(xy[connected], axis=1)
        over = r > 1.08
        xy[np.array(connected)[over]] *= (1.08 / r[over])[:, None]
    isolated = [v for v in range(n) if v not in comm_of]
    rng = np.random.default_rng(5)
    for v in isolated:
        a = rng.uniform(0, 2 * math.pi)
        r = 1.24 + rng.uniform(0, 0.1)
        xy[v] = (r * math.cos(a), r * math.sin(a))
    # Genealogy lanes: communities ordered by median year; lane y within [-1, 1].
    lane_order = sorted(range(min(len(comms), len(communities))), key=lambda k: communities[k]["year"])
    lane_of = {k: i for i, k in enumerate(lane_order)}
    n_lanes = len(lane_order) + 1  # +1: other / unconnected
    lane_y = np.zeros(n)
    for v in range(n):
        k = comm_of.get(v)
        lane = lane_of.get(k, n_lanes - 1)
        jitter = (float(np.clip(xy[v][1], -1, 1)) if v in pos else rng.uniform(-1, 1)) * 0.35
        lane_y[v] = -1 + 2 * (lane + 0.5 + jitter) / n_lanes
    for c in communities:
        c["lane"] = lane_of.get(c["k"])

    # ---------- authors & institutions ----------
    inst_list, inst_idx = [], {}

    def inst_i(iid):
        if iid not in inst_idx:
            g = insts_geo.get(iid) or {}
            inst_idx[iid] = len(inst_list)
            inst_list.append(dict(id=iid, name=g.get("name") or iid, country=g.get("country"),
                                  city=g.get("city"), type=g.get("type"),
                                  lat=g.get("lat"), lng=g.get("lng"), region=region(g),
                                  works=0, years=Counter(), authors=set()))
        return inst_idx[iid]

    auth_list, auth_idx = [], {}
    work_auth, work_inst = [[] for _ in range(n)], [[] for _ in range(n)]
    for i, w in enumerate(works):
        seen_i = set()
        for a in w["authorships"]:
            au = a.get("author") or {}
            aid = short(au.get("id"))
            if not aid:
                continue
            if aid not in auth_idx:
                auth_idx[aid] = len(auth_list)
                auth_list.append(dict(id=aid, name=au.get("display_name") or a.get("raw_author_name") or aid,
                                      orcid=au.get("orcid"), works=[], insts=defaultdict(list)))
            ai = auth_idx[aid]
            if ai not in work_auth[i]:
                work_auth[i].append(ai)
                auth_list[ai]["works"].append(i)
            for inst in a.get("institutions") or []:
                iid = short(inst.get("id"))
                if not iid:
                    continue
                ii = inst_i(iid)
                auth_list[ai]["insts"][ii].append(w["year"])
                inst_list[ii]["authors"].add(ai)
                if ii not in seen_i:
                    seen_i.add(ii)
                    work_inst[i].append(ii)
                    inst_list[ii]["works"] += 1
                    inst_list[ii]["years"][w["year"]] += 1

    # Author citation graph (fractional credit) and co-authorship graph.
    AC = nx.DiGraph()
    CO = nx.Graph()
    AC.add_nodes_from(range(len(auth_list)))
    CO.add_nodes_from(range(len(auth_list)))
    for i, j in G.edges():
        if not work_auth[i] or not work_auth[j]:
            continue
        wgt = 1.0 / (len(work_auth[i]) * len(work_auth[j]))
        for a in work_auth[i]:
            for b in work_auth[j]:
                if a != b:
                    AC.add_edge(a, b, weight=AC.get_edge_data(a, b, {"weight": 0})["weight"] + wgt)
    for i in range(n):
        au = work_auth[i]
        if len(au) > 25:  # consortium papers would swamp co-authorship ties
            continue
        for x in range(len(au)):
            for y in range(x + 1, len(au)):
                CO.add_edge(au[x], au[y], weight=CO.get_edge_data(au[x], au[y], {"weight": 0})["weight"] + 1)
    apr = nx.pagerank(AC, alpha=0.85, weight="weight")
    BR = nx.Graph()
    BR.add_nodes_from(CO.nodes())
    BR.add_edges_from(CO.edges())
    BR.add_edges_from(AC.to_undirected().edges())
    active = [v for v in BR if BR.degree(v) > 0]
    bt = nx.betweenness_centrality(BR.subgraph(active), k=min(800, len(active)), seed=11, normalized=True)

    authors_out = []
    for ai, a in enumerate(auth_list):
        ws = a["works"]
        years = [works[i]["year"] for i in ws]
        lc = sum(local_in[i] for i in ws)
        insts = sorted(((ii, min(y), max(y)) for ii, y in a["insts"].items()), key=lambda t: (t[2], t[1]))
        latest = insts[-1][0] if insts else None
        top_work = max(ws, key=lambda i: (local_in[i], works[i]["cites"]))
        authors_out.append(dict(
            i=ai, id=a["id"], name=a["name"], orcid=a["orcid"], n=len(ws), lc=lc,
            gc=sum(works[i]["cites"] for i in ws), pr=apr.get(ai, 0.0), bt=bt.get(ai, 0.0),
            deg=CO.degree(ai), y0=min(years), y1=max(years), inst=latest,
            insts=[[ii, y0, y1] for ii, y0, y1 in insts],
            region=inst_list[latest]["region"] if latest is not None else None,
            top=top_work, works=sorted(ws, key=lambda i: -local_in[i])[:40],
            seeds=sorted({works[i]["seed"] for i in ws if works[i]["seed"]})))
    # Percentiles saturate at the top (most authors score zero), so the explorer shows ranks,
    # with bars on a square-root scale relative to the leader.
    for key in ("lc", "pr", "bt", "deg"):
        vals = np.array([a[key] for a in authors_out], dtype=float)
        order = vals.argsort().argsort()
        rank = (-vals).argsort().argsort() + 1
        vmax = float(vals.max()) or 1.0
        for a, r, rk, v in zip(authors_out, order, rank, vals):
            a[key + "_pct"] = round(100.0 * r / max(1, len(vals) - 1), 1)
            a[key + "_rank"] = int(rk) if v > 0 else None
            a[key + "_bar"] = round(100.0 * math.sqrt(v / vmax), 1)

    # Co-location: scholars sharing an institution within a 5-year window.
    key_authors = {a["i"] for a in sorted(authors_out, key=lambda a: -a["pr"])[:300]}
    coloc = defaultdict(set)
    for a in auth_list:
        ai = auth_idx[a["id"]]
        for ii, ys in a["insts"].items():
            for y in set(ys):
                coloc[(ii, y // 5 * 5)].add(ai)
    colocations = []
    for (ii, w0), members in coloc.items():
        key_m = sorted(members & key_authors, key=lambda a: -apr.get(a, 0))
        if len(key_m) >= 2:
            colocations.append(dict(inst=ii, y0=w0, y1=w0 + 4, n=len(members), key=key_m[:30]))
    colocations.sort(key=lambda c: (-len(c["key"]), c["y0"]))

    # Collaboration arcs (co-authorship across institutions) and citation-flow arcs.
    collab = Counter()
    for i in range(n):
        ii = sorted(set(work_inst[i]))
        for x in range(len(ii)):
            for y in range(x + 1, len(ii)):
                collab[(ii[x], ii[y], works[i]["year"])] += 1
    flow = Counter()
    for i, j in G.edges():
        for a in set(work_inst[i]):
            for b in set(work_inst[j]):
                if a != b:
                    flow[(a, b, works[i]["year"])] += 1.0 / (len(set(work_inst[i])) * len(set(work_inst[j])))

    # ---------- coverage ----------
    no_refs = sum(1 for w in works if not w["refs"])
    no_inst = sum(1 for i in range(n) if not work_inst[i])
    unconnected = len(isolated)
    types = Counter(w["type"] for w in works)
    coverage = dict(
        seeds_total=len(seeds), seeds_found=sum(s["status"] != "missing" for s in seeds),
        seeds_missing=[dict(key=s["key"], title=s["title"], year=s["year"], venue=s["venue"],
                            form=s["form"], strand=s["strand"], evidence=s.get("evidence"),
                            authors=s["surnames"]) for s in seeds if s["status"] == "missing"],
        works=n, no_refs=no_refs, no_inst=no_inst, unconnected=unconnected,
        xpac=sum(w["xpac"] for w in works), types=dict(types.most_common()),
        edges=G.number_of_edges(),
        reasons={k: sum(k in w["reasons"] for w in works) for k in REASON_BITS},
    )

    # ---------- emit ----------
    concepts = list(CONCEPTS)
    con_i = {c: k for k, c in enumerate(concepts)}
    pr_vals = np.array([pr[i] for i in range(n)])
    pr_pct = pr_vals.argsort().argsort() / max(1, n - 1) * 100
    pr_rank = (-pr_vals).argsort().argsort() + 1
    out_works = []
    for i, w in enumerate(works):
        out_works.append(dict(
            i=i, id=w["id"], t=w["title"], y=w["year"], ty=w["type"], c=w["cites"], lc=local_in[i],
            pr=round(float(pr_pct[i]), 1), prk=int(pr_rank[i]), a=work_auth[i][:12], na=len(work_auth[i]), n=work_inst[i][:12],
            v=w["venue"], why=sum(REASON_BITS[r] for r in w["reasons"] if r in REASON_BITS),
            s=w["seed"], st=w["strand"], k=[con_i[c] for c in w["concepts"]],
            com=comm_of.get(i, -1), mp=1 if i in set(main_path) else 0, x=bool(w["xpac"]),
            doi=w["doi"], oa=w["oa_url"], ab=w["abstract"], f=w["field"],
            fx=round(float(xy[i][0]), 4), fy=round(float(xy[i][1]), 4), ly=round(float(lane_y[i]), 4),
            nr=len(w["refs"])))
    links = [[i, j, 1 if (j, i) in mp_edges else 0] for i, j in G.edges()]
    out_insts = []
    for ii, it in enumerate(inst_list):
        out_insts.append(dict(i=ii, id=it["id"], name=it["name"], cc=it["country"], city=it["city"],
                              type=it["type"], lat=it["lat"], lng=it["lng"], region=it["region"],
                              w=it["works"], au=len(it["authors"]),
                              yr=sorted([y, c] for y, c in it["years"].items())))
    doc = dict(
        meta=dict(built=date.today().isoformat(), source="OpenAlex API (core + expansion corpus)",
                  method=__doc__.strip()),
        strands=seeds_doc["strands"], concepts=concepts, communities=communities,
        works=out_works, links=links, main_path=main_path,
        # The explorer rebuilds each author's work list from works[].a; raw scores give way to percentiles.
        authors=[{k: v for k, v in a.items() if k not in ("works", "pr", "bt")} for a in authors_out],
        insts=out_insts,
        collab=[[a, b, y, c] for (a, b, y), c in collab.items()],
        flow=[[a, b, y, round(c, 3)] for (a, b, y), c in flow.items()],
        colocations=colocations[:400], events=events,
        seeds=[dict(key=s["key"], title=s["title"], year=s["year"], venue=s["venue"], form=s["form"],
                    strand=s["strand"], status=s["status"], evidence=s.get("evidence"),
                    surnames=s["surnames"], broad=s["broad"],
                    work=idx.get(canon.get(s["records"][0]["id"], s["records"][0]["id"])) if s["records"] else None,
                    records=len(s["records"]), cites=s["cited_by"]) for s in seeds],
        coverage=coverage,
    )
    OUT.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")))
    print(f"wrote {OUT} ({OUT.stat().st_size / 1e6:.1f} MB): {n} works, {len(links)} links, "
          f"{len(authors_out)} authors, {len(out_insts)} institutions, {len(colocations)} co-locations")
    print("coverage:", {k: v for k, v in coverage.items() if k != "seeds_missing"})


if __name__ == "__main__":
    main()
