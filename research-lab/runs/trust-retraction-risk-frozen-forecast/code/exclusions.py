"""Plan §1 exclusion counts (confirmation pass, D4). Sequential filters within the cohort years, per window.

Order: not type "article" -> paratext -> xpac -> no DOI -> no primary-topic domain -> domain outside Life/Health
Sciences. Writes results/tables/exclusions.json. Counts only; nothing per work is kept.
"""
import glob
import json
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pyarrow.compute as pc
import pyarrow.parquet as pq

RUN = Path(__file__).resolve().parents[1]
SNAP = "/mnt/data/ubuntu/impact-snapshot/works"
WIN = {"train": range(2015, 2020), "test": range(2021, 2023), "forward": range(2025, 2027)}
STEPS = ["in_years", "not_article", "paratext", "xpac", "no_doi", "no_primary_topic", "other_domain", "cohort"]


def work(path):
    t = pq.ParquetFile(path).read(columns=["publication_year", "type", "is_paratext", "is_xpac", "doi", "primary_topic.domain.id"])
    year = pc.fill_null(t.column("publication_year"), 0).to_numpy(zero_copy_only=False)
    pt = t.column("primary_topic").combine_chunks()
    dom = pc.fill_null(pt.field("domain").field("id"), "").to_pylist()
    dom = np.array([d.rsplit("/", 1)[-1] if d else "" for d in dom])
    has_pt = dom != ""
    art = pc.equal(pc.fill_null(t.column("type"), ""), "article").to_numpy(zero_copy_only=False)
    para = pc.fill_null(t.column("is_paratext"), False).to_numpy(zero_copy_only=False)
    xpac = pc.fill_null(t.column("is_xpac"), False).to_numpy(zero_copy_only=False)
    doi = pc.is_valid(t.column("doi")).to_numpy(zero_copy_only=False)
    bio = np.isin(dom, ["1", "4"])
    out = {}
    for w, yrs in WIN.items():
        m = np.isin(year, list(yrs))
        c = {"in_years": int(m.sum())}
        for k, keep in (("not_article", art), ("paratext", ~para), ("xpac", ~xpac), ("no_doi", doi),
                        ("no_primary_topic", has_pt), ("other_domain", bio)):
            c[k] = int((m & ~keep).sum()); m = m & keep
        c["cohort"] = int(m.sum())
        out[w] = c
    return out


if __name__ == "__main__":
    files = sorted(glob.glob(f"{SNAP}/*.parquet"))
    tot = {w: dict.fromkeys(STEPS, 0) for w in WIN}
    with ProcessPoolExecutor(int(os.environ.get("WORKERS", "10"))) as ex:
        for i, r in enumerate(ex.map(work, files, chunksize=4), 1):
            for w in r:
                for k in STEPS:
                    tot[w][k] += r[w][k]
            if i % 200 == 0:
                print(i, "files", flush=True)
    (RUN / "results" / "tables" / "exclusions.json").write_text(json.dumps(tot, indent=1) + "\n")
    print(json.dumps(tot))
