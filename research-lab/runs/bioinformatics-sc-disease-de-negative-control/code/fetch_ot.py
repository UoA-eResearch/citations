"""Open Targets Platform direct overall association scores for every single-ID disease in the primary contrasts
(plan section 1; enrichment secondary). GraphQL API, release recorded.
  fetch_ot.py -> data/meta/ot_assoc.parquet (disease_id, target ensembl id, score), data/meta/ot_release.json
"""
import json
import time
from pathlib import Path

import pandas as pd
import requests

RUN = Path(__file__).resolve().parents[1]
META = RUN / "data" / "meta"
API = "https://api.platform.opentargets.org/api/v4/graphql"
Q = """query($id: String!, $i: Int!) { disease(efoId: $id) { id name
  associatedTargets(enableIndirect: false, page: {index: $i, size: 1000}) { count rows { target { id } score } } } }"""


def main():
    o = pd.read_parquet(META / "obs_counts.parquet")
    prim = pd.read_csv(META / "contrasts_primary.csv")
    ids = o[o.disease.isin(prim.disease)].groupby("disease").disease_ontology_term_id.first()
    ids = ids[~ids.str.contains(r"\|\|")]
    meta = requests.post(API, json={"query": "{ meta { dataVersion { year month } apiVersion { x y z } } }"}, timeout=60).json()
    rows, status = [], {}
    for dis, term in ids.items():
        efo = term.replace(":", "_")
        i, n = 0, None
        while n is None or i * 1000 < n:
            r = requests.post(API, json={"query": Q, "variables": {"id": efo, "i": i}}, timeout=120).json()
            d = (r.get("data") or {}).get("disease")
            if d is None:
                status[dis] = f"not found: {efo}"; break
            at = d["associatedTargets"]; n = at["count"]
            rows += [(efo, dis, x["target"]["id"], x["score"]) for x in at["rows"]]
            i += 1; time.sleep(0.2)
        status.setdefault(dis, f"ok {n}")
    pd.DataFrame(rows, columns=["disease_id", "disease", "ensembl_id", "score"]).to_parquet(META / "ot_assoc.parquet")
    (META / "ot_release.json").write_text(json.dumps({"meta": meta, "status": status}, indent=1))
    print(json.dumps({"meta": meta, "status": status}, indent=1))


if __name__ == "__main__":
    main()
