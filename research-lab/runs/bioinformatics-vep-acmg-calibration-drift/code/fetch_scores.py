#!/usr/bin/env python
"""Fetch predictor scores and gnomAD allele frequencies for every cohort variant from MyVariant.info (dbNSFP 4.8a).

Batches of 1,000 hg38 HGVS ids are POSTed; each raw response is cached under data/raw/scores/myvariant/ so the
fetch resumes. Multi-transcript scores are reduced per plan.md sec 4: the most pathogenic value (max; min for ESM1b)
is the primary score, the median a sensitivity score.

Output: data/processed/scores_myvariant.parquet
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

RUN = Path(__file__).resolve().parents[1]
PROC, CACHE = RUN / "data" / "processed", RUN / "data" / "raw" / "scores" / "myvariant"
FIELDS = ["dbnsfp.revel.score", "dbnsfp.alphamissense.score", "dbnsfp.esm1b.score", "dbnsfp.bayesdel.no_af.score",
          "dbnsfp.cadd.phred", "dbnsfp.varity.r_loo.score", "gnomad_exome.af.af", "gnomad_genome.af.af"]
BATCH = 1000


def nums(v):
    if v is None:
        return []
    v = v if isinstance(v, list) else [v]
    out = []
    for x in v:
        try:
            out.append(float(x))
        except (TypeError, ValueError):
            pass
    return out


def get(d, path):
    for k in path.split("."):
        if isinstance(d, list):                     # several docs / hits: take the first
            d = d[0] if d else None
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


def wanted_ids(from_status: bool):
    """hg38 HGVS ids to fetch: cohort variants, or (--from-status) every confident variant in the parsed snapshots."""
    if from_status:
        d = pd.concat([pd.read_parquet(f) for f in sorted(PROC.glob("status_*.parquet"))])
        d = d[d.label.notna()]
    else:
        d = pd.read_parquet(PROC / "cohorts.parquet")
    d = d.dropna(subset=["pos"])
    d = d[d.chrom.isin([str(c) for c in range(1, 23)] + ["X", "Y"]) & d.ref.str.fullmatch("[ACGT]", na=False)
          & d.alt.str.fullmatch("[ACGT]", na=False)]
    return sorted({f"chr{c}:g.{int(float(p))}{r}>{a}" for c, p, r, a in zip(d.chrom, d.pos, d.ref, d.alt)})


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    ids = wanted_ids("--from-status" in sys.argv)
    done = set()
    for f in CACHE.glob("batch_*.json"):                  # content-keyed resume: skip ids already fetched
        done.update(d.get("query") for d in json.load(open(f)))
    todo = [i for i in ids if i not in done]
    start = len(list(CACHE.glob("batch_*.json")))
    print(f"{len(ids):,} wanted, {len(done):,} cached, {len(todo):,} to fetch", flush=True)
    from concurrent.futures import ThreadPoolExecutor

    def fetch(job):
        n, chunk = job
        f = CACHE / f"batch_{start + n:05d}.json"
        s = requests.Session()
        for attempt in range(6):
            try:
                r = s.post("https://myvariant.info/v1/variant", timeout=180,
                           data={"ids": ",".join(chunk), "fields": ",".join(FIELDS), "assembly": "hg38"})
                r.raise_for_status()
                json.dump(r.json(), open(f.with_suffix(".part"), "w"))
                f.with_suffix(".part").rename(f)
                return n
            except Exception as e:                      # transient network / rate-limit errors
                print(f"batch {start + n}: attempt {attempt}: {e}", flush=True)
                time.sleep(10 * (attempt + 1))
        raise RuntimeError(f"batch {start + n} failed")

    jobs = [(n, todo[b:b + BATCH]) for n, b in enumerate(range(0, len(todo), BATCH))]
    with ThreadPoolExecutor(max_workers=3) as ex:          # three concurrent requests: polite to the public API
        for k, n in enumerate(ex.map(fetch, jobs)):
            if k % 10 == 0:
                print(f"batch {k} done ({min((k + 1) * BATCH, len(todo)):,}/{len(todo):,})", flush=True)
    if "--from-status" in sys.argv:
        return
    rows = []
    for f in sorted(CACHE.glob("batch_*.json")):
        for d in json.load(open(f)):
            q = d.get("query")
            if d.get("notfound"):
                rows.append({"hgvs": q, "found": False})
                continue
            rec = {"hgvs": q, "found": True}
            for name, path, red in (("revel", "dbnsfp.revel.score", "max"), ("am_dbnsfp", "dbnsfp.alphamissense.score", "max"),
                                    ("esm1b", "dbnsfp.esm1b.score", "min"), ("bayesdel", "dbnsfp.bayesdel.no_af.score", "max"),
                                    ("cadd", "dbnsfp.cadd.phred", "max"), ("varity_r", "dbnsfp.varity.r_loo.score", "max")):
                x = nums(get(d, path))
                rec[name] = (max(x) if red == "max" else min(x)) if x else np.nan
                rec[f"{name}_med"] = float(np.median(x)) if x else np.nan
                rec[f"{name}_n"] = len(x)
            for name, path in (("af_exome", "gnomad_exome.af.af"), ("af_genome", "gnomad_genome.af.af")):
                x = nums(get(d, path))
                rec[name] = max(x) if x else np.nan
            rows.append(rec)
    out = pd.DataFrame(rows).drop_duplicates("hgvs")
    out.to_parquet(PROC / "scores_myvariant.parquet", index=False)
    print(f"{len(out):,} records; found {int(out.found.sum()):,}; coverage: " +
          ", ".join(f"{c} {out[c].notna().mean():.3f}" for c in ("revel", "am_dbnsfp", "esm1b", "bayesdel", "cadd", "varity_r", "af_exome")))


if __name__ == "__main__":
    sys.exit(main())
