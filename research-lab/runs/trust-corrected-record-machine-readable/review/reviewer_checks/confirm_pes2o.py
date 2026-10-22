"""Confirmation pass (review/confirmation.md), peS2o arm: findings 1-3 of review/review.md.

1. Rerun the committed code/pes2o_secondary.py into a scratch directory and compare its two outputs with the
   committed results/tables/pes2o_documents_d5.csv and pes2o_secondary.json.
2. The D5 rule (v2) against the reviewer's re-score (pes2o_rescored.csv): decompose the documents only v2 marks
   (run-together notice vs run-together title prefix), what follows "notice of retraction" in them, and the
   documents the reviewer's broad rule marks that v2 does not.
3. The downstream overlap: replicate the 3,235, show the DOIs with more than one cohort row (the reviewer's 3,238),
   the strata and date sources of the overlap, and the added-before/after split within it.
4. Self-update-dated DOIs in the peS2o registry (the D4 problem, PMC arm) and their share of the matched set.

Run: venv/bin/python -I confirm_pes2o.py > confirm_pes2o.log 2> /tmp/confirm_pes2o_samples.txt
stdout (the log) carries identifiers, counts and shares only; the spot-check samples (first characters of a
document's first line) go to stderr and are not kept in the study.
"""
import contextlib
import io
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
RUN = HERE.parents[1]
T = RUN / "results" / "tables"
sys.path.insert(0, str(RUN / "code"))
import markers  # noqa: E402
import pes2o  # noqa: E402
import pes2o_secondary as PS  # noqa: E402


def sample(label, frame, k, rs=11):
    print(f"\n[{label}] n={len(frame)}, showing {min(k, len(frame))}", file=sys.stderr)
    for i, f in zip(frame.id, frame["first"]):
        pass
    for r in frame.sample(min(k, len(frame)), random_state=rs).itertuples():
        print(f"  {r.id} {r.doi} :: {r.first[:110]!r}", file=sys.stderr)


