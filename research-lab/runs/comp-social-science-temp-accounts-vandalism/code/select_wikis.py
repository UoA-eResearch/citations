#!/usr/bin/env python
"""Sample selection (plan.md sec 2): the 40 Wikipedias with the most anonymous content edits in 2024, from the Wikimedia
Analytics edits API, among wikis present in the 2026-08 mediawiki_history dumps.
Output: results/tables/wikis.csv
"""
import sys
import time
from pathlib import Path

import pandas as pd
import requests

RUN = Path(__file__).resolve().parents[1]
UA = {"User-Agent": "research-lab temporary-accounts study (University of Auckland eResearch)"}


def main():
    sm = requests.get("https://meta.wikimedia.org/w/api.php", params={"action": "sitematrix", "format": "json", "smtype": "language"},
                      headers=UA, timeout=60).json()["sitematrix"]
    sites = []
    for k, v in sm.items():
        if not isinstance(v, dict):
            continue
        for s in v.get("site", []):
            if s.get("code") == "wiki" and "closed" not in s and "private" not in s:
                sites.append(dict(dbname=s["dbname"], project=s["url"].replace("https://", "")))
    dumps = set(open(RUN / "data" / "raw" / "wiki_list.txt").read().split())
    rows = []
    for s in sites:
        if s["dbname"] not in dumps:
            continue
        proj = s["project"].replace(".org", "")
        url = f"https://wikimedia.org/api/rest_v1/metrics/edits/aggregate/{proj}/anonymous/content/monthly/20240101/20250101"
        n = None
        for attempt in range(6):                                         # the API throttles bursts: back off and retry
            try:
                r = requests.get(url, headers=UA, timeout=60)
                if r.status_code == 200:
                    n = sum(x["edits"] for x in r.json()["items"][0]["results"])
                    break
                if r.status_code == 404:
                    break
            except Exception:                                            # noqa: BLE001
                pass
            time.sleep(2 * (attempt + 1))
        rows.append(dict(**s, anon_content_edits_2024=n))
        time.sleep(0.3)
    d = pd.DataFrame(rows)
    for rnd in range(5):                                                 # second passes for throttled requests
        miss = d.anon_content_edits_2024.isna()
        if not miss.any():
            break
        print(f"pass {rnd + 2}: re-querying {int(miss.sum())} wikis", flush=True)
        for i in d.index[miss]:
            proj = d.at[i, "project"].replace(".org", "")
            url = f"https://wikimedia.org/api/rest_v1/metrics/edits/aggregate/{proj}/anonymous/content/monthly/20240101/20250101"
            try:
                r = requests.get(url, headers=UA, timeout=60)
                if r.status_code == 200:
                    d.at[i, "anon_content_edits_2024"] = sum(x["edits"] for x in r.json()["items"][0]["results"])
                elif r.status_code == 404:
                    d.at[i, "anon_content_edits_2024"] = 0
            except Exception:                                            # noqa: BLE001
                pass
            time.sleep(1.0)
    print("still missing after retries:", d[d.anon_content_edits_2024.isna()].dbname.tolist())
    d.to_csv(RUN / "results" / "tables" / "wikis_all.csv", index=False)
    d = d.dropna().sort_values("anon_content_edits_2024", ascending=False)
    d["rank"] = range(1, len(d) + 1)
    d.head(40).to_csv(RUN / "results" / "tables" / "wikis.csv", index=False)
    print(len(sites), "Wikipedias;", len(d), "with data; top 40:")
    print(d.head(40)[["rank", "dbname", "anon_content_edits_2024"]].to_string(index=False))


if __name__ == "__main__":
    sys.exit(main())
