"""Resumable parallel download of the ChEMBL SQLite releases (EBI caps this host at about 60-100 KB/s, so a sub-range
cannot finish inside one bounded curl call; each attempt appends the bytes it got and the next resumes from there).

  fetch.py REL [N]  -> data/raw/chembl_<REL>_sqlite.tar.gz (N sub-ranges, default 8), size checked
"""
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
SIZES = {33: 4735615261, 37: 5764252857}


def sub(url, i, s, e, base):
    f = RAW / f"{base}.part{i}"
    want = e - s + 1
    for attempt in range(100000):
        have = f.stat().st_size if f.exists() else 0
        if have == want:
            return i
        if have > want:
            raise SystemExit(f"part {i} overshot")
        tmp = RAW / f"{base}.part{i}.tmp"
        r = subprocess.run(["curl", "-fsL", "-m", "1800", "-o", str(tmp), "-w", "%{http_code}", "-r", f"{s + have}-{e}", url],
                           capture_output=True, text=True)
        got = tmp.stat().st_size if tmp.exists() else 0
        if r.stdout.strip() == "206":                    # a range response, complete or cut by the time limit
            if 0 < got <= want - have:
                with open(f, "ab") as w, open(tmp, "rb") as rd:
                    w.write(rd.read())
        if tmp.exists():
            tmp.unlink()
        if got == 0:
            time.sleep(10)
    raise SystemExit(f"part {i} did not finish")


def main(rel, n=8):
    base = f"chembl_{rel}_sqlite.tar.gz"
    url = f"https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/releases/chembl_{rel}/{base}"
    size = SIZES[rel]
    step = (size + n - 1) // n
    ranges = [(i, i * step, min(size - 1, (i + 1) * step - 1)) for i in range(n)]
    with ThreadPoolExecutor(n) as ex:
        list(ex.map(lambda a: sub(url, a[0], a[1], a[2], base), ranges))
    out = RAW / base
    with open(out, "wb") as w:
        for i, _, _ in ranges:
            p = RAW / f"{base}.part{i}"
            with open(p, "rb") as r:
                while True:
                    b = r.read(1 << 24)
                    if not b:
                        break
                    w.write(b)
            p.unlink()
    assert out.stat().st_size == size, "size mismatch"
    print("ok", out, size, flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) > 2 else 8)
