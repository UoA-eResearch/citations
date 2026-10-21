"""One pass over the 55 GB opinions archive, keeping only opinions in the study window (plan section 1).

Reading the archive is the slow step: about 300 GB of CSV through one parser. The pilot and the full screen both
need the in-window opinions, so they are extracted once into 32 gzip shards (by cluster id) that later stages read
in parallel. HTML is not stripped here, to keep the single reader light; screen workers do that.

Writes data/opinions/shard_NN.jsonl.gz (one JSON object per opinion: opinion_id, cluster_id, date, ocr, type,
field, raw) and data/opinions/extract_log.json.
"""
import gzip
import io
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import clcsv  # noqa: E402  the bulk files' PostgreSQL CSV dialect

RUN = Path(__file__).resolve().parents[1]
RAW, IDX, OUT = RUN / "data" / "raw", RUN / "data" / "index", RUN / "data" / "opinions"
DATE_FROM, DATE_TO = 20190101, 20260930
SHARDS = 32
TEXT_FIELDS = ("plain_text", "html_with_citations", "html", "html_lawbox", "html_columbia", "html_anon_2020",
               "xml_harvard")


def main():
    import indexed_bzip2
    OUT.mkdir(parents=True, exist_ok=True)
    m = np.load(IDX / "cluster_meta.npz")
    keep = (m["dates"] >= DATE_FROM) & (m["dates"] <= DATE_TO)
    date_of = dict(zip(m["ids"][keep].tolist(), m["dates"][keep].tolist()))
    print(f"{len(date_of):,} in-window clusters", flush=True)
    outs = [gzip.open(OUT / f"shard_{i:02d}.jsonl.gz", "wt", compresslevel=1, encoding="utf-8") for i in range(SHARDS)]
    t0, seen, kept, no_text = time.time(), 0, 0, 0
    with indexed_bzip2.open(str(RAW / "opinions.csv.bz2"), parallelization=12) as raw:
        for row in clcsv.reader(io.TextIOWrapper(raw, encoding="utf-8", errors="ignore", newline="")):
            seen += 1
            try:
                cid = int(row.get("cluster_id") or 0)
            except ValueError:
                continue
            date = date_of.get(cid)
            if date is None:
                continue
            field = next((f for f in TEXT_FIELDS if len(row.get(f) or "") > 200), None)
            if field is None:
                no_text += 1
                continue
            rec = dict(opinion_id=int(row.get("id") or 0), cluster_id=cid, date=date,
                       ocr=row.get("extracted_by_ocr"), type=row.get("type"), field=field, raw=row[field])
            outs[cid % SHARDS].write(json.dumps(rec) + "\n")
            kept += 1
            if seen % 1_000_000 == 0:
                print(f"  read {seen:,} opinions, kept {kept:,} in window, {(time.time() - t0) / 60:.0f} min",
                      flush=True)
    for o in outs:
        o.close()
    log = dict(opinions_read=seen, kept_in_window=kept, in_window_without_text=no_text,
               minutes=round((time.time() - t0) / 60, 1))
    json.dump(log, open(OUT / "extract_log.json", "w"), indent=1)
    print(json.dumps(log), flush=True)


if __name__ == "__main__":
    main()
