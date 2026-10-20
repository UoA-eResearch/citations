"""Build the case-name index from the opinion-clusters snapshot (plan section 4, step 4).

D1 established that this is the primary detector: a fabricated citation usually mimics a real citation format
and so resolves by volume and page, but the *name* it carries matches nothing. This builds the structures that
let the screen ask "does any case anywhere have roughly this name?" over about ten million clusters.

Writes, into data/index/:
  clusters.tsv   one row per cluster: id, date_filed (yyyymmdd), docket_id, precedential_status, case name
  names.npy      the normalised name for each row, aligned to clusters.tsv
  tokens.pkl     distinctive token -> row indices, so a fuzzy search touches thousands of names, not millions
"""
import bz2
import csv
import pickle
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from namenorm import norm_name, tokens_of  # noqa: E402  one shared definition, see namenorm.py

RUN = Path(__file__).resolve().parents[1]
RAW, IDX = RUN / "data" / "raw", RUN / "data" / "index"
csv.field_size_limit(sys.maxsize)

MAX_POSTINGS = 400_000       # a token in more rows than this cannot narrow a search


def dropped_counts(norms, dropped):
    want = set(dropped)
    counts = {t: 0 for t in want}
    for nn in norms:
        for t in tokens_of(nn) & want:
            counts[t] += 1
    return counts


def write_dropped(counts):
    import json
    json.dump({"max_postings": MAX_POSTINGS, "dropped": counts}, open(IDX / "dropped_tokens.json", "w"), indent=1)
    print(f"dropped as too common: {sorted(counts)}", flush=True)


def only_dropped():
    """Recompute just the dropped-token list from an existing names.npy (no full rebuild)."""
    norms = np.load(IDX / "names.npy", allow_pickle=True)
    freq = defaultdict(int)
    for nn in norms:
        for t in tokens_of(nn):
            freq[t] += 1
    write_dropped({t: n for t, n in freq.items() if n > MAX_POSTINGS})


def main():
    IDX.mkdir(parents=True, exist_ok=True)
    ids, dates, dockets, status, names, norms = [], [], [], [], [], []
    n = 0
    with bz2.open(RAW / "opinion-clusters.csv.bz2", "rt", encoding="utf-8", errors="ignore") as fh, \
            open(IDX / "clusters.tsv", "w", encoding="utf-8") as out:
        out.write("cluster_id\tdate_filed\tdocket_id\tprecedential_status\tcase_name\n")
        for row in csv.DictReader(fh):
            try:
                cid = int(row["id"])
            except (ValueError, TypeError, KeyError):
                continue
            name = (row.get("case_name") or row.get("case_name_full") or row.get("case_name_short") or "").strip()
            nn = norm_name(name)
            if not nn:
                continue
            d = (row.get("date_filed") or "")[:10].replace("-", "")
            try:
                di = int(d) if len(d) == 8 else 0
            except ValueError:
                di = 0
            dock = row.get("docket_id") or ""
            try:
                dock = int(dock)
            except (ValueError, TypeError):
                dock = 0
            ids.append(cid); dates.append(di); dockets.append(dock)
            status.append(row.get("precedential_status") or "")
            names.append(name.replace("\t", " ").replace("\n", " ")); norms.append(nn)
            out.write(f"{cid}\t{di}\t{dock}\t{status[-1]}\t{names[-1]}\n")
            n += 1
            if n % 1_000_000 == 0:
                print(f"  {n:,} clusters", flush=True)

    print(f"{n:,} clusters with a usable name", flush=True)
    np.save(IDX / "names.npy", np.array(norms, dtype=object), allow_pickle=True)
    np.savez_compressed(IDX / "cluster_meta.npz", ids=np.array(ids, dtype=np.int64),
                        dates=np.array(dates, dtype=np.int32), dockets=np.array(dockets, dtype=np.int64))

    post = defaultdict(list)
    for i, nn in enumerate(norms):
        for t in tokens_of(nn):
            post[t].append(i)
    dropped = [t for t, v in post.items() if len(v) > MAX_POSTINGS]
    for t in dropped:
        del post[t]
    # Record what was dropped. A dropped token is absent from the index because it is in too many names to be
    # useful, which is the opposite of a token absent because it is in none -- lookups must tell them apart.
    write_dropped(dropped_counts(norms, dropped))
    print(f"{len(post):,} distinctive tokens ({len(dropped):,} too common and dropped)", flush=True)
    with open(IDX / "tokens.pkl", "wb") as fh:
        pickle.dump({t: np.array(v, dtype=np.int32) for t, v in post.items()}, fh, protocol=4)
    print("wrote the name index")


if __name__ == "__main__":
    only_dropped() if "--dropped-only" in sys.argv else main()
