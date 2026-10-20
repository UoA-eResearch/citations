"""Build the citation resolution index from the CourtListener citations table (plan section 4, step 2).

The table maps every reporter-volume-page the corpus knows to the cluster it belongs to: 18,130,236 rows in the
2026-09-30 snapshot. The index is stored per (reporter, volume) as a sorted array of first pages with the
matching cluster ids, which supports both exact lookup and the containment test a pin cite needs — a citation to
page 1342 of a case reported at 1339 resolves to that case, because 1339 is the nearest first page at or below
it and the next case starts later.

Writes data/index/pages.npz and data/index/meta.json.
"""
import bz2
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import clcsv  # noqa: E402  the bulk files' PostgreSQL CSV dialect

import numpy as np

RUN = Path(__file__).resolve().parents[1]
RAW, IDX = RUN / "data" / "raw", RUN / "data" / "index"
csv.field_size_limit(sys.maxsize)


def norm_reporter(r):
    """Fold the spacing and punctuation variants that the same reporter appears under."""
    return "".join(ch for ch in r.lower() if ch.isalnum())


def main():
    IDX.mkdir(parents=True, exist_ok=True)
    per = {}                      # (reporter, volume) -> list of (page, cluster_id)
    kinds = {}
    n = bad = wild = 0
    MAX_PAGE, MAX_VOL = 999_999, 999_999   # the table carries a few absurd values (one page of 5,837,932,014)
    with bz2.open(RAW / "citations.csv.bz2", "rt", encoding="utf-8", errors="ignore", newline="") as fh:
        for row in clcsv.reader(fh):
            try:
                vol = int(row["volume"])
                page = int(row["page"])
                cid = int(row["cluster_id"])
            except (ValueError, TypeError):
                bad += 1              # page numbers like "1339n" or blank volumes
                continue
            if not (1 <= page <= MAX_PAGE and 1 <= vol <= MAX_VOL):
                wild += 1
                continue
            rep = norm_reporter(row["reporter"])
            per.setdefault((rep, vol), []).append((page, cid))
            kinds[row["type"]] = kinds.get(row["type"], 0) + 1
            n += 1
            if n % 2_000_000 == 0:
                print(f"  {n:,} rows, {len(per):,} reporter-volumes", flush=True)

    keys = sorted(per)
    print(f"{n:,} usable rows ({bad:,} unparseable, {wild:,} out of range), {len(keys):,} reporter-volumes", flush=True)

    # flatten into three arrays plus an offset table, so the whole index is a few numpy arrays
    offs = np.zeros(len(keys) + 1, dtype=np.int64)
    for i, k in enumerate(keys):
        offs[i + 1] = offs[i] + len(per[k])
    pages = np.zeros(offs[-1], dtype=np.int32)
    clusters = np.zeros(offs[-1], dtype=np.int64)
    for i, k in enumerate(keys):
        rows = sorted(per[k])
        a, b = offs[i], offs[i + 1]
        pages[a:b] = [p for p, _ in rows]
        clusters[a:b] = [c for _, c in rows]

    np.savez_compressed(IDX / "pages.npz", offs=offs, pages=pages, clusters=clusters,
                        reporters=np.array([k[0] for k in keys]), volumes=np.array([k[1] for k in keys],
                                                                                  dtype=np.int32))
    json.dump({"rows": n, "unparseable": bad, "out_of_range": wild, "reporter_volumes": len(keys),
               "distinct_reporters": len({k[0] for k in keys}), "citation_types": kinds},
              open(IDX / "meta.json", "w"), indent=1)
    print(f"wrote {IDX / 'pages.npz'}")


if __name__ == "__main__":
    main()
