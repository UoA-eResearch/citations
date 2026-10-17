"""Europe PMC search (plan section 2), run once and saved: every hit's core record (title, journal, year, abstract,
type, language). Cursor paging, 1 s apart. Writes data/raw/epmc/records.jsonl and data/raw/epmc/query.json."""
import json
import time
from pathlib import Path

import requests

RUN = Path(__file__).resolve().parents[1]
Q = ('("FAERS" OR "FDA Adverse Event Reporting System") AND (disproportionality OR "reporting odds ratio" OR '
     '"proportional reporting ratio") AND PUB_YEAR:[2023 TO 2025]')
S = requests.Session(); S.headers["User-Agent"] = "research-lab pharmacovigilance study (mailto:noreply@anthropic.com)"


def main():
    out = RUN / "data" / "raw" / "epmc"; out.mkdir(parents=True, exist_ok=True)
    cursor, n, total = "*", 0, None
    with open(out / "records.jsonl", "w") as fh:
        while True:
            r = S.get("https://www.ebi.ac.uk/europepmc/webservices/rest/search",
                      params=dict(query=Q, format="json", resultType="core", pageSize=1000, cursorMark=cursor), timeout=180)
            r.raise_for_status(); j = r.json(); total = j["hitCount"]
            for x in j["resultList"]["result"]:
                fh.write(json.dumps(x) + "\n"); n += 1
            nxt = j.get("nextCursorMark")
            if not nxt or nxt == cursor or not j["resultList"]["result"]:
                break
            cursor = nxt; time.sleep(1)
    json.dump(dict(query=Q, hitCount=total, saved=n, date=time.strftime("%Y-%m-%d")), open(out / "query.json", "w"), indent=1)
    print(n, "of", total, "saved")


if __name__ == "__main__":
    main()
