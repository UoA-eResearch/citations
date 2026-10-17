"""Resolve every distinct Local Contexts URI found in the census (plan section 2): HTTP status after redirects.
Writes data/uri_status.json {uri: status}."""
import json
import sys
import time
from pathlib import Path

import requests

RUN = Path(__file__).resolve().parents[1]
S = requests.Session(); S.headers["User-Agent"] = "research-lab metadata study (mailto:noreply@anthropic.com)"


def main():
    rows = [json.loads(l) for l in open(RUN / "data" / "census.jsonl")]
    uris = set()
    for r in rows:
        uris |= {f"https://localcontexts.org/label/{x}/" for x in r["uri_labels"]}
        uris |= {f"https://localcontexts.org/notice/{x}/" for x in r["uri_notices"]}
        uris |= {f"https://localcontextshub.org/projects/{x}/" for x in r["hub_projects"]}
    out = {}
    for u in sorted(uris):
        try:
            out[u] = S.get(u, timeout=60, allow_redirects=True).status_code
        except Exception:
            out[u] = None
        time.sleep(0.5)
    json.dump(out, open(RUN / "data" / "uri_status.json", "w"), indent=1)
    print(len(out), "URIs;", sum(v == 200 for v in out.values()), "live")


if __name__ == "__main__":
    sys.exit(main())
