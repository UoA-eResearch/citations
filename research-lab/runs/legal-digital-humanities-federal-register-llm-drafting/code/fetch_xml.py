"""Download full-text XML for every document in data/meta/fr_meta.parquet. Documents published from 2026-01-01 onward
(the announcement month and the outcome window) go to data/sealed/xml/ and are NOT parsed until the plan and the
estimator validation are committed; only a SHA-256 manifest of them is written. Earlier documents go to data/raw/xml/."""
import hashlib
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
SEAL_FROM = "2026-01-01"


def fetch(row):
    dest = RUN / "data" / ("sealed" if row.publication_date >= SEAL_FROM else "raw") / "xml" / f"{row.document_number}.xml"
    if dest.exists() and dest.stat().st_size > 0:
        return row.document_number, "cached"
    if not isinstance(row.full_text_xml_url, str) or not row.full_text_xml_url:
        return row.document_number, "no_xml_url"
    for attempt in range(5):
        try:
            data = urllib.request.urlopen(row.full_text_xml_url, timeout=120).read()
            dest.write_bytes(data)
            return row.document_number, "ok"
        except Exception as e:  # noqa: BLE001
            err = str(e)[:80]
            time.sleep(3 * (attempt + 1))
    return row.document_number, "fail:" + err


def main():
    m = pd.read_parquet(RUN / "data" / "meta" / "fr_meta.parquet")
    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(fetch, m.itertuples()))
    st = pd.Series([s.split(":")[0] for _, s in res]).value_counts()
    print(st.to_dict())
    sealed = sorted((RUN / "data" / "sealed" / "xml").glob("*.xml"))
    h = hashlib.sha256()
    lines = []
    for f in sealed:
        d = hashlib.sha256(f.read_bytes()).hexdigest()
        lines.append(f"{d}  {f.name}")
        h.update(d.encode())
    (RUN / "data" / "SEALED_MANIFEST.sha256").write_text("\n".join(lines) + "\n")
    print("sealed files:", len(sealed), "| manifest digest:", h.hexdigest())


if __name__ == "__main__":
    main()
