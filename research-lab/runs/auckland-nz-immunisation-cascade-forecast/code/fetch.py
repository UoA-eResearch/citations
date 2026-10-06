"""Download Health NZ childhood immunisation coverage files: the current page's XLSX files (2023/24 onward) and the
archived 3-month and 12-month files (2008-2023) from the Internet Archive. Logs URL, capture timestamp, size and
sha256 to data/raw/manifest.csv."""
import csv
import hashlib
import re
import time
from pathlib import Path
from urllib.parse import unquote

import requests

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
UA = {"User-Agent": "Mozilla/5.0 (research; UoA eResearch)"}
PAGE = "https://www.healthnz.govt.nz/about-us/health-data/data-sets-and-collections/immunisation-data-and-statistics/immunisation-coverage"
CDX = ("https://web.archive.org/cdx/search/cdx?url=www.tewhatuora.govt.nz/assets/For-the-health-sector/Health-sector-guidance/"
       "Vaccine-information-for-healthcare-professionals/{p}/&matchType=prefix&filter=statuscode:200&collapse=urlkey&output=json")
ARCH = {"archive3m": "Immunisation-coverage-data-three-month-reporting-period", "archive12m": "12month-Immunisation-Coverage-Data"}


def get(url, tries=5):
    for i in range(tries):
        try:
            r = requests.get(url, headers=UA, timeout=120)
            if r.status_code == 200:
                return r
        except requests.RequestException:
            pass
        time.sleep(5 * (i + 1))
    raise RuntimeError(f"failed {url}")


def main():
    rows = []
    html = get(PAGE).text
    for u in sorted(set(re.findall(r'href="(https://static\.info\.content\.health\.nz/[^"]+\.xlsx)"', html))):
        f = RAW / "current" / Path(u).name
        if not f.exists():
            f.write_bytes(get(u).content)
        rows.append(dict(source="current", url=u, timestamp="", file=str(f.relative_to(RUN)), bytes=f.stat().st_size, sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
    for sub, path in ARCH.items():
        caps = get(CDX.format(p=path)).json()[1:]
        for c in caps:
            ts, orig = c[1], c[2]
            if not re.search(r"\.(xlsx|xls)$", orig, re.I):
                continue
            f = RAW / sub / unquote(Path(orig).name)
            if not f.exists():
                f.write_bytes(get(f"https://web.archive.org/web/{ts}id_/{orig}").content)
                time.sleep(1.5)
            rows.append(dict(source=sub, url=orig, timestamp=ts, file=str(f.relative_to(RUN)), bytes=f.stat().st_size, sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
    with open(RAW / "manifest.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print({s: sum(r["source"] == s for r in rows) for s in ("current", "archive3m", "archive12m")})


if __name__ == "__main__":
    main()
