"""D5: the peS2o arm re-scored and its secondary analyses, from the stored matches (data/pes2o/matched.jsonl).

Rules, applied to each matched document's text:
- v1, the study rule as drafted: markers.txt_markers (kept for the record);
- v2, the D5 primary: v1, OR "notice of retraction" anywhere with no closing word boundary (peS2o runs IEEE's
  "Notice of Retraction" into the title), OR a first line beginning Retracted / Retraction / Withdrawn followed by a
  separator or a capital letter;
- broad, a sensitivity: v2, OR "retract" anywhere in the first 200 characters of the first line.

Secondary analyses:
- marked shares overall and by source (s2ag = title and abstract; s2orc = full text);
- by retraction year;
- staleness: Semantic Scholar's 'added' date against the retraction date, within retraction years >= 2015 only (most
  documents were added in the 2017-18 bulk ingest, which confounds the split with retraction year);
- the downstream test: documents also in the PMC snapshot, not notices, with PMC's own-marker rate (D3) beside
  peS2o's.

Writes results/tables/pes2o_secondary.json and results/tables/pes2o_documents_d5.csv.
"""
import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import markers  # noqa: E402
import pes2o  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
NOTICE = re.compile(r"notice\s*of\s*retraction", re.I)
TITLE_RUNON_CASE = re.compile(r"^\W*(?:retracted|retraction|withdrawn)", re.I)
RETRACT = re.compile(r"retract", re.I)


def title_runon(first):
    m = TITLE_RUNON_CASE.match(first)
    if not m:
        return False
    rest = first[m.end():]
    return rest == "" or rest[0] in " \t:.,;-–—([" or rest[0].isupper()


def share(s):
    return round(float(s.mean()), 4) if len(s) else None


def main():
    rows = []
    with open(RUN / "data" / "pes2o" / "matched.jsonl") as fh:
        for line in fh:
            j = json.loads(line)
            t = j["text"]
            first = t.split("\n", 1)[0]
            v1 = markers.txt_markers(t)["textual"]
            v2 = v1 or bool(NOTICE.search(t)) or title_runon(first)
            rows.append({"id": j["id"], "source": j["source"].split("/")[0], "added": j["added"][:10], "v1": v1, "v2": v2,
                         "broad": v2 or bool(RETRACT.search(first[:200]))})
    d = pd.DataFrame(rows)
    ids = json.load(open(RUN / "data" / "pes2o" / "corpus_ids.json"))
    want = {str(v): k for k, v in ids.items() if v}
    d["doi"] = d.id.map(want)
    reg = pes2o.registry()
    d["rdate"] = d.doi.map(reg)
    d["ryear"] = d.rdate.dt.year
    d["after"] = pd.to_datetime(d.added) > d.rdate
    out = {"matched_documents": int(len(d)),
           "marked_share": {"v1_as_drafted": share(d.v1), "v2_D5": share(d.v2), "broad": share(d.broad)},
           "by_source": {s: {"n": int(len(g)), "v1": share(g.v1), "v2": share(g.v2), "broad": share(g.broad)}
                         for s, g in d.groupby("source")},
           "notice_of_retraction_runon_docs": int((~d.v1 & d.v2).sum()),
           "by_retraction_year": {int(y): {"n": int(len(g)), "v2": share(g.v2), "share_added_after": share(g.after)}
                                  for y, g in d.groupby("ryear")},
           "staleness_ryear_ge_2015": {("added_after" if k else "added_before"): {"n": int(len(g)), "v2": share(g.v2)}
                                       for k, g in d[d.ryear >= 2015].groupby("after")}}
    # downstream: also in the PMC snapshot, not a notice
    c = pd.read_parquet(RUN / "data" / "cohort.parquet")
    ov = pd.read_csv(RUN / "results" / "overlay" / "retraction_overlay.csv.gz", usecols=["pmcid", "own_marker", "sidecar_flag"])
    c = c.merge(ov, on="pmcid", how="left")
    c["doi_n"] = c.doi.map(pes2o.ndoi)
    c = c.dropna(subset=["doi_n"]).drop_duplicates("doi_n")
    m = d.merge(c[["doi_n", "in_snapshot", "notice", "stratum", "own_marker"]], left_on="doi", right_on="doi_n", how="left")
    inpmc = m[m.in_snapshot.fillna(False).astype(bool) & ~m.notice.fillna(False).astype(bool)]
    notpmc = m[m.doi_n.isna()]
    out["downstream_pmc_overlap"] = {
        "n": int(len(inpmc)), "pmc_own_marker_share": share(inpmc.own_marker.fillna(False).astype(bool)),
        "pes2o_v2_marked_share": share(inpmc.v2), "pes2o_v1_marked_share": share(inpmc.v1),
        "by_source": {s: {"n": int(len(g)), "v2": share(g.v2)} for s, g in inpmc.groupby("source")}}
    out["not_in_pmc_registry"] = {"n": int(len(notpmc)), "v2": share(notpmc.v2)}
    d.drop(columns=["rdate"]).to_csv(TAB / "pes2o_documents_d5.csv", index=False)
    json.dump(out, open(TAB / "pes2o_secondary.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "by_retraction_year"}, indent=1))


if __name__ == "__main__":
    main()
