"""Record-level GBIF attributes for SAGE's training taxa, from GBIF's public monthly Parquet snapshot on AWS.

SAGE's own download (doi:10.15468/dl.jd7xfa, 38.4 GB zip) is served at about 60 KB/s per connection with at most
two or three connections, so the needed columns are read from the 2026-02-01 snapshot instead (19 days before the
download was created), filtered with the download's own predicate (TAXON_KEY in its 5,863 keys).

usage: s3_extract.py [THREADS]  -> data/gbif_s3/<part>.parquet, logs progress
"""
import json
import sys
import time
import urllib.request
import re
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.fs as pafs
import pyarrow.parquet as pq

RUN = Path(__file__).resolve().parents[1]
OUT = RUN / "data" / "gbif_s3"
OUT.mkdir(parents=True, exist_ok=True)
BUCKET, SNAP = "gbif-open-data-us-east-1", "occurrence/2026-02-01/occurrence.parquet/"
COLS = ["datasetkey", "kingdom", "species", "specieskey", "taxonkey", "taxonrank", "countrycode", "decimallatitude",
        "decimallongitude", "coordinateuncertaintyinmeters", "basisofrecord", "occurrencestatus", "year", "month", "day"]
meta = json.loads((RUN / "data" / "registry" / "download_meta.json").read_text())
KEYS = pa.array(meta["request"]["predicate"]["predicates"][0]["values"], pa.string())


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
            t = pq.read_table(f"{BUCKET}/{key}", columns=COLS, filesystem=fs)
            break
        except Exception as e:                                    # transient S3 errors: retry
            if attempt == 4:
                raise
            time.sleep(10 * (attempt + 1))
    n = t.num_rows
    sel = pc.and_(pc.or_(pc.is_in(t["specieskey"], value_set=KEYS), pc.is_in(t["taxonkey"], value_set=KEYS)),
                  pc.and_(pc.is_valid(t["decimallatitude"]), pc.is_valid(t["decimallongitude"])))
    t = t.filter(sel)
    tmp = out.with_suffix(".tmp")
    pq.write_table(t, tmp, compression="zstd")
    tmp.rename(out)
    return key, n, t.num_rows


def main():
    import urllib.parse  # noqa: F401  (used in list_keys)
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
                tot_in += n; tot_out += m
            if done % 100 == 0:
                print(time.strftime("%H:%M:%S"), done, "of", len(keys), "rows in", tot_in, "kept", tot_out, flush=True)
    print("== done", done, "rows in", tot_in, "kept", tot_out, flush=True)


if __name__ == "__main__":
    import urllib.parse
    main()
