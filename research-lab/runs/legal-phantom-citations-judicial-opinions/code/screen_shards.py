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
import pickle
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
    paths, keep = args[0], args[1]
    chunk, nchunks = (args[2], args[3]) if len(args) > 2 else (0, 1)
    rows, cands, mis, vols, capped = [], [], [], Counter(), 0
    for i, rec in enumerate(records(paths, keep)):
        if i % nchunks != chunk:                   # D7: a shard is split into interleaved chunks for load balance
            continue
        row, c, m, v, cap = parse.screen((rec["opinion_id"], rec["cluster_id"], rec["date"], "", text_of(rec)))
        rows.append(row + (rec.get("ocr"), rec.get("type")))
        for x in c:
            x["ocr"] = rec.get("ocr")
        cands += c; mis += m; vols.update(v); capped += cap
    return rows, cands, mis, vols, capped


CHUNKS = 8
WORKERS = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else None


def part_name(job):
    return f"{Path(job[0][0]).name.split('.')[0]}_c{job[2]}of{job[3]}.pkl"


def work_saved(job):
    r = work(job)
    out = RUN / "data" / "screen" / ("pilot" if job[1] is not None else "") / "parts" / part_name(job)
    tmp = out.with_suffix(".tmp")
    with open(tmp, "wb") as fh:
        pickle.dump(r, fh)
    tmp.rename(out)
    return job, None


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
    # D7: scheduling only. Each shard is split into CHUNKS interleaved parts, each part's result is saved as it
    # completes (so an interrupted run resumes), and parts are merged in a fixed order. The decision for every
    # opinion is parse.screen(), unchanged.
    nchunks = 1 if sample else CHUNKS
    parts = out / "parts"
    parts.mkdir(exist_ok=True)
    jobs = [([p], keep, c, nchunks) for p in paths for c in range(nchunks)]
    todo = [j for j in jobs if not (parts / part_name(j)).exists()]
    print(f"{len(todo)} of {len(jobs)} parts to screen", flush=True)
    with mp.get_context("fork").Pool(WORKERS or max(1, mp.cpu_count() - 6)) as pool:
        for k, (j, r) in enumerate(pool.imap_unordered(work_saved, todo), 1):
            if k % 16 == 0:
                print(f"  {k}/{len(todo)} parts, {(time.time() - t0) / 60:.0f} min", flush=True)
    results = [pickle.load(open(parts / part_name(j), "rb")) for j in jobs]
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
