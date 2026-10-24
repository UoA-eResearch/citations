"""Exposed works, controls and citations per year from the local OpenAlex snapshot (plan section 1).

  build.py rw       Retraction Watch -> data/interim/rw.parquet (doi, retraction year, reason class)
  build.py passA    per work: wid, year, source, domain for article/review 1994-2019; RW DOIs -> wid with authors and
                    institutions -> data/interim/works/*.npz, data/interim/retracted.parquet
  build.py passB    works 1994-2019 citing any RW-retracted work: (wid, year, cited retracted wids, authors, insts)
                    -> data/interim/citers1.parquet
  build.py select1  depth-1 exposed works (window, no overlap, earliest exposure) -> data/interim/d1.parquet
  build.py passC    works citing depth-1 works -> data/interim/citers2.parquet
  build.py select2  depth-2 sample and control candidates -> data/interim/d2.parquet, data/interim/candidates.parquet
  build.py passD    citations per year to every exposed work and candidate -> data/interim/cites.parquet
"""
import glob
import os
import re
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pyarrow as pa  # noqa: E402
import pyarrow.compute as pc  # noqa: E402
import pyarrow.parquet as pq  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
INT = RUN / "data" / "interim"
(INT / "works").mkdir(parents=True, exist_ok=True)
SNAP = "/mnt/data/ubuntu/impact-snapshot/works"
RWCSV = "/mnt/data/retraction-markers/raw/retraction_watch.csv"
Y0, Y1 = 1994, 2019                                     # publication years of exposed works and controls
SEED = 20261025
WORKERS = int(os.environ.get("WORKERS", "14"))
MISCONDUCT = {"Falsification/Fabrication of Data", "Falsification/Fabrication of Image", "Manipulation of Images",
              "Misconduct by Author", "Misconduct - Official Investigation(s) and/or Finding(s)", "Investigation by ORI",
              "Paper Mill", "Compromised Peer Review", "Plagiarism of Article", "Plagiarism of Text", "Plagiarism of Image",
              "Plagiarism of Data", "Euphemisms for Plagiarism", "Duplication of/in Article", "Duplication of/in Image",
              "Duplication of Data", "Duplication of Text", "Euphemisms for Duplication", "False/Forged Authorship",
              "False/Forged Affiliation", "Rogue Editor", "Computer-Aided Content or Computer-Generated Content"}
HONEST = {"Error in Data", "Error in Analyses", "Error in Results and/or Conclusions", "Error in Methods", "Error in Image",
          "Error in Text", "Results Not Reproducible"}


def files():
    return sorted(glob.glob(f"{SNAP}/*.parquet"))


def oid(arr):
    s = pc.utf8_slice_codeunits(pc.fill_null(arr, "https://openalex.org/X0"), 22)
    return pc.cast(pc.if_else(pc.equal(s, ""), "0", s), pa.int64()).to_numpy(zero_copy_only=False)


def ndoi(s):
    return re.sub(r"^https?://(dx\.)?doi\.org/", "", str(s).strip().lower()) if isinstance(s, str) else None


def rw():
    d = pd.read_csv(RWCSV, dtype=str, encoding="utf-8", encoding_errors="replace")
    d = d[d.RetractionNature == "Retraction"].copy()
    d["doi"] = d.OriginalPaperDOI.map(ndoi)
    d["ret_date"] = pd.to_datetime(d.RetractionDate, format="%m/%d/%Y %H:%M", errors="coerce")
    d["orig_date"] = pd.to_datetime(d.OriginalPaperDate, format="%m/%d/%Y %H:%M", errors="coerce")
    d = d[d.doi.notna() & (d.doi.str.len() > 6) & ~d.doi.isin(["unavailable", "na", "n/a"])]
    reasons = d.Reason.fillna("").map(lambda r: {x.strip().lstrip("+") for x in r.split(";") if x.strip()})
    d["cls"] = ["misconduct" if r & MISCONDUCT else "honest" if r & HONEST else "other" for r in reasons]
    d["bad_order"] = d.ret_date < d.orig_date
    d = d.sort_values("ret_date").drop_duplicates("doi")
    d["ret_year"] = d.ret_date.dt.year
    out = d[["doi", "ret_year", "cls", "bad_order"]]
    out.to_parquet(INT / "rw.parquet", index=False)
    print(len(out), out.cls.value_counts().to_dict(), "bad order", int(out.bad_order.sum()))


