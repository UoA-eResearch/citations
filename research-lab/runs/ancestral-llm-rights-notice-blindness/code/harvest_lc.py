"""Harvest every DataCite record whose rightsList carries a Local Contexts URI (public metadata, cursor-paged),
to profile the treatment arm before any sampling rule is fixed. Writes data/raw/datacite/lc_records.jsonl and
VINTAGE_lc.txt."""
import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
OUT = RUN / "data" / "raw" / "datacite"
Q = "rightsList.rightsUri:*localcontexts*"


def get(url, tries=6):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "research-lab (mailto:noreply@anthropic.com)"}), timeout=120) as r:
                return json.load(r)
        except Exception as e:
            time.sleep(2 ** i)
            err = e
    raise err


def main():
    url = "https://api.datacite.org/dois?" + urllib.parse.urlencode({"query": Q, "page[size]": 1000, "page[cursor]": 1})
    n = 0
    with open(OUT / "lc_records.jsonl", "w") as fh:
        while url:
            d = get(url)
            for r in d["data"]:
                fh.write(json.dumps(r) + "\n"); n += 1
            url = d.get("links", {}).get("next")
            print(n, flush=True)
            time.sleep(0.5)
    h = hashlib.sha256((OUT / "lc_records.jsonl").read_bytes()).hexdigest()
    (OUT / "VINTAGE_lc.txt").write_text(f"query {Q}\nrecords {n}\nsha256 {h}\nretrieved {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n")
    print("done", n)


if __name__ == "__main__":
    sys.exit(main())
