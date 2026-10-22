"""Reviewer check for the peS2o secondary: re-score the 17,416 matched documents with the study's rule and with
broadened rules (the study's STATEMENT regex needs a word boundary after 'retraction', which peS2o's run-together
titles such as 'Notice of RetractionThe Effects...' defeat); recompute the 'added' split and its confound with
retraction year; overlap with the PMC cohort. Prints everything.
Run: venv/bin/python -I pes2o_check.py
"""
import json
import re
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
RUN = HERE.parents[1]
sys.path.insert(0, str(RUN / "code"))
import markers  # noqa: E402
import pes2o  # noqa: E402

ANY = re.compile(r"retract", re.I)
NOTICE_LOOSE = re.compile(r"notice\s*of\s*retraction", re.I)
WD = re.compile(r"\bwithdrawn\b|\bwithdrawal\b", re.I)
FIRST_RETRACT = re.compile(r"retract", re.I)


def main():
    rows = []
    with open(RUN / "data" / "pes2o" / "matched.jsonl") as fh:
        for line in fh:
            j = json.loads(line)
            t = j["text"]
            first = t.split("\n", 1)[0]
            m = markers.txt_markers(t)
            rows.append({"id": j["id"], "source": j["source"], "added": j["added"][:10], "created": j["created"][:10],
                         "marked": m["textual"], "kinds": ";".join(m["kinds"]),
                         "first_retract": bool(FIRST_RETRACT.search(first[:200])),
                         "any_retract": bool(ANY.search(t)),
                         "notice_loose_first": bool(NOTICE_LOOSE.search(first[:200])),
                         "starts_notice": first[:25].lower().replace(" ", "").startswith("noticeofretraction"),
                         "wd_first": bool(WD.search(first[:200])),
                         "first120": first[:120], "nchar": len(t)})
    d = pd.DataFrame(rows)
    ids = json.load(open(RUN / "data" / "pes2o" / "corpus_ids.json"))
    want = {str(v): k for k, v in ids.items() if v}
    d["doi"] = d.id.map(want)
    print("matched", len(d), "; study rule marked:", round(d.marked.mean(), 4))
    print("'retract' anywhere in the FIRST LINE (title):", round(d.first_retract.mean(), 4), int(d.first_retract.sum()))
    print("'retract' anywhere in text:", round(d.any_retract.mean(), 4), int(d.any_retract.sum()))
    print("first line starts 'Notice of Retraction' (spaces ignored):", int(d.starts_notice.sum()),
          "; of these the study rule marked:", int(d[d.starts_notice].marked.sum()))
    print("'notice of retraction' loose in first line:", int(d.notice_loose_first.sum()))
    print("withdrawn/withdrawal in first line:", int(d.wd_first.sum()), "; of these marked by study rule:", int(d[d.wd_first].marked.sum()))
    d["broad"] = d.marked | d.first_retract | d.notice_loose_first
    print("study rule OR 'retract' in title line:", round(d.broad.mean(), 4), int(d.broad.sum()))
    print("by source, study rule vs broad:")
    print(d.groupby(d.source.str.split("/").str[0]).agg(n=("id", "size"), marked=("marked", "mean"), broad=("broad", "mean"),
                                                        any_retract=("any_retract", "mean")).round(4))
    print("\nexamples: first line of 12 docs unmarked by the study rule but with 'retract' in the title line:")
    for s in d[~d.marked & d.first_retract].first120.sample(12, random_state=3):
        print("   ", s)
    print("\nexamples: first line of 8 docs marked by the study rule:")
    for s in d[d.marked].first120.sample(8, random_state=3):
        print("   ", s)
    print("\nDOI prefix of docs unmarked by study rule but 'retract' in title:",
          d[~d.marked & d.first_retract].doi.str.split("/").str[0].value_counts().head(6).to_dict())
    # registry dates and the 'added' split
    reg = pes2o.registry()
    d["rdate"] = d.doi.map(reg)
    d["added_dt"] = pd.to_datetime(d.added)
    d["after"] = d.added_dt > d.rdate
    print("\n--- added vs retraction (study rule):")
    print(d.groupby("after").agg(n=("id", "size"), marked=("marked", "mean"), broad=("broad", "mean")).round(4))
    print("added year distribution:", d.added_dt.dt.year.value_counts().sort_index().to_dict())
    d["ryear"] = d.rdate.dt.year
    print("by retraction year (n, study rule, broad, share added-after):")
    print(d.groupby("ryear").agg(n=("id", "size"), marked=("marked", "mean"), broad=("broad", "mean"), after=("after", "mean")).round(3).to_string())
    print("\nwithin retraction year >= 2015 only: added after vs before (study rule, broad):")
    sub = d[d.ryear >= 2015]
    print(sub.groupby("after").agg(n=("id", "size"), marked=("marked", "mean"), broad=("broad", "mean")).round(4))
    # RW-only
    rw = pd.read_csv(RUN / "data" / "raw" / "retraction_watch.csv", dtype=str, encoding="utf-8", encoding_errors="replace")
    rwd = {pes2o.ndoi(x) for x in rw[rw.RetractionNature == "Retraction"].OriginalPaperDOI if pes2o.ndoi(x)}
    print("\nRW-dated only: n", int(d.doi.isin(rwd).sum()), "marked", round(d[d.doi.isin(rwd)].marked.mean(), 4))
    # overlap with PMC
    c = pd.read_parquet(RUN / "data" / "cohort.parquet")
    ov = pd.read_csv(RUN / "results" / "overlay" / "retraction_overlay.csv.gz")
    c = c.merge(ov[["pmcid", "own_marker", "sidecar_flag"]], on="pmcid", how="left")
    c["doi_n"] = c.doi.map(pes2o.ndoi)
    m = d.merge(c[["doi_n", "pmcid", "in_snapshot", "notice", "stratum", "own_marker", "sidecar_flag"]], left_on="doi", right_on="doi_n", how="left")
    print("\n--- overlap with PMC union registry (any stratum):", int(m.pmcid.notna().sum()), "of", len(d))
    inpmc = m[m.pmcid.notna() & m.in_snapshot.fillna(False) & ~m.notice.fillna(False)]
    print("in PMC snapshot and not a notice:", len(inpmc), "; peS2o marked (study rule):", round(inpmc.marked.mean(), 4),
          "broad:", round(inpmc.broad.mean(), 4), "; PMC own marker:", round(inpmc.own_marker.fillna(False).astype(bool).mean(), 4))
    print("by source among PMC overlap:", inpmc.groupby(inpmc.source.str.split("/").str[0]).agg(n=("id", "size"), marked=("marked", "mean"), broad=("broad", "mean")).round(4).to_dict("index"))
    notp = m[m.pmcid.isna()]
    print("NOT in PMC registry:", len(notp), "marked:", round(notp.marked.mean(), 4), "broad:", round(notp.broad.mean(), 4))
    # s2orc text format: does it begin with a title?
    print("\n--- s2orc first lines (6):")
    for s in d[d.source.str.startswith("s2orc")].first120.sample(6, random_state=5):
        print("   ", s)
    print("s2orc median chars", int(d[d.source.str.startswith("s2orc")].nchar.median()), "; s2ag median", int(d[d.source.str.startswith("s2ag")].nchar.median()))
    d.drop(columns=["first120"]).to_csv(HERE / "pes2o_rescored.csv", index=False)


if __name__ == "__main__":
    main()