def _flat_ids(lst_arr):
    """list<struct<...id>> column -> (offsets, int ids)."""
    off = np.asarray(lst_arr.offsets.to_numpy(), dtype=np.int64)
    return off, oid(pc.list_flatten(lst_arr).field("id")) if len(pc.list_flatten(lst_arr)) else np.array([], np.int64)


def _authors_insts(t):
    au = t.column("authorships").combine_chunks()
    flat = pc.list_flatten(au)
    a_off = np.asarray(au.offsets.to_numpy(), dtype=np.int64)
    a_ids = oid(flat.field("author").field("id"))
    inst = flat.field("institutions")
    i_off_auth = np.asarray(inst.offsets.to_numpy(), dtype=np.int64)
    i_ids = oid(pc.list_flatten(inst).field("id"))
    return a_off, a_ids, i_off_auth, i_ids


def _sets(k, a_off, a_ids, i_off_auth, i_ids):
    a = set(a_ids[a_off[k]:a_off[k + 1]].tolist()) - {0}
    lo, hi = i_off_auth[a_off[k]], i_off_auth[a_off[k + 1]]
    return a, set(i_ids[lo:hi].tolist()) - {0}


def _a(path):
    out = INT / "works" / (Path(path).stem + ".npz")
    t = pq.ParquetFile(path).read(columns=["id", "doi", "publication_year", "type", "is_paratext", "is_retracted",
                                           "primary_location.source.id", "primary_topic.domain.id", "authorships.list.element.author.id", "authorships.list.element.institutions.list.element.id"])   # leaf paths: some other leaves have corrupt pages
    year = pc.fill_null(t.column("publication_year"), 0).to_numpy(zero_copy_only=False).astype(np.int16)
    typ = pc.fill_null(t.column("type"), "").to_numpy(zero_copy_only=False)
    ok = (np.isin(typ, ["article", "review"]) & ~pc.fill_null(t.column("is_paratext"), False).to_numpy(zero_copy_only=False)
          & (year >= Y0) & (year <= Y1))
    wid = oid(t.column("id"))
    src = oid(t.column("primary_location").combine_chunks().field("source").field("id"))
    dom = pc.fill_null(t.column("primary_topic").combine_chunks().field("domain").field("id"), "").to_pylist()
    dom = np.array([int(x.rsplit("/", 1)[-1]) if x else 0 for x in dom], np.int8)
    oaret = pc.fill_null(t.column("is_retracted"), False).to_numpy(zero_copy_only=False)
    np.savez(out, wid=wid[ok], year=year[ok], src=src[ok], dom=dom[ok], oaret=oaret[ok], review=(typ[ok] == "review"))
    # RW DOIs
    dois = [ndoi(x) for x in t.column("doi").to_pylist()]
    hit = [k for k, x in enumerate(dois) if x in RWDOI]
    rows = []
    if hit:
        a_off, a_ids, i_off, i_ids = _authors_insts(t)
        for k in hit:
            a, i = _sets(k, a_off, a_ids, i_off, i_ids)
            rows.append({"doi": dois[k], "wid": int(wid[k]), "year": int(year[k]), "dom": int(dom[k]),
                         "authors": sorted(a), "insts": sorted(i)})
    return rows


RWDOI = set()


def _init_rw():
    global RWDOI
    RWDOI = set(pd.read_parquet(INT / "rw.parquet").doi)


def passA():
    rows = []
    with ProcessPoolExecutor(WORKERS, initializer=_init_rw) as ex:
        for k, r in enumerate(ex.map(_a, files(), chunksize=4), 1):
            rows += r
            if k % 200 == 0:
                print(k, "files", len(rows), "RW works", flush=True)
    d = pd.DataFrame(rows).drop_duplicates("doi")
    d.to_parquet(INT / "retracted.parquet", index=False)
    print("RW DOIs matched", len(d))


REF_SET = np.array([], np.int64)


def _init_refs(path):
    global REF_SET
    REF_SET = np.unique(pd.read_parquet(path).wid.to_numpy(np.int64))


