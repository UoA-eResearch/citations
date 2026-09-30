#!/usr/bin/env python
"""Flatten the harvested Semantic Scholar citations into one row per (original, citing paper, context).
Output: data/processed/contexts.parquet, data/processed/citing.parquet (one row per original x citing paper,
including citing papers without contexts), results/tables/harvest_summary.csv
"""
import json
import sys
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
PROC, TAB = RUN / "data" / "processed", RUN / "results" / "tables"


def main():
    ctx, cit, summ = [], [], []
    for f in sorted((RUN / "data" / "raw" / "s2").glob("*.json")):
        js = json.loads(f.read_text())
        summ.append(dict(doi_o=js["doi"], status=js["status"], n_citing=js["n"]))
        for row in js["data"]:
            cp = row.get("citingPaper") or {}
            pid = cp.get("paperId")
            if pid is None:
                continue
            contexts = row.get("contexts") or []
            doi_c = ((cp.get("externalIds") or {}).get("DOI") or "").strip().lower() or None
            cit.append(dict(doi_o=js["doi"], citing_id=pid, citing_doi=doi_c, year=cp.get("year"), pub_date=cp.get("publicationDate"),
                            n_contexts=len(contexts), influential=row.get("isInfluential"),
                            intents=";".join(sorted({i for i in (row.get("intents") or [])}))))
            for k, c in enumerate(contexts):
                ctx.append(dict(doi_o=js["doi"], citing_id=pid, citing_doi=doi_c, year=cp.get("year"), k=k, text=c))
    PROC.mkdir(parents=True, exist_ok=True)
    c = pd.DataFrame(ctx)
    c["ctx_id"] = pd.util.hash_pandas_object(c[["doi_o", "citing_id", "k"]], index=False).astype("uint64").astype(str)
    c.to_parquet(PROC / "contexts.parquet", index=False)
    pd.DataFrame(cit).drop_duplicates(["doi_o", "citing_id"]).to_parquet(PROC / "citing.parquet", index=False)
    s = pd.DataFrame(summ)
    TAB.mkdir(parents=True, exist_ok=True)
    s.to_csv(TAB / "harvest_summary.csv", index=False)
    print("originals", len(s), "status", s.status.value_counts().to_dict(), "| citing rows", len(cit),
          "| contexts", len(c), "| unique context texts", c.text.nunique())


if __name__ == "__main__":
    sys.exit(main())
