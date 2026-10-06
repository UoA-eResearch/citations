"""Download GovInfo daily Federal Register issues (bulk XML) for every publication date in the metadata. Issues dated
2026-01-01 or later (the announcement month and the outcome window) are stored in data/sealed/daily/ and NOT parsed
until the plan and estimator validation are committed; a SHA-256 manifest is written. Earlier issues go to
data/raw/daily/. Replaces fetch_xml.py (the per-document API took ~11 s per request)."""
import hashlib
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
SEAL_FROM = "2026-01-01"


def fetch(date):
    y, m, _ = date.split("-")
    sub = "sealed" if date >= SEAL_FROM else "raw"
    dest = RUN / "data" / sub / "daily" / f"FR-{date}.xml"
    if dest.exists() and dest.stat().st_size > 0:
        return date, "cached"
    url = f"https://www.govinfo.gov/bulkdata/FR/{y}/{m}/FR-{date}.xml"
    for attempt in range(5):
        try:
            dest.write_bytes(urllib.request.urlopen(url, timeout=180).read())
            return date, "ok"
        except Exception as e:  # noqa: BLE001
            err = str(e)[:60]
            time.sleep(3 * (attempt + 1))
    return date, "fail:" + err


def main():
    m = pd.read_parquet(RUN / "data" / "meta" / "fr_meta.parquet")
    dates = sorted(m.publication_date.unique())
    with ThreadPoolExecutor(6) as ex:
        res = list(ex.map(fetch, dates))
    print(pd.Series([s.split(":")[0] for _, s in res]).value_counts().to_dict(), [r for r in res if r[1].startswith("fail")][:5])
    sealed = sorted((RUN / "data" / "sealed" / "daily").glob("*.xml"))
    h, lines = hashlib.sha256(), []
    for f in sealed:
        d = hashlib.sha256(f.read_bytes()).hexdigest()
        lines.append(f"{d}  {f.name}")
        h.update(d.encode())
    (RUN / "data" / "SEALED_MANIFEST.sha256").write_text("\n".join(lines) + "\n")
    print("sealed issues:", len(sealed), "| manifest digest:", h.hexdigest())


if __name__ == "__main__":
    main()