def _refs_hits(path, keep_authors=True):
    t = pq.ParquetFile(path).read(columns=["id", "publication_year", "type", "is_paratext", "referenced_works", "authorships.list.element.author.id", "authorships.list.element.institutions.list.element.id"])
    year = pc.fill_null(t.column("publication_year"), 0).to_numpy(zero_copy_only=False).astype(np.int16)
    typ = pc.fill_null(t.column("type"), "").to_numpy(zero_copy_only=False)
    ok = (np.isin(typ, ["article", "review"]) & ~pc.fill_null(t.column("is_paratext"), False).to_numpy(zero_copy_only=False)
          & (year >= Y0) & (year <= Y1))
    refs = t.column("referenced_works").combine_chunks()
    off = np.asarray(refs.offsets.to_numpy(), dtype=np.int64)
    rid = oid(pc.list_flatten(refs))
    m = np.isin(rid, REF_SET)
    if not m.any():
        return []
    owner = np.searchsorted(off, np.nonzero(m)[0], side="right") - 1
    wid = oid(t.column("id"))
    a_off, a_ids, i_off, i_ids = _authors_insts(t)
    out = []
    for k in np.unique(owner):
        if not ok[k]:
            continue
        cited = sorted(set(rid[off[k]:off[k + 1]][m[off[k]:off[k + 1]]].tolist()))
        a, i = _sets(k, a_off, a_ids, i_off, i_ids)
        out.append({"wid": int(wid[k]), "year": int(year[k]), "cited": cited, "authors": sorted(a), "insts": sorted(i)})
    return out


def _scan(refpath, outpath):
    rows = []
    with ProcessPoolExecutor(WORKERS, initializer=_init_refs, initargs=(refpath,)) as ex:
        for k, r in enumerate(ex.map(_refs_hits, files(), chunksize=4), 1):
            rows += r
            if k % 200 == 0:
                print(k, "files", len(rows), "rows", flush=True)
    pd.DataFrame(rows).to_parquet(outpath, index=False)
    print(outpath.name, len(rows))


def passB():
    _scan(INT / "retracted.parquet", INT / "citers1.parquet")


def select1():
    R = pd.read_parquet(INT / "retracted.parquet").merge(pd.read_parquet(INT / "rw.parquet"), on="doi")
    allret = set(R.wid)
    R = R[R.ret_year.between(2000, 2021) & ~R.bad_order]
    info = {r.wid: r for r in R.itertuples()}
    C = pd.read_parquet(INT / "citers1.parquet")
    rows = []
    for c in C.itertuples():
        if c.wid in allret:
            continue
        best = None
        for r in c.cited:
            ri = info.get(r)
            if ri is None or not (ri.ret_year - 6 <= c.year <= ri.ret_year - 2):
                continue
            if set(c.authors) & set(ri.authors) or set(c.insts) & set(ri.insts):
                continue
            if best is None or ri.ret_year < best.ret_year:
                best = ri
        if best is not None:
            rows.append({"wid": c.wid, "year": c.year, "ret": best.wid, "T": int(best.ret_year), "cls": best.cls,
                         "authors": c.authors, "insts": c.insts})
    d = pd.DataFrame(rows)
    d.to_parquet(INT / "d1.parquet", index=False)
    pd.DataFrame({"wid": sorted(set(C.wid))}).to_parquet(INT / "cites_any_retracted.parquet", index=False)
    print("depth-1 exposed", len(d), "retractions", d.ret.nunique(), d.cls.value_counts().to_dict())


def passC():
    _scan(INT / "d1.parquet", INT / "citers2.parquet")


