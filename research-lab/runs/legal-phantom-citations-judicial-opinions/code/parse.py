"""Extract and screen every full case citation in the in-scope opinions (plan section 4, steps 1-5).

One pass over the 55 GB opinions archive. Storing context around every citation would take ~24 GB, so screening
happens inline and context is kept only for the citations that survive it:

  1. eyecite pulls each full case citation: volume, reporter, page, pin cite, year, plaintiff, defendant.
  2. The citation is resolved by reporter-volume-page against the citations index (build_index.py).
  3. If it resolves, the cited name is scored against the resolved case's own name. A match ends the screen.
  4. If it does not resolve, or resolves to a case with a different name, the cited name is searched across all
     ten million case names (build_names.py). D1: this step is the primary detector, since fabrications usually
     mimic a real citation format and land inside a real case.
  5. A citation that neither resolves to a matching case nor matches any case name anywhere is a phantom
     candidate, and only those keep ±400 characters of context for the reliance/flag split and manual review.

Per reporter-volume counts of citations and resolutions are accumulated for the preregistered completeness filter,
which is applied in analysis.py, not here.

Writes data/screen/candidates.jsonl, data/screen/opinions.tsv (one row per screened opinion) and
data/screen/volumes.json.
"""
import csv
import html
import json
import multiprocessing as mp
import pickle
import re
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from namenorm import norm_name, party_score, tokens_of  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
RAW, IDX, OUT = RUN / "data" / "raw", RUN / "data" / "index", RUN / "data" / "screen"
csv.field_size_limit(sys.maxsize)

DATE_FROM, DATE_TO = 20190101, 20260930
NAME_MATCH = 80          # party_score at or above which two case names are the same case
MISATTRIB_MAX = 50       # a resolved case this dissimilar to the cited name is not a near-miss typo
CONTEXT = 400
MAX_CANDIDATES = 60_000  # cap on names scored for one global search; logged when hit
TEXT_FIELDS = ("plain_text", "html_with_citations", "html", "html_lawbox", "html_columbia", "html_anon_2020",
               "xml_harvard")
TAG = re.compile(r"<[^>]+>")

# set in each worker by init()
G = {}


def norm_reporter(r):
    return "".join(ch for ch in r.lower() if ch.isalnum())


def init():
    """Load the indices once per worker. Forked workers share these pages copy-on-write."""
    from rapidfuzz import fuzz
    from eyecite import get_citations
    from eyecite.models import FullCaseCitation
    z = np.load(IDX / "pages.npz", allow_pickle=False)
    G.update(offs=z["offs"], pages=z["pages"], clusters=z["clusters"],
             keymap={(r, int(v)): i for i, (r, v) in enumerate(zip(z["reporters"], z["volumes"]))},
             names=np.load(IDX / "names.npy", allow_pickle=True),
             tokens=pickle.load(open(IDX / "tokens.pkl", "rb")),
             dropped=set(json.load(open(IDX / "dropped_tokens.json"))["dropped"]),
             fuzz=fuzz, get_citations=get_citations, FullCaseCitation=FullCaseCitation)
    m = np.load(IDX / "cluster_meta.npz")
    G["ids"] = m["ids"]
    G["row_of"] = {int(c): i for i, c in enumerate(m["ids"])}


def text_of(row):
    for f in TEXT_FIELDS:
        t = row.get(f) or ""
        if len(t) > 200:
            if f != "plain_text":
                t = html.unescape(TAG.sub(" ", t))
            return t
    return ""


def resolve(rep, vol, page):
    i = G["keymap"].get((norm_reporter(rep), vol))
    if i is None:
        return None, "reporter-volume absent"
    a, b = G["offs"][i], G["offs"][i + 1]
    pg = G["pages"][a:b]
    j = int(np.searchsorted(pg, page, side="right")) - 1
    if j < 0:
        return None, "below the volume"
    nxt = int(pg[j + 1]) if j + 1 < len(pg) else None
    if int(pg[j]) == page or nxt is None or page < nxt:
        return int(G["clusters"][a + j]), "resolved"
    return None, "gap"


