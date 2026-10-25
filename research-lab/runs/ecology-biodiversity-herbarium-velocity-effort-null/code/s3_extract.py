"""Tracheophyta preserved-specimen records, 1970-2024, from GBIF's public monthly Parquet snapshot on AWS (2026-07-01,
the snapshot the lead names; citation doi:10.15468/dl.teccpa).

Filter: phylum = Tracheophyta, basisofrecord = PRESERVED_SPECIMEN, 1970 <= year <= 2024, both coordinates present.
Only filtering happens here; no centroid or displacement is computed.

usage: s3_extract.py [THREADS]  -> data/gbif_s3/<part>.parquet, progress on stdout
"""
import re
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.fs as pafs
import pyarrow.parquet as pq

RUN = Path(__file__).resolve().parents[1]
OUT = RUN / "data" / "gbif_s3"
OUT.mkdir(parents=True, exist_ok=True)
BUCKET, SNAP = "gbif-open-data-us-east-1", "occurrence/2026-07-01/occurrence.parquet/"
FILTER_COLS = ["phylum", "basisofrecord", "year", "decimallatitude", "decimallongitude"]
KEEP = ["gbifid", "datasetkey", "institutioncode", "family", "species", "specieskey", "taxonrank", "countrycode",
        "decimallatitude", "decimallongitude", "coordinateuncertaintyinmeters", "year", "establishmentmeans",
        "occurrencestatus", "issue"]


def list_keys():
    keys, token = [], None
    while True:
        u = f"https://{BUCKET}.s3.amazonaws.com/?list-type=2&prefix={SNAP}&max-keys=1000"
        if token:
            u += "&continuation-token=" + urllib.parse.quote(token)
        s = urllib.request.urlopen(u, timeout=120).read().decode()
        keys += re.findall(r"<Key>([^<]+)</Key>", s)
        m = re.search(r"<NextContinuationToken>([^<]+)</NextContinuationToken>", s)
        if not m:
            return [k for k in keys if k.rsplit("/", 1)[-1].isdigit()]
        token = m.group(1)


def one(key, fs):
    out = OUT / (key.rsplit("/", 1)[-1] + ".parquet")
    if out.exists():
        return key, -1, -1
    for attempt in range(5):
        try:
            t = pq.read_table(f"{BUCKET}/{key}", columns=sorted(set(FILTER_COLS + KEEP)), filesystem=fs)
            break
        except Exception:                                        # transient S3 errors: retry
            if attempt == 4:
                raise
            time.sleep(10 * (attempt + 1))
    n = t.num_rows
    sel = pc.and_(pc.and_(pc.equal(t["phylum"], "Tracheophyta"), pc.equal(t["basisofrecord"], "PRESERVED_SPECIMEN")),
                  pc.and_(pc.and_(pc.greater_equal(t["year"], 1970), pc.less_equal(t["year"], 2024)),
                          pc.and_(pc.is_valid(t["decimallatitude"]), pc.is_valid(t["decimallongitude"]))))
    t = t.filter(pc.fill_null(sel, False)).select(KEEP)
    tmp = out.with_suffix(".tmp")
    pq.write_table(t, tmp, compression="zstd")
    tmp.rename(out)
    return key, n, t.num_rows


def main():
    threads = int(sys.argv[1]) if len(sys.argv) > 1 else 96
    pa.set_io_thread_count(threads * 4)          # pyarrow's own I/O pool (default 8) otherwise caps concurrency
    keys = list_keys()
    print(len(keys), "files", flush=True)
    fs = pafs.S3FileSystem(anonymous=True, region="us-east-1", connect_timeout=60, request_timeout=600)
    tot_in = tot_out = done = 0
    with ThreadPoolExecutor(threads) as ex:
        futs = [ex.submit(one, k, fs) for k in keys]
        for f in as_completed(futs):
            k, n, m = f.result()
            done += 1
            if n >= 0:
                tot_in += n
                tot_out += m
            if done % 100 == 0:
                print(time.strftime("%H:%M:%S"), done, "of", len(keys), "rows in", tot_in, "kept", tot_out, flush=True)
    print("== done", done, "rows in", tot_in, "kept", tot_out, flush=True)


if __name__ == "__main__":
    main()
