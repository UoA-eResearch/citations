"""Fetch the snapshot files of every registry document (primary, recent and undated strata, notices excluded): the
sidecar JSON named in the inventory, then the XML and plain text it points to. Resumable; writes data/files/.
"""
import concurrent.futures as cf
import json
import time
import urllib.request
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
FILES = RUN / "data" / "files"
HTTP = "https://pmc-oa-opendata.s3.amazonaws.com/"


def get(url):
    for t in range(5):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(3 * (t + 1))
        except Exception:
            time.sleep(3 * (t + 1))
    return None


def one(row):
    pmcid, key = row
    jp = FILES / f"{pmcid}.json"
    if not jp.exists():
        b = get(HTTP + key)
        if b is None:
            return pmcid, "no-json"
        jp.write_bytes(b)
    meta = json.loads(jp.read_bytes())
    status = []
    for field, ext in (("xml_url", "xml"), ("text_url", "txt")):
        p = FILES / f"{pmcid}.{ext}"
        if p.exists():
            continue
        u = meta.get(field)
        if not u:
            status.append(f"no-{ext}-url")
            continue
        b = get(HTTP + u.replace("s3://pmc-oa-opendata/", "").split("?")[0])
        if b is None:
            status.append(f"no-{ext}")
            continue
        p.write_bytes(b)
    return pmcid, ",".join(status) or "ok"


def main():
    FILES.mkdir(parents=True, exist_ok=True)
    d = pd.read_parquet(RUN / "data" / "cohort.parquet")
    d = d[d.in_snapshot & ~d.notice & d.stratum.isin(["primary", "recent", "undated"])]
    rows = list(zip(d.pmcid, d.key))
    print(len(rows), "documents to fetch", flush=True)
    res = {}
    with cf.ThreadPoolExecutor(48) as ex:
        for i, (p, s) in enumerate(ex.map(one, rows)):
            res[p] = s
            if i % 5000 == 0:
                print(i, flush=True)
    st = pd.Series(res).value_counts().to_dict()
    json.dump(st, open(RUN / "results" / "tables" / "fetch_log.json", "w"), indent=1)
    print(st)


if __name__ == "__main__":
    main()