def name_search(cited):
    """Best-scoring case name anywhere in the corpus for a cited name.

    Returns (score, row, capped, absent). A token can be missing from the index for two opposite reasons: it is
    in so many names that it was dropped as useless (inc, people, state, states, united), or it is in none at
    all. The first is skipped; the second is returned as `absent`, because a party name containing a word that
    appears in no case caption anywhere is strong evidence the case does not exist.
    """
    want = tokens_of(norm_name(cited)) - G["dropped"]
    pools = {t: G["tokens"].get(t) for t in want}
    absent = sorted(t for t, p in pools.items() if p is None or not len(p))
    present = {t: p for t, p in pools.items() if p is not None and len(p)}
    if not present:
        return 0.0, None, False, absent
    rarest = sorted(present, key=lambda t: len(present[t]))[:2]
    cand = present[rarest[0]]
    for t in rarest[1:]:
        cand = np.intersect1d(cand, present[t], assume_unique=False)
    capped = len(cand) > MAX_CANDIDATES
    if not len(cand):
        return 0.0, None, False, absent
    target = norm_name(cited)
    names, fz = G["names"], G["fuzz"]
    best, bi = max((party_score(fz, target, str(names[i])), int(i)) for i in cand[:MAX_CANDIDATES])
    return float(best), bi, capped, absent


def screen(task):
    """Screen one opinion. Returns (summary row, candidates, per-volume counters, capped searches)."""
    oid, cid, date, court, text = task
    fz, names = G["fuzz"], G["names"]
    vols = Counter()
    cands, misattrib, n_full, n_resolved, n_consistent, capped = [], [], 0, 0, 0, 0
    try:
        cites = G["get_citations"](text)
    except Exception:                                   # noqa: BLE001  eyecite chokes on rare malformed text
        return (oid, cid, date, court, -1, 0, 0), [], [], vols, 0
    for c in cites:
        if not isinstance(c, G["FullCaseCitation"]):
            continue
        g = c.groups
        try:
            vol, page = int(g.get("volume") or 0), int(g.get("page") or 0)
        except ValueError:
            continue
        rep = c.corrected_reporter() or g.get("reporter") or ""
        if not (vol and page and rep):
            continue
        n_full += 1
        md = c.metadata
        plaintiff, defendant = (getattr(md, "plaintiff", None) or ""), (getattr(md, "defendant", None) or "")
        cited = f"{plaintiff} v. {defendant}" if plaintiff and defendant else (plaintiff or defendant)
        key = f"{norm_reporter(rep)}|{vol}"
        vols[key + "|n"] += 1
        hit, why = resolve(rep, vol, page)
        if hit is not None:
            vols[key + "|res"] += 1
            n_resolved += 1
            row = G["row_of"].get(hit)
            if not cited or (row is not None and party_score(fz, norm_name(cited), str(names[row])) >= NAME_MATCH):
                n_consistent += 1
                continue
        if not cited:
            continue                                   # an unresolved citation with no names cannot be screened
        score, bi, cap, absent = name_search(cited)
        capped += int(cap)
        if score >= NAME_MATCH:
            # The name exists somewhere. If the citation also resolved, but to a case with an unrelated name, the
            # citation and the name do not belong together: the plan's misattribution class (plan §4 step 4).
            # Fabrications that reuse a common name land here -- Miller v. United Airlines, 174 F.3d 366, from the
            # Mata filings, names a real case but points into a different one. Not a phantom under plan §1, so it
            # is recorded separately rather than counted. Near-miss typos that land in an adjacent case with a
            # similar name are excluded by MISATTRIB_MAX.
            row = G["row_of"].get(hit) if hit is not None else None
            if row is not None and G["ids"][bi] != hit:
                rs = party_score(fz, norm_name(cited), str(names[row]))
                if rs < MISATTRIB_MAX:
                    s0, e0 = c.span()
                    misattrib.append({
                        "opinion_id": oid, "cluster_id": cid, "date": date, "court": court,
                        "cite": f"{vol} {rep} {page}", "cited_name": cited, "resolved_to": hit,
                        "resolved_name": str(names[row])[:90], "resolved_score": round(float(rs), 1),
                        "name_found_as": str(names[bi])[:90], "name_found_cluster": int(G["ids"][bi]),
                        "context": text[max(0, s0 - 200):e0 + 200]})
            continue
        s, e = c.span()
        cands.append({
            "opinion_id": oid, "cluster_id": cid, "date": date, "court": court,
            "cite": f"{vol} {rep} {page}", "cited_name": cited, "year": getattr(md, "year", None),
            "pin": getattr(md, "pin_cite", None), "route": "resolved-elsewhere" if hit else why,
            "resolved_to": hit, "resolved_name": str(names[G["row_of"][hit]]) if hit in G["row_of"] else None,
            "best_name_score": round(score, 1), "best_name": str(names[bi])[:90] if bi is not None else None,
            "absent_tokens": absent,
            "context": text[max(0, s - CONTEXT):e + CONTEXT],
        })
    return (oid, cid, date, court, n_full, n_resolved, n_consistent), cands, misattrib, vols, capped


