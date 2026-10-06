"""Fetch Federal Register metadata for all RULE and PRORULE documents, 2019-01 to 2026-09, month by month (the API
caps results per query). Writes data/meta/fr_meta.parquet. No full text is read here."""
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
API = "https://www.federalregister.gov/api/v1/documents.json"
FIELDS = ["document_number", "type", "publication_date", "agencies", "title", "abstract", "action", "cfr_references",
          "significant", "page_length", "full_text_xml_url", "regulation_id_numbers", "docket_ids", "html_url"]


def month_ranges():
    for y in range(2019, 2027):
        for m in range(1, 13):
            if (y, m) > (2026, 9):
                return
            start = f"{y}-{m:02d}-01"
            end = (pd.Timestamp(start) + pd.offsets.MonthEnd(0)).strftime("%Y-%m-%d")
            yield start, end


def get(params):
    q = urllib.parse.urlencode(params, doseq=True)
    for attempt in range(5):
        try:
            return json.load(urllib.request.urlopen(f"{API}?{q}", timeout=120))
        except Exception:  # noqa: BLE001
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(q)


def main():
    rows = []
    for start, end in month_ranges():
        page = 1
        while True:
            params = {"conditions[type][]": ["RULE", "PRORULE"], "conditions[publication_date][gte]": start,
                      "conditions[publication_date][lte]": end, "per_page": 1000, "page": page, "fields[]": FIELDS, "order": "oldest"}
            d = get(params)
            res = d.get("results", [])
            rows.extend(res)
            if page >= d.get("total_pages", 1) or not res:
                break
            page += 1
        print(start, d.get("count"), len(rows), flush=True)
        time.sleep(0.5)
    df = pd.DataFrame(rows)
    df["agencies"] = df.agencies.map(json.dumps)
    df["cfr_references"] = df.cfr_references.map(json.dumps)
    df["regulation_id_numbers"] = df.regulation_id_numbers.map(json.dumps)
    df["docket_ids"] = df.docket_ids.map(json.dumps)
    df.to_parquet(RUN / "data" / "meta" / "fr_meta.parquet")
    print(len(df), "documents", df.type.value_counts().to_dict())


if __name__ == "__main__":
    main()
