"""Pass 2: extract the cohort (plan section 1) with the raw lists its features need. Writes data/cohort_raw/<n>.npz.

Cohort: type "article", not paratext, not xpac, with a DOI, primary topic in Life Sciences (domains/1) or Health
Sciences (domains/4), publication year in 2015-2019, 2021-2022 or 2025-2026.
"""
import glob
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pyarrow.compute as pc
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pass1 import SNAP, oid  # noqa: E402
import pyarrow as pa  # noqa: E402


def tid(arr):
    """Topic ids ("https://openalex.org/domains/2", ".../fields/27") -> int64; null -> 0."""
    s = pc.replace_substring_regex(pc.fill_null(arr, "x/0"), r"^.*/[A-Za-z]*", "")
    return pc.cast(pc.if_else(pc.equal(s, ""), "0", s), pa.int64()).to_numpy(zero_copy_only=False)

RUN = Path(__file__).resolve().parents[1]
OUT = RUN / "data" / "cohort_raw"
YEARS = {2015, 2016, 2017, 2018, 2019, 2021, 2022, 2025, 2026}
COLS = ["id", "doi", "publication_year", "type", "is_paratext", "is_xpac", "primary_topic.domain.id", "primary_topic.field.id",
        "primary_location.source.id", "primary_location.source.type", "primary_location.source.host_organization",
        "open_access.is_oa", "authors_count", "authorships.list.element.author.id",
        "authorships.list.element.author_position", "authorships.list.element.countries.list.element",
        "authorships.list.element.institutions.list.element.id", "referenced_works.list.element"]
STYPE = {"journal": 1, "repository": 2, "conference": 3, "ebook platform": 4, "book series": 5}


def offsets(lst):
    return np.asarray(lst.offsets.to_numpy(), dtype=np.int64)


def work(path):
    n = Path(path).stem.split("part_")[-1] + "_" + Path(path).stem.split("updated_date=")[-1][:10]
    out = OUT / f"{n}.npz"
    if out.exists():
        return n, 0, 0
    t = pq.ParquetFile(path).read(columns=COLS)
    total = t.num_rows
    year = pc.fill_null(t.column("publication_year"), 0).to_numpy(zero_copy_only=False)
    dom = t.column("primary_topic").combine_chunks().field("domain").field("id")
    dom = tid(dom)
    m = (pc.equal(pc.fill_null(t.column("type"), ""), "article").to_numpy(zero_copy_only=False)
         & ~pc.fill_null(t.column("is_paratext"), False).to_numpy(zero_copy_only=False)
         & ~pc.fill_null(t.column("is_xpac"), False).to_numpy(zero_copy_only=False)
         & pc.is_valid(t.column("doi")).to_numpy(zero_copy_only=False)
         & np.isin(dom, [1, 4]) & np.isin(year, list(YEARS)))
    idx = np.where(m)[0]
    if len(idx) == 0:
        np.savez(out, empty=np.array([1]))
        return n, total, 0
    t = t.take(idx)
    loc = t.column("primary_location").combine_chunks().field("source")
    stype = np.array([STYPE.get(s, 9) if s else 0 for s in loc.field("type").to_pylist()], dtype=np.int8)
    field = tid(t.column("primary_topic").combine_chunks().field("field").field("id"))
    au = t.column("authorships").combine_chunks()
    flat = pc.list_flatten(au)
    aid = oid(flat.field("author").field("id"))
    pos = np.array([p == "first" for p in flat.field("author_position").to_pylist()])
    ctry_l = flat.field("countries")
    inst_l = flat.field("institutions")
    refs = t.column("referenced_works").combine_chunks()
    np.savez(out, wid=oid(t.column("id")), year=year[idx].astype(np.int16), src=oid(loc.field("id")),
             host=oid(loc.field("host_organization")), stype=stype, field=field.astype(np.int32),
             oa=pc.fill_null(t.column("open_access").combine_chunks().field("is_oa"), False).to_numpy(zero_copy_only=False),
             nauth=pc.fill_null(t.column("authors_count"), 0).to_numpy(zero_copy_only=False).astype(np.int32),
             doi=np.array(pc.utf8_lower(t.column("doi")).to_pylist()),
             au_off=offsets(au), au_id=aid, au_first=pos,
             ct_off=offsets(ctry_l), ct=np.array(pc.list_flatten(ctry_l).to_pylist(), dtype="U2"),
             in_off=offsets(inst_l), in_id=oid(pc.list_flatten(inst_l).field("id")),
             rf_off=offsets(refs), rf=oid(pc.list_flatten(refs)))
    return n, total, len(idx)


def main(workers=12):
    OUT.mkdir(parents=True, exist_ok=True)
    files = sorted(glob.glob(f"{SNAP}/*.parquet"))
    done = rows = kept = 0
    with ProcessPoolExecutor(workers) as ex:
        for n, a, b in ex.map(work, files, chunksize=4):
            done += 1; rows += a; kept += b
            if done % 100 == 0:
                print(done, "files", rows, "rows", kept, "cohort", flush=True)
    print("pass 2 done", done, rows, kept)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 12)