def scope():
    """In-scope clusters: date_filed in the study window, with their court from the dockets table."""
    m = np.load(IDX / "cluster_meta.npz")
    ids, dates, dockets = m["ids"], m["dates"], m["dockets"]
    keep = (dates >= DATE_FROM) & (dates <= DATE_TO)
    want_dockets = set(int(d) for d in dockets[keep])
    court = {}
    import bz2
    with bz2.open(RAW / "dockets.csv.bz2", "rt", encoding="utf-8", errors="ignore") as fh:
        for row in csv.DictReader(fh):
            try:
                d = int(row["id"])
            except (ValueError, TypeError):
                continue
            if d in want_dockets:
                court[d] = row.get("court_id") or ""
    return {int(c): (int(dt), court.get(int(dk), "")) for c, dt, dk in zip(ids[keep], dates[keep], dockets[keep])}


def reader(inscope, q, nworkers):
    """Stream the opinions archive and feed in-scope opinions to the workers."""
    import indexed_bzip2
    seen = kept = 0
    with indexed_bzip2.open(str(RAW / "opinions.csv.bz2"), parallelization=8) as raw:
        import io
        for row in csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8", errors="ignore")):
            seen += 1
            try:
                cid = int(row.get("cluster_id") or 0)
            except ValueError:
                continue
            if cid not in inscope:
                continue
            t = text_of(row)
            if not t:
                continue
            date, court = inscope[cid]
            q.put((int(row.get("id") or 0), cid, date, court, t))
            kept += 1
            if seen % 500_000 == 0:
                print(f"  read {seen:,} opinions, {kept:,} in scope", flush=True)
    for _ in range(nworkers):
        q.put(None)
    print(f"reader done: {seen:,} opinions read, {kept:,} in scope", flush=True)


def worker(q, r):
    init()
    while True:
        t = q.get()
        if t is None:
            r.put(None)
            return
        r.put(screen(t))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    inscope = scope()
    print(f"{len(inscope):,} in-scope clusters ({DATE_FROM}-{DATE_TO}) in {time.time() - t0:.0f}s", flush=True)
    nworkers = max(1, mp.cpu_count() - 6)
    q, r = mp.Queue(maxsize=nworkers * 64), mp.Queue(maxsize=nworkers * 64)
    ctx_procs = [mp.Process(target=worker, args=(q, r), daemon=True) for _ in range(nworkers)]
    for p in ctx_procs:
        p.start()
    rd = mp.Process(target=reader, args=(inscope, q, nworkers), daemon=True)
    rd.start()

    vols, done, ncand, nmis, capped, finished = Counter(), 0, 0, 0, 0, 0
    with open(OUT / "opinions.tsv", "w") as ot, open(OUT / "candidates.jsonl", "w") as ct, \
            open(OUT / "misattributions.jsonl", "w") as mt:
        ot.write("opinion_id\tcluster_id\tdate\tcourt\tn_full\tn_resolved\tn_consistent\n")
        while finished < nworkers:
            res = r.get()
            if res is None:
                finished += 1
                continue
            row, cands, mis, v, cap = res
            ot.write("\t".join(map(str, row)) + "\n")
            for c in cands:
                ct.write(json.dumps(c) + "\n")
            for m_ in mis:
                mt.write(json.dumps(m_) + "\n")
            vols.update(v); ncand += len(cands); nmis += len(mis); capped += cap; done += 1
            if done % 100_000 == 0:
                print(f"  screened {done:,} opinions, {ncand:,} candidates, {nmis:,} misattributions, "
                      f"{(time.time() - t0) / 60:.0f} min", flush=True)
    rd.join()
    json.dump({"volumes": dict(vols), "capped_name_searches": capped, "opinions_screened": done,
               "candidates": ncand, "misattributions": nmis}, open(OUT / "volumes.json", "w"))
    print(f"done: {done:,} opinions screened, {ncand:,} phantom candidates, {capped:,} capped searches, "
          f"{(time.time() - t0) / 60:.0f} min", flush=True)


if __name__ == "__main__":
    mp.set_start_method("fork")
    main()