def main():
    # ---- 1. rerun the committed code into a scratch dir
    tmp = Path(tempfile.mkdtemp(prefix="confirm_d5_pes2o_"))
    PS.TAB = tmp
    with contextlib.redirect_stdout(io.StringIO()):
        PS.main()
    a = pd.read_csv(tmp / "pes2o_documents_d5.csv")
    b = pd.read_csv(T / "pes2o_documents_d5.csv")
    print("1. rerun of pes2o_secondary.py")
    print("   pes2o_documents_d5.csv rerun == committed:", a.equals(b), a.shape, b.shape)
    if not a.equals(b):
        for col in a.columns:
            if not a[col].equals(b[col]):
                print("   differing column:", col, int((a[col] != b[col]).sum()))
    ja, jb = json.load(open(tmp / "pes2o_secondary.json")), json.load(open(T / "pes2o_secondary.json"))
    print("   pes2o_secondary.json rerun == committed:", ja == jb)
    if ja != jb:
        for k in jb:
            if ja.get(k) != jb.get(k):
                print("   differing key:", k)
    print("   v2 share:", jb["marked_share"]["v2_D5"], "broad:", jb["marked_share"]["broad"], "v1:", jb["marked_share"]["v1_as_drafted"])

    # ---- 2. the rule
    d = b.copy()
    texts = {}
    with open(RUN / "data" / "pes2o" / "matched.jsonl") as fh:
        for line in fh:
            j = json.loads(line)
            texts[str(j["id"])] = j["text"]
    d["first"] = [texts[str(i)].split("\n", 1)[0] for i in d.id]
    d["notice_hit"] = [bool(PS.NOTICE.search(texts[str(i)])) for i in d.id]
    d["notice_first"] = [bool(PS.NOTICE.search(f)) for f in d["first"]]
    d["runon_hit"] = [PS.title_runon(f) for f in d["first"]]
    mine = pd.read_csv(HERE / "pes2o_rescored.csv")
    m = d.merge(mine[["id", "marked", "first_retract", "starts_notice", "broad"]].rename(columns={"broad": "rev_broad"}), on="id")
    print("\n2. the D5 rule against the reviewer's re-score")
    print("   joined", len(m), "of", len(d))
    print("   v1 == reviewer's application of the study rule on every document:", bool((m.v1 == m.marked).all()))
    print("   v2 x reviewer broad (rows v2, cols reviewer broad):")
    print(pd.crosstab(m.v2, m.rev_broad).to_string())
    print("   v2 marks a document the reviewer's broad rule does not:", int((m.v2 & ~m.rev_broad).sum()))
    print("   reviewer broad marks, v2 does not:", int((~m.v2 & m.rev_broad).sum()))
    new = d[d.v2 & ~d.v1]
    print("   documents only v2 marks (v2 & ~v1):", len(new), "(json says", jb["notice_of_retraction_runon_docs"], ")")
    print("     via NOTICE (anywhere):", int(new.notice_hit.sum()), "; of which in the first line:", int(new.notice_first.sum()))
    print("     via title_runon only (no NOTICE hit):", int((~new.notice_hit & new.runon_hit).sum()))
    print("     by source:", new.source.value_counts().to_dict())
    print("     DOI prefix:", new.doi.str.split("/").str[0].value_counts().head(6).to_dict())
    print("     first line starts 'Notice of Retraction' (reviewer's starts_notice):",
          int(m[m.v2 & ~m.v1].starts_notice.sum()))
    follow = Counter()
    for i in new.id:
        t = texts[str(i)]
        mm = PS.NOTICE.search(t)
        nxt = t[mm.end():mm.end() + 1] if mm else "<no NOTICE hit>"
        follow["UPPER" if nxt.isupper() else "lower" if nxt.islower() else "digit" if nxt.isdigit() else repr(nxt)] += 1
    print("     character after 'notice of retraction' in the v2-only documents:", follow.most_common(10))
    # whole-corpus: what the no-boundary NOTICE adds beyond v1's bounded statement, by following character
    add = d[d.notice_hit & ~d.v1]
    print("   NOTICE (no boundary) hits on documents v1 missed:", len(add))
    # over-matching probes on the whole matched set
    low = [i for i in add.id if (lambda t, mm: mm and t[mm.end():mm.end() + 1].islower())(texts[str(i)], PS.NOTICE.search(texts[str(i)]))]
    print("     of which followed by a lower-case letter (plural / other word):", len(low))
    ro = d[d.runon_hit & ~d.v1 & ~d.notice_hit]
    print("   title_runon-only documents:", len(ro), "by source:", ro.source.value_counts().to_dict())
    # the plan's title rule allows "after punctuation"; v1's TITLE already covers separators, so title_runon adds
    # only the capital-letter case. Show them all on stderr.
    sample("title_runon-only (run-together title prefix), all", ro, 60)
    sample("v2-only via NOTICE, random 20", new[new.notice_hit], 20)
    lowf = new[new.id.isin(low)]
    sample("v2-only via NOTICE followed by lower-case letter, all", lowf, 60)
    bo = m[~m.v2 & m.rev_broad].merge(d[["id", "first"]], on="id", suffixes=("", "_d"))
    bo["first"] = bo["first"]
    sample("reviewer-broad-only (v2 does not mark), up to 45", bo, 45)
    print("   reviewer-broad-only by source:", bo.source.value_counts().to_dict(),
          "; DOI prefix:", bo.doi.str.split("/").str[0].value_counts().head(5).to_dict())
    s2orc_new = new[new.source == "s2orc"]
    sample("v2-only among s2orc full texts, up to 15", s2orc_new, 15)

    # ---- 3. staleness and by-year from the committed table
    print("\n3. secondary figures recomputed from pes2o_documents_d5.csv")
    sub = d[d.ryear >= 2015]
    print("   staleness, retraction year >= 2015:",
          sub.groupby("after").v2.agg(["size", "mean"]).round(4).to_dict("index"))
    print("   whole set, added after vs before (for the record):",
          d.groupby("after").v2.agg(["size", "mean"]).round(4).to_dict("index"))
    by = d.groupby("ryear").v2.agg(["size", "mean"]).round(3)
    print("   by retraction year 2009-2011:", by.loc[[2009, 2010, 2011]].to_dict("index"))
    print("   2014-2022 range of v2:", round(by.loc[2014:2022]["mean"].min(), 3), "-", round(by.loc[2014:2022]["mean"].max(), 3))

    # ---- 4. the downstream overlap
    print("\n4. downstream overlap")
    c = pd.read_parquet(RUN / "data" / "cohort.parquet")
    ov = pd.read_csv(RUN / "results" / "overlay" / "retraction_overlay.csv.gz",
                     usecols=["pmcid", "own_marker", "sidecar_flag", "date_source"])
    c = c.merge(ov, on="pmcid", how="left")
    c["doi_n"] = c.doi.map(pes2o.ndoi)
    c = c.dropna(subset=["doi_n"])
    dup = c[c.doi_n.duplicated(keep=False) & c.doi_n.isin(set(d.doi))]
    print("   peS2o-matched DOIs with more than one cohort row:", dup.doi_n.nunique(), "; rows:", len(dup))
    cols = [x for x in ("doi_n", "pmcid", "in_snapshot", "notice", "stratum", "own_marker", "sidecar_flag") if x in dup.columns]
    print(dup.sort_values("doi_n")[cols].to_string(index=False))
    c1 = c.drop_duplicates("doi_n")                                   # the study's choice: first row
    m1 = d.merge(c1[["doi_n", "in_snapshot", "notice", "stratum", "own_marker", "date_source"]],
                 left_on="doi", right_on="doi_n", how="left")
    inp = m1[m1.in_snapshot.fillna(False).astype(bool) & ~m1.notice.fillna(False).astype(bool)]
    own = inp.own_marker.fillna(False).astype(bool)
    print("   study selection: n", len(inp), "; PMC own marker", round(own.mean(), 4), "; peS2o v2", round(inp.v2.mean(), 4),
          "; v1", round(inp.v1.mean(), 4))
    print("     strata:", inp.stratum.value_counts().to_dict())
    print("     date source:", inp.date_source.value_counts().to_dict())
    print("     by source:", inp.groupby("source").v2.agg(["size", "mean"]).round(4).to_dict("index"))
    print("     added after retraction vs before, within the overlap:",
          inp.groupby("after").agg(n=("id", "size"), v2=("v2", "mean"),
                                   pmc_own=("own_marker", lambda s: s.fillna(False).astype(bool).mean())).round(4).to_dict("index"))
    print("     retraction year >= 2015 within the overlap, added after vs before:",
          inp[inp.ryear >= 2015].groupby("after").agg(n=("id", "size"), v2=("v2", "mean")).round(4).to_dict("index"))
    pr = inp[inp.stratum.isin(["primary", "recent"])]
    print("   restricted to primary + recent strata (deviations.md wording): n", len(pr),
          "; PMC own", round(pr.own_marker.fillna(False).astype(bool).mean(), 4), "; v2", round(pr.v2.mean(), 4))
    c2 = c.sort_values(["in_snapshot", "notice"], ascending=[False, True]).drop_duplicates("doi_n")
    m2 = d.merge(c2[["doi_n", "in_snapshot", "notice", "stratum", "own_marker"]], left_on="doi", right_on="doi_n", how="left")
    inp2 = m2[m2.in_snapshot.fillna(False).astype(bool) & ~m2.notice.fillna(False).astype(bool)]
    print("   de-duplication preferring in-snapshot non-notice rows: n", len(inp2),
          "; PMC own", round(inp2.own_marker.fillna(False).astype(bool).mean(), 4), "; v2", round(inp2.v2.mean(), 4))
    m3 = d.merge(c[["doi_n", "in_snapshot", "notice", "own_marker"]], left_on="doi", right_on="doi_n", how="left")
    inp3 = m3[m3.in_snapshot.fillna(False).astype(bool) & ~m3.notice.fillna(False).astype(bool)]
    print("   no de-duplication (reviewer's earlier join): n", len(inp3),
          "; PMC own", round(inp3.own_marker.fillna(False).astype(bool).mean(), 4), "; v2", round(inp3.v2.mean(), 4))
    print("   not in the PMC registry: n", int(m1.doi_n.isna().sum()), "; v2", round(m1[m1.doi_n.isna()].v2.mean(), 4))

    # ---- 5. self-update dates in the peS2o registry
    print("\n5. Crossref self-update dates in the peS2o registry (the D4 problem)")
    rw = pd.read_csv(RUN / "data" / "raw" / "retraction_watch.csv", dtype=str, encoding="utf-8", encoding_errors="replace")
    rw["date"] = pd.to_datetime(rw.RetractionDate, format="%m/%d/%Y %H:%M", errors="coerce")
    rwset = {pes2o.ndoi(x) for x, dt in zip(rw[rw.RetractionNature == "Retraction"].OriginalPaperDOI,
                                            rw[rw.RetractionNature == "Retraction"].date) if pes2o.ndoi(x) and pd.notna(dt)}
    selfset, sepset = set(), set()
    with open(RUN / "data" / "raw" / "crossref_notices.jsonl") as fh:
        for line in fh:
            it = json.loads(line)
            own = pes2o.ndoi(it.get("DOI"))
            for u in it.get("update-to") or []:
                if (u.get("type") or "").lower() != "retraction":
                    continue
                k = pes2o.ndoi(u.get("DOI"))
                if not k:
                    continue
                (selfset if k == own else sepset).add(k)
    d["rw_dated"] = d.doi.isin(rwset)
    d["self_only"] = ~d.rw_dated & ~d.doi.isin(sepset) & d.doi.isin(selfset)
    print("   matched documents dated by Retraction Watch:", int(d.rw_dated.sum()), "; by a separate Crossref notice only:",
          int((~d.rw_dated & d.doi.isin(sepset)).sum()), "; by a Crossref self-update only:", int(d.self_only.sum()))
    so = d[d.self_only]
    print("   self-update-only: v2 marked", round(so.v2.mean(), 4) if len(so) else None,
          "; by source", so.source.value_counts().to_dict(), "; DOI prefix", so.doi.str.split("/").str[0].value_counts().head(4).to_dict())
    print("   self-update-only: 'retraction' (= issue) year:", so.ryear.value_counts().sort_index().to_dict())
    inp_self = inp[inp.doi.isin(set(so.doi))]
    print("   self-update-only within the 3,235 overlap:", len(inp_self), "; their PMC own marker",
          round(inp_self.own_marker.fillna(False).astype(bool).mean(), 4) if len(inp_self) else None,
          "; v2", round(inp_self.v2.mean(), 4) if len(inp_self) else None)
    print("   overlap without them: n", len(inp) - len(inp_self), "; PMC own",
          round(inp[~inp.doi.isin(set(so.doi))].own_marker.fillna(False).astype(bool).mean(), 4),
          "; v2", round(inp[~inp.doi.isin(set(so.doi))].v2.mean(), 4))
    print("   whole matched set without them: n", int((~d.self_only).sum()), "; v2", round(d[~d.self_only].v2.mean(), 4))
    print("\nscratch dir:", tmp)


if __name__ == "__main__":
    main()
