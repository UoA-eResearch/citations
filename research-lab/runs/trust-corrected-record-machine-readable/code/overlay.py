"""Secondary 9: the overlay. One row per PMC document in the union registry (notices excluded), with its layers,
retraction date and the date's source, whether it is in the 2026-10-21 snapshot, and what the snapshot's own files
say (XML marker outside reference lists, withdrawal wording, sidecar flag, text header). Rebuild: registry.py ->
match.py -> fetch.py -> analysis.py parse -> sensitivity_d3.py -> overlay.py.
Writes results/overlay/retraction_overlay.csv.gz and results/tables/overlay.json.
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402
from match import ndoi  # noqa: E402

RUN = A.RUN


def main():
    selfdoi = set()
    for line in open(RUN / "data" / "raw" / "crossref_notices.jsonl"):
        it = json.loads(line)
        own = ndoi(it.get("DOI"))
        for u in it.get("update-to") or []:
            if (u.get("type") or "").lower() == "retraction" and ndoi(u.get("DOI")) == own:
                selfdoi.add(own)
    c = pd.read_parquet(RUN / "data" / "cohort.parquet")
    c = c[~c.notice]
    p = pd.read_parquet(RUN / "data" / "parsed.parquet")[["pmcid", "article_type", "sidecar_flag", "xml_structured", "xml_textual"]]
    s = pd.read_csv(A.TAB / "documents_d3.csv.gz")
    d = c.merge(p, on="pmcid", how="left").merge(s, on="pmcid", how="left")
    d = d[d.article_type.fillna("").str.lower() != "retraction"]
    d["date_source"] = "none"
    d.loc[d.cr_date.notna(), "date_source"] = "crossref"
    d.loc[d.cr_date.notna() & d.doi.isin(selfdoi) & d.rw_date.isna(), "date_source"] = "crossref-self-update (issue date)"
    d.loc[d.rw_date.notna(), "date_source"] = "retraction-watch"
    todo = [x for x in d[d.in_snapshot & d.own_structured.isna()].pmcid      # recent and undated strata
            if (A.FILES / f"{x}.xml").exists() and (A.FILES / f"{x}.txt").exists()]
    if todo:
        import concurrent.futures as cf
        import sensitivity_d3 as S
        with cf.ProcessPoolExecutor(12) as ex:
            extra = pd.DataFrame(list(ex.map(S.one, todo, chunksize=50))).set_index("pmcid")
        for col in ("own_structured", "own_textual", "withdrawal", "txt_header"):
            d.loc[d.pmcid.isin(extra.index), col] = d.loc[d.pmcid.isin(extra.index), "pmcid"].map(extra[col])
    for col in ("own_structured", "own_textual", "withdrawal", "txt_header", "sidecar_flag"):
        d[col] = d[col].astype("boolean")
    d["own_marker"] = (d.own_structured.fillna(False) | d.own_textual.fillna(False) | d.withdrawal.fillna(False)).astype(bool)
    keep = ["pmcid", "pmid", "doi", "rw", "crossref", "pubmed", "openalex", "date", "date_source", "stratum", "in_snapshot",
            "version", "own_marker", "sidecar_flag", "txt_header"]
    out = d[keep].sort_values("pmcid")
    (RUN / "results" / "overlay").mkdir(parents=True, exist_ok=True)
    out.to_csv(RUN / "results" / "overlay" / "retraction_overlay.csv.gz", index=False)
    snap = out[out.in_snapshot]
    prim = snap[snap.stratum == "primary"]
    gap = lambda g: int((~g.own_marker & ~g.sidecar_flag.fillna(False).astype(bool)).sum())
    res = {"rows": len(out), "in_snapshot": len(snap), "snapshot_docs_without_own_marker_or_flag": gap(snap),
           "primary_without_own_marker_or_flag": gap(prim),
           "by_stratum": {k: {"n": len(g), "without_marker_or_flag": gap(g)} for k, g in snap.groupby("stratum")}}
    json.dump(res, open(A.TAB / "overlay.json", "w"), indent=1)
    print(res)


if __name__ == "__main__":
    main()
