"""Download PHARMAC's monthly XML archives (plan D2): the community Pharmaceutical Schedule
(/pub/schedule/archive/<year>/Schedule_YYYY-MM.xml, 2006-2026) and the Hospital Medicines List
(/pub/HML/archive/<year>/<date>/HML_<date>.xml, 2011-2025), plus the current HML. One request at a time, 1 s apart,
resumable; sha256 in data/raw/pharmac/xml/MANIFEST.tsv."""
import hashlib
import re
import sys
import time
from pathlib import Path

import requests

RUN = Path(__file__).resolve().parents[1]
D = RUN / "data" / "raw" / "pharmac" / "xml"
BASE = "https://schedule.pharmac.govt.nz"
S = requests.Session(); S.headers["User-Agent"] = "research-lab medicines-access study (mailto:noreply@anthropic.com)"


def links(path, pat):
    h = S.get(BASE + path, timeout=60).text
    return sorted(set(re.findall(pat, h)))


def main():
    D.mkdir(parents=True, exist_ok=True)
    todo = []
    for y in range(2006, 2027):
        todo += links(f"/pub/schedule/archive/{y}/", rf'href="(/pub/schedule/archive/{y}/Schedule_[0-9-]+\.xml)"'); time.sleep(1)
    todo += links("/pub/schedule/archive/", r'href="(/pub/schedule/archive/Schedule_[0-9-]+\.xml)"')
    for y in range(2011, 2027):
        for m in links(f"/pub/HML/archive/{y}/", rf'href="(/pub/HML/archive/{y}/[0-9-]+)"'):
            todo += links(m + "/", r'href="(/pub/HML/archive/[^"]+/HML_[0-9-]+\.xml)"'); time.sleep(1)
    todo += links("/pub/HML/", r'href="(/pub/HML/HML_[0-9-]+\.xml)"')
    man = D / "MANIFEST.tsv"
    done = {l.split("\t")[0] for l in open(man)} if man.exists() else set()
    print(len(todo), "files listed", flush=True)
    with open(man, "a") as fh:
        for p in todo:
            if p in done:
                continue
            out = D / ("HML" if "/HML/" in p else "schedule") / p.rsplit("/", 1)[1]
            out.parent.mkdir(parents=True, exist_ok=True)
            for k in range(4):
                try:
                    r = S.get(BASE + p, timeout=180)
                    if r.status_code == 200 and r.content.lstrip()[:5] == b"<?xml":
                        out.write_bytes(r.content)
                        fh.write(f"{p}\t{len(r.content)}\t{hashlib.sha256(r.content).hexdigest()}\n"); fh.flush()
                        break
                    print("status", r.status_code, p, flush=True)
                except Exception as e:
                    print("err", p, str(e)[:80], flush=True)
                time.sleep(5 * (k + 1))
            time.sleep(1)
    print("xml done", flush=True)


if __name__ == "__main__":
    sys.exit(main())
