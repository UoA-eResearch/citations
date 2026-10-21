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
import clcsv  # noqa: E402  the bulk files' PostgreSQL CSV dialect
from namenorm import clean_cited, distinctive, norm_name, party_score, tokens_of  # noqa: E402
import abbrev  # noqa: E402  Bluebook abbreviations and tolerant token match (D6)

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
    """Load the indices once, in the parent, before the workers are forked.

    Each worker loading its own copy cost 2.79 GB, so 22 workers would need 61 GB of the machine's 82 GB free.
    Forking after loading shares pages copy-on-write -- but only for flat numpy buffers: touching a Python object
    writes its reference count and copies its page, so ten million name strings or a ten-million-entry dict would
    be duplicated piecemeal into every worker over the run. Names are therefore one UTF-8 blob with an offset
    table, and cluster id -> row is a sorted array searched with searchsorted.
    """
    from rapidfuzz import fuzz
    from eyecite import get_citations
    from eyecite.models import FullCaseCitation
    z = np.load(IDX / "pages.npz", allow_pickle=False)
    G.update(offs=z["offs"], pages=z["pages"], clusters=z["clusters"],
             keymap={(r, int(v)): i for i, (r, v) in enumerate(zip(z["reporters"], z["volumes"]))},
             
             tokens=pickle.load(open(IDX / "tokens.pkl", "rb")),
             dropped=set(json.load(open(IDX / "dropped_tokens.json"))["dropped"]),
             fuzz=fuzz, get_citations=get_citations, FullCaseCitation=FullCaseCitation)
    names = np.load(IDX / "names.npy", allow_pickle=True)
    enc = [str(n).encode("utf-8") for n in names]
    G["name_off"] = np.zeros(len(enc) + 1, dtype=np.int64)
    G["name_off"][1:] = np.cumsum([len(b) for b in enc])
    G["name_blob"] = np.frombuffer(b"".join(enc), dtype=np.uint8)
    del names, enc
    m = np.load(IDX / "cluster_meta.npz")
    G["ids"] = m["ids"]
    G["id_order"] = np.argsort(G["ids"], kind="stable")
    G["ids_sorted"] = G["ids"][G["id_order"]]


def name_at(i):
    a, b = G["name_off"][i], G["name_off"][i + 1]
    return G["name_blob"][a:b].tobytes().decode("utf-8")


def row_of(cid):
    j = int(np.searchsorted(G["ids_sorted"], cid))
    if j < len(G["ids_sorted"]) and int(G["ids_sorted"][j]) == cid:
        return int(G["id_order"][j])
    return None


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
    """Best-scoring case name anywhere in the corpus for a cleaned cited name.

    Returns (score, row, capped, absent). Tokens dropped as too common are skipped; tokens in no caption anywhere
    are returned as `absent`, which is evidence. Candidates are the union of the postings of the three rarest
    distinctive tokens, not their intersection: in the pilot (D3) an intersection let a single junk token -- a
    year, an OCR fragment -- empty the pool and turn a real case into a phantom candidate.
    """
    norm = norm_name(cited)
    first = _name_search_norm(norm)
    exp = abbrev.expanded_name(norm)                   # D6: also search the name with abbreviations spelled out
    if exp != norm:
        second = _name_search_norm(exp)
        if second[0] > first[0]:
            return second[0], second[1], first[2] or second[2], first[3]
    return first


def _name_search_norm(norm):
    want = distinctive(norm, G["dropped"])
    pools = {t: G["tokens"].get(t) for t in want}
    absent = sorted(t for t, p in pools.items() if p is None or not len(p))
    present = {t: p for t, p in pools.items() if p is not None and len(p)}
    if not present:
        return 0.0, None, False, absent
    rarest = sorted(present, key=lambda t: len(present[t]))[:3]
    per = MAX_CANDIDATES // len(rarest)
    capped = any(len(present[t]) > per for t in rarest)
    cand = np.unique(np.concatenate([present[t][:per] for t in rarest]))
    fz = G["fuzz"]
    best, bi = max((party_score(fz, norm, name_at(int(i))), int(i)) for i in cand)
    return float(best), bi, capped, absent


