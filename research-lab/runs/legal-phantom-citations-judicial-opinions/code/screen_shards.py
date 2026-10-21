"""Screen the extracted in-window opinions, shard by shard, in parallel (plan section 4, steps 1-5).

Uses parse.py's screen() -- the same per-citation decision, parse.judge(), that the validation tests -- over the
shards written by extract.py. The indices are loaded once in the parent and the workers are forked, so they share
them (parse.init docstring).

  --sample N   the in-window pilot (deviations D3): a seeded random sample of N opinions across all shards, screened
               before the screen is frozen. Writes data/screen/pilot/...
  (default)    the full screen of every in-window opinion. Writes data/screen/...

Outputs, in the chosen directory: candidates.jsonl, misattributions.jsonl, opinions.tsv, volumes.json, and
court lookups are added later by analysis (scope from dockets).
"""
import gzip
import html as htmlmod
import json
import multiprocessing as mp
import random
import re
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import parse  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
SHARDS = RUN / "data" / "opinions"
TAG = re.compile(r"<[^>]+>")
SEED = 20261021


def text_of(rec):
    t = rec["raw"]
    if rec["field"] != "plain_text":
        t = htmlmod.unescape(TAG.sub(" ", t))
    return t


def records(paths, keep=None):
    for p in paths:
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            for line in fh:
                rec = json.loads(line)
                if keep is None or rec["opinion_id"] in keep:
                    yield rec


def work(args):
    paths, keep = args
    rows, cands, mis, vols, capped = [], [], [], Counter(), 0
    for rec in records(paths, keep):
        row, c, m, v, cap = parse.screen((rec["opinion_id"], rec["cluster_id"], rec["date"], "", text_of(rec)))
        rows.append(row + (rec.get("ocr"), rec.get("type")))
        for x in c:
            x["ocr"] = rec.get("ocr")
        cands += c; mis += m; vols.update(v); capped += cap
    return rows, cands, mis, vols, capped


def main():
    sample = int(sys.argv[sys.argv.index("--sample") + 1]) if "--sample" in sys.argv else None
    out = RUN / "data" / "screen" / ("pilot" if sample else "")
    out.mkdir(parents=True, exist_ok=True)
    paths = sorted(SHARDS.glob("shard_*.jsonl.gz"))
    keep = None
    if sample:
        ids = [rec["opinion_id"] for rec in records(paths)]
        keep = set(random.Random(SEED).sample(ids, min(sample, len(ids))))
        print(f"pilot: {len(keep):,} of {len(ids):,} in-window opinions, seed {SEED}", flush=True)
    t0 = time.time()
    parse.init()                                   # once, before forking
    jobs = [([p], keep) for p in paths]
    with mp.get_context("fork").Pool(max(1, mp.cpu_count() - 6)) as pool:
        results = pool.map(work, jobs, chunksize=1)
    rows, cands, mis, vols, capped = [], [], [], Counter(), 0
    for r in results:
        rows += r[0]; cands += r[1]; mis += r[2]; vols.update(r[3]); capped += r[4]
    with open(out / "opinions.tsv", "w") as fh:
        fh.write("opinion_id\tcluster_id\tdate\tcourt\tn_full\tn_resolved\tn_consistent\tocr\ttype\n")
        for row in rows:
            fh.write("\t".join(map(str, row)) + "\n")
    with open(out / "candidates.jsonl", "w") as fh:
        for c in cands:
            fh.write(json.dumps(c) + "\n")
    with open(out / "misattributions.jsonl", "w") as fh:
        for m in mis:
            fh.write(json.dumps(m) + "\n")
    full = sum(r[4] for r in rows if r[4] > 0)
    summary = dict(opinions=len(rows), full_citations=full, candidates=len(cands), misattributions=len(mis),
                   candidates_per_1000_citations=round(1000 * len(cands) / max(1, full), 2),
                   capped_name_searches=capped, minutes=round((time.time() - t0) / 60, 1))
    json.dump(dict(volumes=dict(vols), **summary), open(out / "volumes.json", "w"))
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
