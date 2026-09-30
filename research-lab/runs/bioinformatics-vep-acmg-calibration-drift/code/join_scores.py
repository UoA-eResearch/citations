#!/usr/bin/env python
"""Join cohorts, MyVariant/dbNSFP scores and the official AlphaMissense hg38 release; apply the rarity filter.

AlphaMissense primary score = the official hg38 release (one score per variant, canonical transcript); the dbNSFP
maximum over transcripts is the fallback (plan.md sec 3-4). Rare = gnomAD v2.1.1 exome AF < 0.01 (genome AF when
the exome AF is missing; absent from gnomAD counts as rare). VCEP gene = any gene with a ClinGen ERepo classification.

Output: data/processed/analysis_table.parquet, results/tables/score_coverage.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
PROC, RAWS, TAB = RUN / "data" / "processed", RUN / "data" / "raw" / "scores", RUN / "results" / "tables"
CHROMS = [str(c) for c in range(1, 23)] + ["X", "Y"]


def key(chrom, pos):
    ci = pd.Series(chrom).map({c: i + 1 for i, c in enumerate(CHROMS)}).fillna(0).astype(np.int64).values
    return ci * 10**10 + np.asarray(pos, dtype=np.int64)


def am_subset(coh: pd.DataFrame) -> pd.DataFrame:
    """Official AlphaMissense hg38 scores at the cohort positions (cached: streaming 71M rows takes minutes)."""
    cache = PROC / "am_subset.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    need = set(key(coh.chrom, coh.pos))
    parts = []
    # skip the three licence comment lines; the header line starts with '#CHROM'
    for ch in pd.read_csv(RAWS / "AlphaMissense_hg38.tsv.gz", sep="\t", skiprows=3, chunksize=5_000_000,
                          usecols=["#CHROM", "POS", "REF", "ALT", "am_pathogenicity"], dtype={"#CHROM": str}):
        ch["#CHROM"] = ch["#CHROM"].str.replace("chr", "", regex=False)
        parts.append(ch[pd.Series(key(ch["#CHROM"], ch.POS)).isin(need).values])
    am = pd.concat(parts).rename(columns={"#CHROM": "chrom", "POS": "pos", "REF": "ref", "ALT": "alt", "am_pathogenicity": "am_official"})
    am = am.drop_duplicates(["chrom", "pos", "ref", "alt"])
    am.to_parquet(cache, index=False)
    return am


def main():
    coh = pd.read_parquet(PROC / "cohorts.parquet")
    coh = coh[coh.chrom.isin(CHROMS) & coh.pos.notna()].copy()
    coh["pos"] = coh.pos.astype(float).astype(np.int64)
    coh["hgvs"] = "chr" + coh.chrom + ":g." + coh.pos.astype(str) + coh.ref + ">" + coh.alt
    sc = pd.read_parquet(PROC / "scores_myvariant.parquet")
    df = coh.merge(sc, on="hgvs", how="left")
    am = am_subset(coh)
    df = df.merge(am, on=["chrom", "pos", "ref", "alt"], how="left")
    df["am"] = df.am_official.where(df.am_official.notna(), df.am_dbnsfp)
    df["am_source"] = np.where(df.am_official.notna(), "official", np.where(df.am_dbnsfp.notna(), "dbnsfp", "none"))
    af = df.af_exome.where(df.af_exome.notna(), df.af_genome)
    df["af"] = af
    df["rare"] = af.isna() | (af < 0.01)
    vcep = pd.read_parquet(PROC / "vcep_recount.parquet")
    df["vcep_gene"] = df.gene.isin(set(vcep.gene.dropna()))
    df.to_parquet(PROC / "analysis_table.parquet", index=False)
    cov = df.groupby("cohort").agg(n=("variation_id", "size"), rare=("rare", "mean"), found=("found", "mean"),
                                   revel=("revel", lambda s: s.notna().mean()), am=("am", lambda s: s.notna().mean()),
                                   am_official=("am_official", lambda s: s.notna().mean()),
                                   esm1b=("esm1b", lambda s: s.notna().mean()), bayesdel=("bayesdel", lambda s: s.notna().mean()),
                                   varity_r=("varity_r", lambda s: s.notna().mean()), cadd=("cadd", lambda s: s.notna().mean()))
    cov.to_csv(TAB / "score_coverage.csv")
    print(cov.round(3).to_string())
    print("AlphaMissense official vs dbNSFP-max, where both exist: corr",
          round(float(df[["am_official", "am_dbnsfp"]].dropna().corr().iloc[0, 1]), 4),
          "| mean abs diff", round(float((df.am_official - df.am_dbnsfp).abs().mean()), 4))


if __name__ == "__main__":
    sys.exit(main())
