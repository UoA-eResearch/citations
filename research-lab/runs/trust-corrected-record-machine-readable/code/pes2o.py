"""Secondary 7: retraction markers in peS2o v2 (knowledge cutoff 2023-01-03), a derived pretraining corpus.

Registry: dated retractions (Retraction Watch, not reinstated; else Crossref update-to) with a DOI, retracted on or
before 2022-07-07 (180 days before the cutoff), notices excluded. DOIs -> Semantic Scholar corpus ids (Graph API
batch, unauthenticated). The 22 v2 shards are streamed and only matching documents are kept. A matched document is
marked if its text carries a textual marker (markers.txt_markers). Matching is lossy, so counts are lower bounds.
Writes data/pes2o/{corpus_ids.json, matched.jsonl} and results/tables/pes2o.json.
"""
import concurrent.futures as cf
import gzip
import json
import sys
import time
import urllib.request
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import markers  # noqa: E402
from match import ndoi  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
RAW, OUT = RUN / "data" / "raw", RUN / "data" / "pes2o"
CUT = pd.Timestamp("2022-07-07")
HF = "https://huggingface.co/datasets/allenai/peS2o/resolve/main/data/v2/"


def registry():
    rw = pd.read_csv(RAW / "retraction_watch.csv", dtype=str, encoding="utf-8", encoding_errors="replace")
    rw["date"] = pd.to_datetime(rw.RetractionDate, format="%m/%d/%Y %H:%M", errors="coerce")
    # D1: a notice identifier equal to the original's (or a Crossref assertion pointing at itself) is not a notice
    notices = {ndoi(a) for a, b in zip(rw.RetractionDOI, rw.OriginalPaperDOI) if ndoi(a) and ndoi(a) != ndoi(b)}
    reinst = {ndoi(x) for x in rw[rw.RetractionNature == "Reinstatement"].OriginalPaperDOI if ndoi(x)}
    dates = {}
    for r in rw[rw.RetractionNature == "Retraction"].itertuples():
        k = ndoi(r.OriginalPaperDOI)
        if k and k not in reinst and pd.notna(r.date):
            dates[k] = min(dates.get(k, r.date), r.date)
    for line in open(RAW / "crossref_notices.jsonl"):
        it = json.loads(line)
        own = ndoi(it.get("DOI"))
        if own and any(ndoi(u.get("DOI")) != own for u in it.get("update-to") or []
                       if (u.get("type") or "").lower() == "retraction"):
            notices.add(own)
        for u in it.get("update-to") or []:
            k = ndoi(u.get("DOI"))
            dp = ((u.get("updated") or {}).get("date-parts") or [[None]])[0]
            if (u.get("type") or "").lower() == "retraction" and k and k not in dates and dp and dp[0]:
                dates[k] = pd.Timestamp(year=dp[0], month=dp[1] if len(dp) > 1 else 1, day=dp[2] if len(dp) > 2 else 1)
    return {k: v for k, v in dates.items() if v <= CUT and k not in notices - set(dates)}


def corpus_ids(dois):
    p = OUT / "corpus_ids.json"
    got = json.load(open(p)) if p.exists() else {}
    todo = [d for d in dois if d not in got]
    for i in range(0, len(todo), 500):
        chunk = todo[i:i + 500]
        body = json.dumps({"ids": [f"DOI:{d}" for d in chunk]}).encode()
        for t in range(8):
            try:
                req = urllib.request.Request("https://api.semanticscholar.org/graph/v1/paper/batch?fields=corpusId",
                                             data=body, headers={"Content-Type": "application/json"})
                res = json.loads(urllib.request.urlopen(req, timeout=120).read())
                break
            except Exception as e:
                time.sleep(10 * (t + 1))
        else:
            raise RuntimeError("Semantic Scholar batch failed repeatedly")
        for d, r in zip(chunk, res):
            got[d] = r.get("corpusId") if r else None
        json.dump(got, open(p, "w"))
        time.sleep(1.5)
        print("s2", i + len(chunk), "/", len(todo), flush=True)
    return got


def stream(name, want):
    keep, n = [], 0
    with urllib.request.urlopen(HF + name, timeout=600) as r:
        for line in gzip.GzipFile(fileobj=r):
            n += 1
            j = json.loads(line)
            if j["id"] in want:
                keep.append(j)
    return name, n, keep


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    reg = registry()
    ids = corpus_ids(sorted(reg))
    want = {str(v): k for k, v in ids.items() if v}
    names = [f"train-{i:05d}-of-00020.json.gz" for i in range(20)] + [f"validation-{i:05d}-of-00002.json.gz" for i in range(2)]
    total, matched = 0, []
    with cf.ThreadPoolExecutor(8) as ex:
        for name, n, keep in ex.map(lambda s: stream(s, want), names):
            total += n
            matched += keep
            print(name, n, len(keep), flush=True)
    with open(OUT / "matched.jsonl", "w") as fh:
        for j in matched:
            fh.write(json.dumps(j) + "\n")
    rows = []
    for j in matched:
        m = markers.txt_markers(j["text"])
        rows.append({"id": j["id"], "doi": want[j["id"]], "source": j["source"], "marked": m["textual"],
                     "kinds": ";".join(m["kinds"])})
    d = pd.DataFrame(rows)
    out = {"registry_dois_retracted_by_2022_07_07": len(reg), "with_corpus_id": len(want), "pes2o_documents": total,
           "matched_documents": len(d),
           "marked_share": round(float(d.marked.mean()), 4) if len(d) else None,
           "by_source": d.groupby("source").marked.agg(["size", "mean"]).round(4).to_dict(orient="index") if len(d) else {},
           "kinds": d.kinds.str.split(";").explode().value_counts().to_dict() if len(d) else {}}
    json.dump(out, open(RUN / "results" / "tables" / "pes2o.json", "w"), indent=1)
    d.to_csv(RUN / "results" / "tables" / "pes2o_documents.csv", index=False)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
