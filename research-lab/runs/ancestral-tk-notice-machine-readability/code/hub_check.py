"""D5 (review issue 23): what the Local Contexts Hub itself shows for every project linked from an element-bearing
record. Public project API (api/v1/projects/<id>/), one request at a time, 1 s apart. For care, only the creator's
account type is kept (institution / researcher / community), never a name. Writes results/tables/hub_projects.csv."""
import csv
import json
import time
from pathlib import Path

import requests

RUN = Path(__file__).resolve().parents[1]
S = requests.Session(); S.headers.update({"User-Agent": "research-lab metadata study (mailto:noreply@anthropic.com)", "Accept": "application/json"})


def main():
    ps = sorted({p for l in open(RUN / "data" / "census.jsonl") for p in json.loads(l)["hub_projects"]})
    rows = []
    for p in ps:
        try:
            r = S.get(f"https://localcontextshub.org/api/v1/projects/{p}/", timeout=60); st = r.status_code
            j = r.json() if st == 200 else {}
        except Exception as e:  # noqa: BLE001
            st, j = f"error: {str(e)[:60]}", {}
        types = sorted({k for c in (j.get("created_by") or []) for k in ("institution", "community", "researcher") if c.get(k)})
        rows.append(dict(project=p, status=st, privacy=j.get("project_privacy"), creator_type="+".join(types),
                         notices=";".join(sorted({str(n.get("notice_type") or n.get("name")) for n in (j.get("notice") or [])})),
                         bc_labels=len(j.get("bc_labels") or []), tk_labels=len(j.get("tk_labels") or [])))
        time.sleep(1)
    with open(RUN / "results" / "tables" / "hub_projects.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    live = [r for r in rows if r["status"] == 200]
    print(len(rows), "projects;", len(live), "live;", sum(1 for r in live if r["bc_labels"] or r["tk_labels"]), "with a Label at the Hub;",
          sum(1 for r in live if not (r["bc_labels"] or r["tk_labels"])), "Notices only")


if __name__ == "__main__":
    main()