def select2():
    rng = np.random.default_rng(SEED)
    R = pd.read_parquet(INT / "retracted.parquet").merge(pd.read_parquet(INT / "rw.parquet"), on="doi")
    rinfo = {r.wid: r for r in R.itertuples()}
    D1 = pd.read_parquet(INT / "d1.parquet")
    d1ret = dict(zip(D1.wid, D1.ret))
    bad = set(pd.read_parquet(INT / "cites_any_retracted.parquet").wid) | set(D1.wid) | set(R.wid)
    C2 = pd.read_parquet(INT / "citers2.parquet")
    cand = {}
    for c in C2.itertuples():
        if c.wid in bad:                                       # cites a retracted work itself, or depth-1, or retracted
            continue
        for d in c.cited:
            r = d1ret.get(d)
            if r is None:
                continue
            ri = rinfo[r]
            if not (ri.ret_year - 6 <= c.year <= ri.ret_year - 2):
                continue
            if set(c.authors) & set(ri.authors) or set(c.insts) & set(ri.insts):
                continue
            cand.setdefault(r, set()).add((c.wid, c.year))
    rows, used = [], set()
    for r in sorted(cand, key=lambda x: rinfo[x].ret_year):
        pool = sorted(cand[r] - {u for u in cand[r] if u[0] in used})
        if not pool:
            continue
        pick = rng.choice(len(pool), min(20, len(pool)), replace=False)
        for j in pick:
            w, y = pool[j]
            used.add(w)
            rows.append({"wid": w, "year": y, "ret": r, "T": int(rinfo[r].ret_year), "cls": rinfo[r].cls})
    D2 = pd.DataFrame(rows)
    D2.to_parquet(INT / "d2.parquet", index=False)
    # control candidates: same source and year, not exposed, not citing any retracted work
    W = pd.concat([pd.DataFrame(dict(np.load(f))) for f in sorted(glob.glob(str(INT / "works" / "*.npz")))])
    W = W[~W.oaret & (W.src > 0) & ~W.wid.isin(bad) & ~W.wid.isin(set(D2.wid))]
    ex = pd.concat([D1[["wid", "year"]].assign(depth=1), D2[["wid", "year"]].assign(depth=2)])
    srcmap = W.set_index("wid").src if False else None
    allw = pd.concat([pd.DataFrame(dict(np.load(f), )) for f in sorted(glob.glob(str(INT / "works" / "*.npz")))])[["wid", "src", "dom", "year"]]
    ex = ex.merge(allw[["wid", "src", "dom"]], on="wid", how="left")
    ex.to_parquet(INT / "exposed_meta.parquet", index=False)
    cells = W.groupby(["src", "year"]).wid.apply(np.array)
    crow = []
    for e in ex.itertuples():
        if pd.isna(e.src) or (e.src, e.year) not in cells.index:
            continue
        pool = cells.loc[(e.src, e.year)]
        pick = pool[rng.choice(len(pool), min(20, len(pool)), replace=False)]
        crow += [{"exposed": e.wid, "cand": int(c)} for c in pick]
    P = pd.DataFrame(crow)
    P.to_parquet(INT / "candidates.parquet", index=False)
    print("depth-2 sampled", len(D2), "exposed with candidates", P.exposed.nunique(), "of", len(ex), "candidate rows", len(P))


TARGET = np.array([], np.int64)


def _init_target():
    global TARGET
    TARGET = np.load(INT / "targets.npy")


def _d(path):
    t = pq.ParquetFile(path).read(columns=["publication_year", "referenced_works"])
    year = pc.fill_null(t.column("publication_year"), 0).to_numpy(zero_copy_only=False).astype(np.int16)
    refs = t.column("referenced_works").combine_chunks()
    off = np.asarray(refs.offsets.to_numpy(), dtype=np.int64)
    rid = oid(pc.list_flatten(refs))
    m = np.isin(rid, TARGET)
    if not m.any():
        return pd.DataFrame(columns=["wid", "cyear", "n"])
    owner = np.searchsorted(off, np.nonzero(m)[0], side="right") - 1
    d = pd.DataFrame({"wid": rid[m], "cyear": year[owner]})
    return d.groupby(["wid", "cyear"]).size().rename("n").reset_index()


def passD():
    D1, D2 = pd.read_parquet(INT / "d1.parquet"), pd.read_parquet(INT / "d2.parquet")
    P = pd.read_parquet(INT / "candidates.parquet")
    tg = np.unique(np.concatenate([D1.wid.to_numpy(), D2.wid.to_numpy(), P.cand.to_numpy()]).astype(np.int64))
    np.save(INT / "targets.npy", tg)
    parts = []
    with ProcessPoolExecutor(WORKERS, initializer=_init_target) as ex:
        for k, r in enumerate(ex.map(_d, files(), chunksize=4), 1):
            parts.append(r)
            if k % 200 == 0:
                print(k, "files", flush=True)
    d = pd.concat(parts).groupby(["wid", "cyear"]).n.sum().reset_index()
    d.to_parquet(INT / "cites.parquet", index=False)
    print("targets", len(tg), "wid-year rows", len(d))


if __name__ == "__main__":
    {"rw": rw, "passA": passA, "passB": passB, "select1": select1, "passC": passC, "select2": select2, "passD": passD}[sys.argv[1]]()
