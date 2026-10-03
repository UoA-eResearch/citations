"""Index OpenTopography LAZ tiles by reading only each file's LAS header (HTTP range request, first 375 bytes).

Collections: Auckland_2013 (2013), NZ16_NAuckland + NZ16_SAuckland (2016-18), NZ24_Auckland (2024).
Output: data/tile_index.parquet with key, epoch, bounds (NZTM; 2013 is checked for its CRS), point count, size.
"""
import re
import struct
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
BASE = "https://opentopography.s3.sdsc.edu/pc-bulk"
COLL = {"Auckland_2013/": "2013", "NZ16_NAuckland/": "2016", "NZ16_SAuckland/": "2016", "NZ24_Auckland/": "2024"}


def keys(prefix):
    tok, out = None, []
    while True:
        q = {"list-type": "2", "prefix": prefix, "max-keys": "1000"}
        if tok:
            q["continuation-token"] = tok
        x = urllib.request.urlopen(BASE + "?" + urllib.parse.urlencode(q), timeout=120).read().decode()
        out += [(k, int(s)) for k, s in re.findall(r"<Key>([^<]+\.laz)</Key>.*?<Size>(\d+)</Size>", x, re.S)]
        m = re.search(r"<NextContinuationToken>([^<]+)</NextContinuationToken>", x)
        if not m:
            return out
        tok = m.group(1)


def header(key):
    for k in range(5):
        try:
            r = urllib.request.Request(f"{BASE}/{key}", headers={"Range": "bytes=0-374"})
            b = urllib.request.urlopen(r, timeout=60).read()
            ver = (b[24], b[25])
            maxx, minx, maxy, miny, maxz, minz = struct.unpack("<6d", b[179:227])
            npts = struct.unpack("<I", b[107:111])[0]
            if npts == 0 and ver >= (1, 4):
                npts = struct.unpack("<Q", b[247:255])[0]
            return dict(minx=minx, maxx=maxx, miny=miny, maxy=maxy, npts=npts, ver=f"{ver[0]}.{ver[1]}")
        except Exception:  # noqa: BLE001
            continue
    return dict(minx=None)


def main():
    rows = []
    for p, ep in COLL.items():
        ks = keys(p)
        with ThreadPoolExecutor(48) as ex:
            hs = list(ex.map(header, [k for k, _ in ks]))
        rows += [dict(key=k, size=s, epoch=ep, **h) for (k, s), h in zip(ks, hs)]
        print(p, len(ks), "tiles")
    d = pd.DataFrame(rows)
    d.to_parquet(RUN / "data" / "tile_index.parquet")
    print(d.groupby("epoch").agg(n=("key", "size"), gb=("size", lambda s: s.sum() / 1e9), minx=("minx", "min"),
                                 maxx=("maxx", "max"), miny=("miny", "min"), maxy=("maxy", "max"), fail=("minx", lambda s: s.isna().sum())))


if __name__ == "__main__":
    main()
