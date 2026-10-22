"""Retracted DOIs and their retraction dates (plan section 2), from the registry layers fetched on 2026-10-21 for the
trust-corrected-record-machine-readable study (copied unchanged).

  Retraction Watch  RetractionNature == "Retraction"; reinstated originals removed; RetractionDate
  Crossref          update-to targets of type "retraction"; the notice's update date (an issue date for self-updates)

Writes data/labels.parquet (doi, date, rw, crossref, self_update) and results/tables/labels_log.json.
"""
import json
import re
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
SRC = Path("/mnt/data/retraction-markers/raw")


def ndoi(x):
    if not isinstance(x, str):
        return None
    x = x.strip().lower()
    x = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", x)
    return x if x.startswith("10.") else None


def main():
    rec, log = {}, {}
    rw = pd.read_csv(SRC / "retraction_watch.csv", dtype=str, encoding="utf-8", encoding_errors="replace")
    rw["date"] = pd.to_datetime(rw.RetractionDate, format="%m/%d/%Y %H:%M", errors="coerce")
    reinst = {ndoi(d) for d in rw[rw.RetractionNature == "Reinstatement"].OriginalPaperDOI if ndoi(d)}
    rr = rw[rw.RetractionNature == "Retraction"]
    log["rw_retraction_rows"] = len(rr)
    for d, dt in zip(rr.OriginalPaperDOI, rr.date):
        k = ndoi(d)
        if not k or k in reinst:
            continue
        x = rec.setdefault(k, {"rw": False, "crossref": False, "rw_date": pd.NaT, "cr_date": pd.NaT, "self_update": False})
        x["rw"] = True
        if pd.notna(dt) and (pd.isna(x["rw_date"]) or dt < x["rw_date"]):
            x["rw_date"] = dt
    for line in open(SRC / "crossref_notices.jsonl"):
        it = json.loads(line)
        own = ndoi(it.get("DOI"))
        for u in it.get("update-to") or []:
            if (u.get("type") or "").lower() != "retraction":
                continue
            k = ndoi(u.get("DOI"))
            if not k or k in reinst:
                continue
            dp = ((u.get("updated") or {}).get("date-parts") or [[None]])[0]
            dt = pd.Timestamp(year=dp[0], month=(dp[1] if len(dp) > 1 and dp[1] else 1),
                              day=(dp[2] if len(dp) > 2 and dp[2] else 1)) if dp and dp[0] else pd.NaT
            x = rec.setdefault(k, {"rw": False, "crossref": False, "rw_date": pd.NaT, "cr_date": pd.NaT, "self_update": False})
            x["crossref"] = True
            x["self_update"] = x["self_update"] or (k == own)
            if pd.notna(dt) and (pd.isna(x["cr_date"]) or dt < x["cr_date"]):
                x["cr_date"] = dt
    d = pd.DataFrame([{"doi": k, **v} for k, v in rec.items()])
    d["date"] = d.rw_date.fillna(d.cr_date)
    log.update({"retracted_dois": len(d), "rw": int(d.rw.sum()), "crossref": int(d.crossref.sum()),
                "both": int((d.rw & d.crossref).sum()), "undated": int(d.date.isna().sum()),
                "self_update": int(d.self_update.sum()), "reinstated_removed": len(reinst)})
    d[["doi", "date", "rw", "crossref", "self_update"]].to_parquet(RUN / "data" / "labels.parquet", index=False)
    json.dump(log, open(RUN / "results" / "tables" / "labels_log.json", "w"), indent=1)
    print(json.dumps(log, indent=1))


if __name__ == "__main__":
    main()
