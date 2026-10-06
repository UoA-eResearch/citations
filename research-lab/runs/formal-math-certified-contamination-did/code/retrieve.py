"""Candidate retrieval (plan section 3), no Lean. For each benchmark item and corpus:
  L0: identical normalised statement;
  MinHash: top 10 corpus statements by MinHash-estimated Jaccard on character 5-grams (128 permutations), estimate >= 0.3;
  numerals: statements with the identical numeral multiset that share at least half of the item's identifiers.
Writes data/candidates/<bench>__<corpus>.parquet with bench_id, corpus_id, jac (MinHash estimate), via (L0 / minhash /
numerals) and results/tables/retrieval_counts.csv."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
ST = RUN / "data" / "statements"
OUT = RUN / "data" / "candidates"
K, NPERM, P = 10, 128, np.uint64((1 << 61) - 1)
rng = np.random.default_rng(20261007)
A = rng.integers(1, (1 << 61) - 1, NPERM, dtype=np.uint64)
B = rng.integers(0, (1 << 61) - 1, NPERM, dtype=np.uint64)
BASE = np.uint64(1000003)
MASK32 = np.uint64(0xFFFFFFFF)


def shingles(s, k=5):
    c = np.frombuffer(s.encode("utf-32-le"), dtype=np.uint32).astype(np.uint64)
    if len(c) < k:
        c = np.concatenate([c, np.zeros(k - len(c), np.uint64)])
    h = np.zeros(len(c) - k + 1, np.uint64)
    for j in range(k):
        h = (h * BASE + c[j:len(c) - k + 1 + j]) & MASK32
    return np.unique(h)


def signature(s):
    h = shingles(s)
    # (a * h + b) mod p, computed with 32-bit inputs so that the product fits in uint64 modulo 2^64 before the reduction;
    # a is reduced to 31 bits for that reason
    v = ((A[:, None] & np.uint64(0x7FFFFFFF)) * h[None, :] + B[:, None]) % P
    return v.min(axis=1).astype(np.uint64)


def signatures(texts):
    return np.stack([signature(t) for t in texts]) if len(texts) else np.zeros((0, NPERM), np.uint64)


def main(bench="bench_minif2f", corpora=None):
    OUT.mkdir(parents=True, exist_ok=True)
    b = pd.read_parquet(ST / f"{bench}.parquet").reset_index(drop=True)
    bsig = signatures(b.norm.tolist())
    bid = set()
    counts = []
    corpora = corpora or [p.stem for p in sorted(ST.glob("*.parquet")) if not p.stem.startswith("bench")]
    for corp in corpora:
        c = pd.read_parquet(ST / f"{corp}.parquet").reset_index(drop=True)
        rows = []
        # L0
        idx = {n: i for i, n in enumerate(c.norm)}
        for i, n in enumerate(b.norm):
            if n in idx:
                rows.append(dict(bench_id=b.id[i], corpus_id=c.id[idx[n]], jac=1.0, via="L0"))
        # MinHash top-K
        best = np.full((len(b), K), -1.0)
        bestj = np.full((len(b), K), -1, np.int64)
        CH = 4000
        for s in range(0, len(c), CH):
            sig = signatures(c.norm.iloc[s:s + CH].tolist())
            jac = (sig[None, :, :] == bsig[:, None, :]).mean(axis=2)  # (n_bench, chunk)
            allj = np.concatenate([best, jac], axis=1)
            alli = np.concatenate([bestj, np.arange(s, s + len(sig))[None, :].repeat(len(b), 0)], axis=1)
            top = np.argpartition(-allj, K - 1, axis=1)[:, :K]
            best = np.take_along_axis(allj, top, 1)
            bestj = np.take_along_axis(alli, top, 1)
        for i in range(len(b)):
            for j, v in zip(bestj[i], best[i]):
                if j >= 0 and v >= 0.3:
                    rows.append(dict(bench_id=b.id[i], corpus_id=c.id[j], jac=float(v), via="minhash"))
        # numerals
        byn = c.groupby("numerals").indices
        for i in range(len(b)):
            nu = b.numerals[i]
            if not nu or nu not in byn:
                continue
            bi = set(b.idents[i].split())
            for j in byn[nu]:
                ci = set(c.idents[j].split())
                if bi and len(bi & ci) >= 0.5 * len(bi):
                    rows.append(dict(bench_id=b.id[i], corpus_id=c.id[j], jac=np.nan, via="numerals"))
        r = pd.DataFrame(rows, columns=["bench_id", "corpus_id", "jac", "via"])
        r.to_parquet(OUT / f"{bench}__{corp}.parquet")
        counts.append(dict(bench=bench, corpus=corp, n_corpus=len(c), L0_items=r[r.via == "L0"].bench_id.nunique(),
                           minhash_pairs=int((r.via == "minhash").sum()), numeral_pairs=int((r.via == "numerals").sum()),
                           items_with_any=r.bench_id.nunique(), max_numeral_pairs_per_item=int(r[r.via == "numerals"].groupby("bench_id").size().max()) if (r.via == "numerals").any() else 0))
        print(counts[-1], flush=True)
    f = RUN / "results" / "tables" / "retrieval_counts.csv"
    old = pd.read_csv(f) if f.exists() else pd.DataFrame()
    new = pd.DataFrame(counts)
    if len(old):
        old = old[~(old.bench.isin(new.bench) & old.corpus.isin(new.corpus))]
    pd.concat([old, new]).to_csv(f, index=False)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "bench_minif2f", sys.argv[2:] or None)
