"""Read CHIRP and CHIRPS pentad values at every gauge by HTTP range request (plan section 2). Resumable; a failed read is
written as an error row, never as a value.
Usage: venv/bin/python code/extract_pentads.py chirp|chirps [first_year last_year part]
  Parallel workers take disjoint year ranges and write data/extract/<product><part>.csv; resumption skips a pentad already
  read into any part file.
CHIRPS (tiled, compressed COGs) is read through GDAL /vsicurl/. CHIRP pentads are uncompressed striped float32 GeoTIFFs,
read directly: the file's tags and strip offsets, then one multi-range request for the 4 bytes of each gauge's cell
(the same cell rasterio's sample() reads; checked against GDAL reads in code/check_chirp_reader.py).
Writes pentad (yyyy.mm.k), status, station, value (mm/pentad; empty where the cell is masked)."""
import csv
import glob
import re
import struct
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
import requests
from rasterio.env import Env

RUN = Path(__file__).resolve().parents[1]
URL = {"chirp": "https://data.chc.ucsb.edu/products/CHIRP/pentads/CHIRP.{y}.{m:02d}.{k}.tif",
       "chirps": "https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_pentad/cogs/chirps-v2.0.{y}.{m:02d}.{k}.cog"}
UA = "research-lab rainfall study (mailto:noreply@anthropic.com)"
ENV = dict(GDAL_HTTP_USERAGENT=UA, GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
           CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif,.cog", GDAL_HTTP_MAX_RETRY="4", GDAL_HTTP_RETRY_DELAY="10", GDAL_HTTP_MULTIRANGE="YES",
           GDAL_HTTP_MERGE_CONSECUTIVE_RANGES="YES", VSI_CACHE="FALSE")
S = requests.Session(); S.headers["User-Agent"] = UA


def _range(url, spec):
    for i in range(4):
        try:
            r = S.get(url, headers={"Range": f"bytes={spec}"}, timeout=120)
            if r.status_code == 206:
                return r
            raise IOError(f"HTTP {r.status_code}")
        except Exception:  # noqa: BLE001
            if i == 3:
                raise
            time.sleep(10 * (i + 1))


def chirp_read(url, rows, cols):
    """Values of an uncompressed, single-band float32 striped TIFF at (row, col) cells; NaN outside the raster."""
    h = _range(url, "0-15").content
    bo = "<" if h[:2] == b"II" else ">"
    ifd_off = struct.unpack(bo + "I", h[4:8])[0]
    tail = _range(url, f"{ifd_off}-{ifd_off + 20000}").content
    n = struct.unpack(bo + "H", tail[:2])[0]
    tags = {}
    for i in range(n):
        tag, typ, cnt = struct.unpack(bo + "HHI", tail[2 + 12 * i:10 + 12 * i])
        raw = tail[10 + 12 * i:14 + 12 * i]
        tags[tag] = (typ, cnt, raw)
    short = lambda t: struct.unpack(bo + "H", tags[t][2][:2])[0]
    W, Hh = short(256), short(257)
    assert short(258) == 32 and short(259) == 1 and short(277) == 1 and short(339) == 3 and short(278) == 1, "unexpected layout"
    typ, cnt, raw = tags[273]
    assert cnt == Hh
    fmt, size = ("I", 4) if typ == 4 else ("H", 2)
    so_off = struct.unpack(bo + "I", raw)[0] - ifd_off
    offs = struct.unpack(bo + fmt * cnt, tail[so_off:so_off + size * cnt])
    vals = np.full(len(rows), np.nan)
    inside = [i for i, (r, c) in enumerate(zip(rows, cols)) if 0 <= r < Hh and 0 <= c < W]
    want = sorted({offs[rows[i]] + 4 * cols[i] for i in inside})
    got = {}
    resp = _range(url, ",".join(f"{o}-{o + 3}" for o in want))
    if resp.headers.get("Content-Type", "").startswith("multipart/byteranges"):
        bnd = re.search(r"boundary=(\S+)", resp.headers["Content-Type"]).group(1).strip('"').encode()
        for part in resp.content.split(b"--" + bnd):
            m = re.search(rb"Content-Range: bytes (\d+)-(\d+)/\d+\r\n\r\n", part, re.I)
            if m:
                a, b = int(m[1]), int(m[2]); body = part[m.end():m.end() + (b - a + 1)]
                for o in range(a, b + 1, 4):
                    got[o] = struct.unpack(bo + "f", body[o - a:o - a + 4])[0]
    else:   # a single range came back
        a = int(re.search(r"bytes (\d+)-", resp.headers["Content-Range"])[1])
        for o in want:
            got[o] = struct.unpack(bo + "f", resp.content[o - a:o - a + 4])[0]
    for i in inside:
        vals[i] = got[offs[rows[i]] + 4 * cols[i]]
    return vals


def main(prod, y0=1981, y1=2025, part=""):
    st = pd.read_csv(RUN / "data" / "raw" / "ghcn" / "stations.csv")
    ext = RUN / "data" / "extract"; ext.mkdir(parents=True, exist_ok=True)
    out = ext / f"{prod}{part}.csv"
    done = set()
    for f in glob.glob(str(ext / f"{prod}*.csv")):
        if re.fullmatch(prod + r"(_[a-z0-9]+)?\.csv", Path(f).name) and Path(f).stat().st_size:
            done |= set(pd.read_csv(f, usecols=["pentad", "status"]).query("status == 'ok'").pentad)
    pts = list(zip(st.lon, st.lat))
    with open(out, "a", newline="") as fh, Env(**ENV):
        w = csv.writer(fh)
        if out.stat().st_size == 0:
            w.writerow(["pentad", "status", "station", "value"])
        rc = None
        n = 0
        for y in range(y0, y1 + 1):
            for m in range(1, 13):
                for k in range(1, 7):
                    pid = f"{y}.{m:02d}.{k}"
                    if pid in done:
                        continue
                    url = URL[prod].format(y=y, m=m, k=k)
                    try:
                        if prod == "chirp":
                            if rc is None:
                                with rasterio.open("/vsicurl/" + url) as r:
                                    rc = [r.index(x, yy) for x, yy in pts]
                            vals = chirp_read(url, [a for a, _ in rc], [b for _, b in rc])
                        else:
                            with rasterio.open("/vsicurl/" + url) as r:
                                vals = np.array([v[0] for v in r.sample(pts)], dtype=float)
                        vals[(vals <= -999) | ~np.isfinite(vals)] = np.nan
                        w.writerows([pid, "ok", s, "" if np.isnan(v) else round(float(v), 3)] for s, v in zip(st.id, vals))
                    except Exception as e:  # noqa: BLE001
                        w.writerow([pid, "error", "", str(e)[:120]])
                        time.sleep(30)
                    fh.flush(); n += 1
                    if n % 50 == 0:
                        print(prod, pid, n, flush=True)
    print(prod, "done", flush=True)


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], *(map(int, a[1:3]) if len(a) > 2 else ()), *(a[3:4] if len(a) > 3 else ()))
