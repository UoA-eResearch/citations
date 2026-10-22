"""Pass 1 over every snapshot works file (plan sections 1-3): the works lookup and the as-of aggregates.

Per file, written to data/pass1/<n>.parquet tables:
  lookup   wid, year, src, host, ret_year (0 = not retracted), article (type == "article")
  afirst   author id, first publication year in this file
  aret     author id, retraction year, for every authorship of a retracted work (any type or field)
  ent      entity kind (S source, H host organisation, I institution), entity id, publication year,
           articles, and per retraction year the retracted articles (ret_year, 0 = none)
"""
import glob
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

RUN = Path(__file__).resolve().parents[1]
SNAP = "/mnt/data/ubuntu/impact-snapshot/works"
OUT = RUN / "data" / "pass1"
COLS = ["id", "doi", "publication_year", "type", "primary_location.source.id", "primary_location.source.host_organization",
        "authorships.list.element.author.id", "authorships.list.element.institutions.list.element.id"]
RET = None


def oid(arr):
    """OpenAlex URL ids ("https://openalex.org/W123") -> int64; null -> 0."""
    s = pc.utf8_slice_codeunits(pc.fill_null(arr, "https://openalex.org/X0"), 22)
    return pc.cast(pc.if_else(pc.equal(s, ""), "0", s), pa.int64()).to_numpy(zero_copy_only=False)


def ndoi(arr):
    s = pc.utf8_lower(pc.fill_null(arr, ""))
    return pc.replace_substring_regex(s, r"^https?://(dx\.)?doi\.org/", "")


def init():
    global RET
    lab = pd.read_parquet(RUN / "data" / "labels.parquet")
    RET = dict(zip(lab.doi, lab.date.dt.year.astype(int)))


def work(path):
    n = Path(path).stem.split("part_")[-1] + "_" + Path(path).stem.split("updated_date=")[-1][:10]
    out = OUT / f"{n}.npz"
    if out.exists():
        return n, 0
    t = pq.ParquetFile(path).read(columns=COLS)
    wid = oid(t.column("id"))
    year = pc.fill_null(t.column("publication_year"), 0).to_numpy(zero_copy_only=False).astype(np.int16)
    loc = t.column("primary_location").combine_chunks()
    srcs = loc.field("source")
    src = oid(srcs.field("id"))
    host = oid(srcs.field("host_organization"))
    doi = ndoi(t.column("doi")).to_pylist()
    ret = np.array([RET.get(d, 0) for d in doi], dtype=np.int16)
    art = pc.equal(pc.fill_null(t.column("type"), ""), "article").to_numpy(zero_copy_only=False)
    au = t.column("authorships").combine_chunks()
    par = pc.list_parent_indices(au).to_numpy()
    flat = pc.list_flatten(au)
    aid = oid(flat.field("author").field("id"))
    inst_l = flat.field("institutions")
    ipar_a = pc.list_parent_indices(inst_l).to_numpy()
    iid = oid(pc.list_flatten(inst_l).field("id"))
    ipar = par[ipar_a]
    # author first year
    m = (aid > 0) & (year[par] > 0)
    af = pd.DataFrame({"a": aid[m], "y": year[par][m]}).groupby("a").y.min().reset_index()
    # retracted authorships
    rm = ret[par] > 0
    ar = pd.DataFrame({"a": aid[rm & (aid > 0)], "r": ret[par][rm & (aid > 0)]})
    # entity counts: articles only, per (entity, pub year, ret year)
    ents = []
    for kind, ids, rows in (("S", src, np.arange(len(wid))), ("H", host, np.arange(len(wid))), ("I", iid, ipar)):
        e = pd.DataFrame({"e": ids, "row": rows})
        e = e[(e.e > 0)].drop_duplicates()
        e = e[art[e.row] & (year[e.row] > 0)]
        g = pd.DataFrame({"k": kind, "e": e.e.values, "y": year[e.row.values], "r": ret[e.row.values]})
        ents.append(g.groupby(["k", "e", "y", "r"]).size().rename("n").reset_index())
    ent = pd.concat(ents)
    np.savez(out, wid=wid, year=year, src=src, host=host, ret=ret, art=art,
             af_a=af.a.values, af_y=af.y.values.astype(np.int16), ar_a=ar.a.values, ar_r=ar.r.values.astype(np.int16),
             ent_k=ent.k.values.astype("U1"), ent_e=ent.e.values, ent_y=ent.y.values.astype(np.int16),
             ent_r=ent.r.values.astype(np.int16), ent_n=ent.n.values.astype(np.int32))
    return n, len(wid)


def main(workers=12):
    OUT.mkdir(parents=True, exist_ok=True)
    files = sorted(glob.glob(f"{SNAP}/*.parquet"))
    done, rows = 0, 0
    with ProcessPoolExecutor(workers, initializer=init) as ex:
        for n, k in ex.map(work, files, chunksize=4):
            done += 1
            rows += k
            if done % 100 == 0:
                print(done, "files", rows, "rows", flush=True)
    print("pass 1 done", done, rows)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 12)