def judge(rep, vol, page, cited):
    """The screen's decision for one citation. The validator calls this same function, so the check it reports
    is the check the screen runs (D2: two copies of this logic had drifted apart once already).

    Returns a dict: verdict is one of consistent | phantom | misattribution | name-exists | unscreenable.
    """
    hit, why = resolve(rep, vol, page) if (rep and vol and page) else (None, "not a reporter citation")
    out = {"resolved_to": hit, "route": why}
    if hit is not None:
        row = row_of(hit)
        out["resolved_name"] = name_at(row) if row is not None else None
        nc = norm_name(cited) if cited else ""
        ct = abbrev.cited_tokens(nc, distinctive(nc, G["dropped"]), G["dropped"]) if cited else set()
        if not ct or (row is not None and abbrev.shares_token(G["fuzz"], ct, name_at(row))):
            out["verdict"] = "consistent"
            return out
        out["route"] = "resolved-elsewhere"
    if not cited:
        out["verdict"] = "unscreenable"
        return out
    score, bi, cap, absent = name_search(cited)
    out.update(best_name_score=round(score, 1), absent_tokens=absent, capped=cap,
               best_name=name_at(bi)[:90] if bi is not None else None,
               best_cluster=int(G["ids"][bi]) if bi is not None else None)
    if score < NAME_MATCH:
        out["verdict"] = "phantom"
        return out
    # the name exists somewhere: a misattribution if the citation resolved into an unrelated case
    if hit is not None and out["best_cluster"] != hit:
        row = row_of(hit)
        rs = party_score(G["fuzz"], norm_name(cited), name_at(row)) if row is not None else 0.0
        out["resolved_score"] = round(float(rs), 1)
        out["verdict"] = "misattribution" if rs < MISATTRIB_MAX else "name-exists"
    else:
        out["verdict"] = "name-exists"
    return out


def screen(task):
    """Screen one opinion. Returns (summary row, candidates, per-volume counters, capped searches)."""
    oid, cid, date, court, text = task
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
        cited = clean_cited(plaintiff, defendant)
        key = f"{norm_reporter(rep)}|{vol}"
        vols[key + "|n"] += 1
        j = judge(rep, vol, page, cited)
        if j["resolved_to"] is not None:
            vols[key + "|res"] += 1
            n_resolved += 1
        if j["verdict"] in ("consistent", "name-exists"):   # D6: the cited case is in the corpus
            vols[key + "|cov"] += 1
        capped += int(j.get("capped", False))
        if j["verdict"] == "consistent":
            n_consistent += 1
            continue
        if j["verdict"] not in ("phantom", "misattribution"):
            continue
        s0, e0 = c.span()
        rec = {"opinion_id": oid, "cluster_id": cid, "date": date, "court": court,
               "cite": f"{vol} {rep} {page}", "cited_name": cited, "year": getattr(md, "year", None),
               "pin": getattr(md, "pin_cite", None), **j}
        if j["verdict"] == "phantom":
            rec["context"] = text[max(0, s0 - CONTEXT):e0 + CONTEXT]
            cands.append(rec)
        else:
            rec["context"] = text[max(0, s0 - 200):e0 + 200]
            misattrib.append(rec)
    return (oid, cid, date, court, n_full, n_resolved, n_consistent), cands, misattrib, vols, capped


def scope():
    """In-scope clusters: date_filed in the study window, with their court from the dockets table."""
    m = np.load(IDX / "cluster_meta.npz")
    ids, dates, dockets = m["ids"], m["dates"], m["dockets"]
    keep = (dates >= DATE_FROM) & (dates <= DATE_TO)
    want_dockets = set(int(d) for d in dockets[keep])
    court = {}
    import bz2
    with bz2.open(RAW / "dockets.csv.bz2", "rt", encoding="utf-8", errors="ignore", newline="") as fh:
        for row in clcsv.reader(fh):
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
        for row in clcsv.reader(io.TextIOWrapper(raw, encoding="utf-8", errors="ignore", newline="")):
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
    init()                                   # once, before forking: workers share it copy-on-write
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
