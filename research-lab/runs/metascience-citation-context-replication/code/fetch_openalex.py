#!/usr/bin/env python
"""Baseline covariates from OpenAlex (open API, no key): for each FLoRA original, the venue (primary source), its
two-year mean citedness, the primary topic's field and domain, and the publication year.
Output: data/processed/openalex_originals.parquet
"""
import sys
import time
from pathlib import Path

import pandas as pd
import requests

RUN = Path(__file__).resolve().parents[1]


def get(url, params):
    for attempt in range(6):
        try:
            r = requests.get(url, params=params, timeout=60)
            if r.status_code == 200:
                return r.json()
        except requests.RequestException:
            pass
        time.sleep(2 * (attempt + 1))
    return None


def main():
    f = pd.read_csv(RUN / "data" / "raw" / "flora_filtered.csv", low_memory=False)
    dois = sorted(f[(f.type == "replication") & f.doi_o.notna()].doi_o.str.strip().str.lower().unique())
    rows = []
    for i in range(0, len(dois), 50):
        chunk = dois[i:i + 50]
        js = get("https://api.openalex.org/works", {"filter": "doi:" + "|".join(chunk), "per-page": 50,
                                                    "select": "doi,publication_year,primary_location,primary_topic,cited_by_count"})
        for w in (js or {}).get("results", []):
            src = ((w.get("primary_location") or {}).get("source") or {})
            topic = w.get("primary_topic") or {}
            rows.append(dict(doi_o=(w.get("doi") or "").replace("https://doi.org/", "").lower(), oa_year=w.get("publication_year"),
                             source_id=src.get("id"), source_name=src.get("display_name"),
                             field=(topic.get("field") or {}).get("display_name"), domain=(topic.get("domain") or {}).get("display_name"),
                             oa_cited_by=w.get("cited_by_count")))
        time.sleep(0.2)
    w = pd.DataFrame(rows).drop_duplicates("doi_o")
    srcs = sorted(w.source_id.dropna().unique())
    cit = {}
    for i in range(0, len(srcs), 50):
        chunk = [s.split("/")[-1] for s in srcs[i:i + 50]]
        js = get("https://api.openalex.org/sources", {"filter": "openalex:" + "|".join(chunk), "per-page": 50,
                                                      "select": "id,summary_stats"})
        for s in (js or {}).get("results", []):
            cit[s["id"]] = (s.get("summary_stats") or {}).get("2yr_mean_citedness")
        time.sleep(0.2)
    w["venue_citedness"] = w.source_id.map(cit)
    w.to_parquet(RUN / "data" / "processed" / "openalex_originals.parquet", index=False)
    print(len(dois), "originals;", len(w), "found in OpenAlex;", w.venue_citedness.notna().sum(), "with venue citedness")
    print(w.field.value_counts().head(8).to_dict())


if __name__ == "__main__":
    sys.exit(main())
