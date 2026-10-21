"""Join the four registry layers to PMC and to the snapshot (plan section 1). Writes data/cohort.parquet (one row per
PMCID in the union registry) and results/tables/match_log.json.

Strata: primary (dated, retracted on or before 2026-04-24), recent (2026-04-25 to 2026-10-21), after_snapshot
(dated after S; excluded), undated (PubMed-only or OpenAlex-only). Notices are excluded here by identifier; by XML
article-type later, when the files are parsed.
"""
import gzip
import json
import re
from collections import defaultdict
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
S, CUT = pd.Timestamp("2026-10-21"), pd.Timestamp("2026-04-24")


def ndoi(x):
    if not isinstance(x, str):
        return None
    x = x.strip().lower()
    x = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", x)
    return x if x.startswith("10.") else None


def npmid(x):
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    x = str(x).strip().rsplit("/", 1)[-1]
    x = x.split(".")[0]
    return x if x.isdigit() and x != "0" else None


def main():
    ids = pd.read_csv(RAW / "PMC-ids.csv.gz", dtype=str, usecols=["DOI", "PMCID", "PMID"])
    doi2pmc = {ndoi(d): p for d, p in zip(ids.DOI, ids.PMCID) if ndoi(d)}
    pmid2pmc = {npmid(m): p for m, p in zip(ids.PMID, ids.PMCID) if npmid(m)}

    def pmc(doi=None, pmid=None):
        return pmid2pmc.get(npmid(pmid)) or doi2pmc.get(ndoi(doi))

    rec = defaultdict(lambda: {"rw": False, "crossref": False, "pubmed": False, "openalex": False, "rw_date": None,
                               "cr_date": None, "publisher": None, "journal": None, "doi": None, "pmid": None})
    notices = set()
    log = {}
    # Retraction Watch
    rw = pd.read_csv(RAW / "retraction_watch.csv", dtype=str, encoding="utf-8", encoding_errors="replace")
    rw["date"] = pd.to_datetime(rw.RetractionDate, format="%m/%d/%Y %H:%M", errors="coerce")
    reinst = set()
    for r in rw[rw.RetractionNature == "Reinstatement"].itertuples():
        reinst |= {k for k in (ndoi(r.OriginalPaperDOI), npmid(r.OriginalPaperPubMedID)) if k}
    for r in rw[rw.RetractionNature.isin(["Retraction", "Expression of concern", "Correction", "Reinstatement"])].itertuples():
        # D1: a notice identifier equal to the original's is a self-reference, not a separate notice
        nd = ndoi(r.RetractionDOI) if ndoi(r.RetractionDOI) != ndoi(r.OriginalPaperDOI) else None
        nm = npmid(r.RetractionPubMedID) if npmid(r.RetractionPubMedID) != npmid(r.OriginalPaperPubMedID) else None
        p = pmc(nd, nm)
        if p:
            notices.add(p)
    rr = rw[rw.RetractionNature == "Retraction"]
    log["rw_retractions"], n_map = len(rr), 0
    for r in rr.itertuples():
        if ndoi(r.OriginalPaperDOI) in reinst or npmid(r.OriginalPaperPubMedID) in reinst:
            continue
        p = pmc(r.OriginalPaperDOI, r.OriginalPaperPubMedID)
        if not p:
            continue
        n_map += 1
        x = rec[p]
        x["rw"] = True
        if pd.notna(r.date) and (x["rw_date"] is None or r.date < x["rw_date"]):
            x["rw_date"] = r.date
        x["publisher"], x["journal"] = x["publisher"] or r.Publisher, x["journal"] or r.Journal
        x["doi"], x["pmid"] = x["doi"] or ndoi(r.OriginalPaperDOI), x["pmid"] or npmid(r.OriginalPaperPubMedID)
    log["rw_mapped_to_pmc"], log["rw_reinstated_ids"] = n_map, len(reinst)
    # Crossref
    n_cr, n_map = 0, 0
    for line in open(RAW / "crossref_notices.jsonl"):
        it = json.loads(line)
        own = ndoi(it.get("DOI"))
        # D1: a work whose retraction assertion points at itself is a retracted original, not a notice
        if any(ndoi(u.get("DOI")) != own for u in it.get("update-to") or [] if (u.get("type") or "").lower() == "retraction"):
            p = pmc(own)
            if p:
                notices.add(p)
        for u in it.get("update-to") or []:
            if (u.get("type") or "").lower() != "retraction":
                continue
            n_cr += 1
            p = pmc(u.get("DOI"))
            if not p:
                continue
            n_map += 1
            dp = ((u.get("updated") or {}).get("date-parts") or [[None]])[0]
            dt = pd.Timestamp(year=dp[0], month=(dp[1] if len(dp) > 1 else 1), day=(dp[2] if len(dp) > 2 else 1)) \
                if dp and dp[0] else None
            x = rec[p]
            x["crossref"] = True
            if dt is not None and (x["cr_date"] is None or dt < x["cr_date"]):
                x["cr_date"] = dt
            x["doi"] = x["doi"] or ndoi(u.get("DOI"))
    log["crossref_targets"], log["crossref_mapped_to_pmc"] = n_cr, n_map
    # PubMed
    pm = [l.strip() for l in open(RAW / "pubmed_retracted.txt") if l.strip()]
    n_map = 0
    for m in pm:
        p = pmc(pmid=m)
        if p:
            n_map += 1
            rec[p]["pubmed"] = True
            rec[p]["pmid"] = rec[p]["pmid"] or m
    log["pubmed_ids"], log["pubmed_mapped_to_pmc"] = len(pm), n_map
    # OpenAlex
    n_oa, n_map = 0, 0
    for line in open(RAW / "openalex_retracted.jsonl"):
        it = json.loads(line)
        n_oa += 1
        p = (it.get("pmcid") or "").rsplit("/", 1)[-1] or None
        p = p if p and p.startswith("PMC") else pmc(it.get("doi"), it.get("pmid"))
        if p:
            n_map += 1
            rec[p]["openalex"] = True
            rec[p]["doi"] = rec[p]["doi"] or ndoi(it.get("doi"))
    log["openalex_works"], log["openalex_mapped_to_pmc"] = n_oa, n_map
    d = pd.DataFrame([{"pmcid": k, **v} for k, v in rec.items()])
    d["date"] = d.rw_date.fillna(d.cr_date)
    d["notice_id"] = d.pmcid.isin(notices)
    # D1: a document a curated layer lists as the retracted original is not excluded by identifier; true notices
    # among them are caught by the XML article-type check at parse time
    d["notice"] = d.notice_id & ~(d.rw | d.pubmed | d.crossref)
    snap = pd.read_parquet(RUN / "data" / "snapshot" / "latest_versions.parquet")
    d = d.merge(snap[["pmcid", "version", "key"]], on="pmcid", how="left")
    d["in_snapshot"] = d.key.notna()
    d["stratum"] = "undated"
    d.loc[d.date.notna() & (d.date <= CUT), "stratum"] = "primary"
    d.loc[d.date.notna() & (d.date > CUT) & (d.date <= S), "stratum"] = "recent"
    d.loc[d.date.notna() & (d.date > S), "stratum"] = "after_snapshot"
    d.to_parquet(RUN / "data" / "cohort.parquet", index=False)
    log["union_pmcids"] = len(d)
    log["notices_excluded_by_id"] = int(d.notice.sum())
    log["notice_id_but_curated_original"] = int((d.notice_id & ~d.notice).sum())
    log["in_snapshot_by_stratum"] = d[d.in_snapshot & ~d.notice].stratum.value_counts().to_dict()
    log["not_in_snapshot_by_stratum"] = d[~d.in_snapshot & ~d.notice].stratum.value_counts().to_dict()
    json.dump(log, open(RUN / "results" / "tables" / "match_log.json", "w"), indent=1, default=str)
    print(json.dumps(log, indent=1, default=str))


if __name__ == "__main__":
    main()
