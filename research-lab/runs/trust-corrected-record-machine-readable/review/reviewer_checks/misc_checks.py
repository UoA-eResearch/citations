"""Reviewer check: version consistency (inventory / sidecar / xml_url / XML pmcid-ver) on all fetched documents, the
D3 structured share, the one document last-modified before its retraction date, peS2o id uniqueness, and a recount
of the D1 self-reference figures from the raw registry files. Output in misc_checks.log.
Run: venv/bin/python -I misc_checks.py
"""
import json
import re
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
RUN = HERE.parents[1]


def main():
    c = pd.read_parquet(RUN / "data/cohort.parquet")
    c = c[c.in_snapshot & ~c.notice & c.stratum.isin(["primary", "recent", "undated"])]
    x = pd.read_parquet(HERE / "xml_pass.parquet")[["pmcid", "pmcid_ver"]]
    rows = []
    for p, k, v in zip(c.pmcid, c.key, c.version):
        m = json.loads((RUN / "data/files" / f"{p}.json").read_bytes())
        xu = m.get("xml_url", "")
        rows.append((p, int(v), m.get("version"), re.search(r"\.(\d+)\.xml", xu).group(1) if xu else None,
                     m.get("is_pmc_openaccess"), m.get("is_manuscript")))
    d = pd.DataFrame(rows, columns=["pmcid", "inv_v", "json_v", "xmlurl_v", "oa", "ms"]).merge(x, on="pmcid")
    d["xml_v"] = d.pmcid_ver.str.extract(r"\.(\d+)$")[0]
    print("inventory version == sidecar version:", int((d.inv_v == d.json_v).sum()), "of", len(d))
    print("inventory version == xml_url version:", int((d.inv_v.astype(str) == d.xmlurl_v).sum()))
    print("inventory version == XML pmcid-ver:", int((d.inv_v.astype(str) == d.xml_v).sum()), "; mismatches sample:",
          d[d.inv_v.astype(str) != d.xml_v][["pmcid", "inv_v", "json_v", "xml_v"]].head(5).to_dict("records"))
    print("version 319 sidecars:", d[d.inv_v == 319][["pmcid", "json_v", "xmlurl_v", "xml_v"]].to_dict("records"))
    print("is_pmc_openaccess False:", int((d.oa == False).sum()), "; manuscripts:", int((d.ms == True).sum()))  # noqa: E712
    d3 = pd.read_csv(RUN / "results/tables/documents_d3.csv.gz")
    print("D3 own_structured share (primary):", round(d3.own_structured.mean(), 4), "own_textual:", round(d3.own_textual.mean(), 4))
    snap = pd.read_parquet(RUN / "data/snapshot/latest_versions.parquet")
    P = c[c.stratum == "primary"].merge(snap[["pmcid", "last_modified"]], on="pmcid")
    P["lm"] = pd.to_datetime(P.last_modified, utc=True).dt.tz_localize(None)
    print("last_modified BEFORE retraction date:", P[P.lm <= P.date][["pmcid", "doi", "date", "lm"]].to_dict("records"))
    pe = pd.read_csv(RUN / "results/tables/pes2o_documents.csv")
    print("peS2o ids unique:", pe.id.is_unique, "dois unique:", pe.doi.is_unique, len(pe))
    rw = pd.read_csv(RUN / "data/raw/retraction_watch.csv", dtype=str, encoding="utf-8", encoding_errors="replace")
    nd = lambda s: s.astype(str).str.strip().str.lower()  # noqa: E731
    print("RW rows notice DOI == original DOI:",
          int((nd(rw.RetractionDOI) == nd(rw.OriginalPaperDOI))[rw.RetractionDOI.notna() & rw.OriginalPaperDOI.notna()].sum()),
          "; notice PMID == original PMID:", int((nd(rw.RetractionPubMedID) == nd(rw.OriginalPaperPubMedID))[rw.RetractionPubMedID.notna()].sum()),
          "of", len(rw))
    n_self = n_all = 0
    for line in open(RUN / "data/raw/crossref_notices.jsonl"):
        it = json.loads(line)
        own = (it.get("DOI") or "").lower()
        for u in it.get("update-to") or []:
            if (u.get("type") or "").lower() == "retraction":
                n_all += 1
                n_self += (u.get("DOI") or "").lower() == own
    print("Crossref retraction assertions:", n_all, "self-pointing:", n_self)


if __name__ == "__main__":
    main()
