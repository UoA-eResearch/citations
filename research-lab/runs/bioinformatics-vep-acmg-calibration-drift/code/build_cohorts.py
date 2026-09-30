#!/usr/bin/env python
"""Parse the ClinVar variant_summary snapshots into missense-SNV status tables and build the plan.md sec 4 cohorts.

Per snapshot (GRCh38 rows, single-nucleotide variants whose Name carries a single amino-acid substitution):
  VariationID, gene, protein change, label (P / B / None), stars, number of submitters, raw ClinicalSignificance.
Label P = {Pathogenic, Likely pathogenic, Pathogenic/Likely pathogenic}; B = {Benign, Likely benign,
Benign/Likely benign}; a label counts only with >= 1 star (criteria provided); anything else (VUS, conflicting,
0-star, combined terms such as "Pathogenic; risk factor") is "not confident". Somatic-only records are dropped.

Cohorts (plan.md sec 4): C2019 = confident at 2019-12; N_Y = confident at Y and not confident at the previous
snapshot (label at Y); N_new = union of N_2021..N_2026 (label at the first confident snapshot).
Coordinates (GRCh38 chrom, pos, ref, alt) come from the newest snapshot that carries VCF-style alleles.

Output: data/processed/status_<snapshot>.parquet, data/processed/cohorts.parquet, results/tables/cohort_counts.csv
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
RAW, PROC, TAB = RUN / "data" / "raw" / "clinvar", RUN / "data" / "processed", RUN / "results" / "tables"
SNAPS = ["2019-12", "2020-12", "2021-12", "2022-12", "2023-12", "2024-12", "2025-12", "2026-09"]
COHORT_YEAR = {"2020-12": 2020, "2021-12": 2021, "2022-12": 2022, "2023-12": 2023, "2024-12": 2024, "2025-12": 2025,
               "2026-09": 2026}
P_TERMS = {"Pathogenic", "Likely pathogenic", "Pathogenic/Likely pathogenic"}
B_TERMS = {"Benign", "Likely benign", "Benign/Likely benign"}
STARS = {"practice guideline": 4, "reviewed by expert panel": 3,
         "criteria provided, multiple submitters, no conflicts": 2,
         "criteria provided, single submitter": 1,
         "criteria provided, conflicting interpretations": 1, "criteria provided, conflicting classifications": 1}
AA3 = {"Ala", "Arg", "Asn", "Asp", "Cys", "Gln", "Glu", "Gly", "His", "Ile", "Leu", "Lys", "Met", "Phe", "Pro", "Ser",
       "Thr", "Trp", "Tyr", "Val"}
PCHANGE = re.compile(r"\(p\.([A-Z][a-z]{2})(\d+)([A-Z][a-z]{2})\)")


def parse_snapshot(snap: str) -> pd.DataFrame:
    cols = ["Type", "Name", "GeneSymbol", "ClinicalSignificance", "OriginSimple", "Assembly", "Chromosome", "Start",
            "ReferenceAllele", "AlternateAllele", "ReviewStatus", "NumberSubmitters", "VariationID"]
    vcf_cols = ["PositionVCF", "ReferenceAlleleVCF", "AlternateAlleleVCF"]
    path = RAW / f"variant_summary_{snap}.txt.gz"
    head = pd.read_csv(path, sep="\t", nrows=0).columns
    use = [c for c in cols + vcf_cols if c in head]
    df = pd.read_csv(path, sep="\t", usecols=use, dtype=str, low_memory=False)
    n0 = len(df)
    df = df[(df.Assembly == "GRCh38") & (df.Type == "single nucleotide variant")]
    df = df[df.OriginSimple.fillna("") != "somatic"]
    m = df.Name.str.extract(PCHANGE)
    ok = m[0].isin(AA3) & m[2].isin(AA3) & (m[0] != m[2])
    df, m = df[ok.values], m[ok.values]
    out = pd.DataFrame({
        "variation_id": df.VariationID.astype(np.int64).values,
        "gene": df.GeneSymbol.values,
        "pchange": (m[0] + m[1] + m[2]).values,
        "clinsig": df.ClinicalSignificance.values,
        "review_status": df.ReviewStatus.values,
        "stars": df.ReviewStatus.map(STARS).fillna(0).astype(int).values,
        "n_submitters": pd.to_numeric(df.NumberSubmitters, errors="coerce").fillna(0).astype(int).values,
        "chrom": df.Chromosome.values,
        "pos": (df.PositionVCF if "PositionVCF" in df else df.Start).values,
        "ref": (df.ReferenceAlleleVCF if "ReferenceAlleleVCF" in df else df.ReferenceAllele).values,
        "alt": (df.AlternateAlleleVCF if "AlternateAlleleVCF" in df else df.AlternateAllele).values,
    })
    lab = np.where(out.clinsig.isin(P_TERMS), "P", np.where(out.clinsig.isin(B_TERMS), "B", None))
    conflict = out.review_status.str.contains("conflicting", na=False)
    out["label"] = np.where((out.stars >= 1) & ~conflict, lab, None)
    out = out.drop_duplicates("variation_id")
    print(f"{snap}: {n0:,} rows -> {len(out):,} missense SNVs; confident P {int((out.label == 'P').sum()):,}, "
          f"B {int((out.label == 'B').sum()):,}", flush=True)
    return out


def main():
    PROC.mkdir(parents=True, exist_ok=True)
    TAB.mkdir(parents=True, exist_ok=True)
    status = {}
    for s in SNAPS:
        p = PROC / f"status_{s}.parquet"
        if p.exists():
            status[s] = pd.read_parquet(p)
        else:
            status[s] = parse_snapshot(s)
            status[s].to_parquet(p, index=False)
    # coordinates: newest snapshot with VCF-style alleles first
    coords = pd.concat([status[s][["variation_id", "chrom", "pos", "ref", "alt"]] for s in reversed(SNAPS)])
    valid = coords.ref.str.fullmatch("[ACGT]", na=False) & coords.alt.str.fullmatch("[ACGT]", na=False)
    coords = coords[valid].drop_duplicates("variation_id")
    rows = []
    c19 = status["2019-12"][status["2019-12"].label.notna()]
    c19 = c19.assign(cohort="C2019", year=2019, first_snapshot="2019-12")
    rows.append(c19)
    for prev, cur in zip(SNAPS[:-1], SNAPS[1:]):
        a, b = status[prev], status[cur]
        conf_prev = set(a.variation_id[a.label.notna()])
        new = b[b.label.notna() & ~b.variation_id.isin(conf_prev)]
        rows.append(new.assign(cohort=f"N_{COHORT_YEAR[cur]}", year=COHORT_YEAR[cur], first_snapshot=cur))
    coh = pd.concat(rows, ignore_index=True).drop(columns=["chrom", "pos", "ref", "alt"])
    coh = coh.merge(coords, on="variation_id", how="left")
    # latest label (2026-09) and whether a confident label later flipped P <-> B
    last = status["2026-09"].set_index("variation_id").label
    coh["label_2026"] = coh.variation_id.map(last)
    coh["flipped_later"] = coh.label_2026.notna() & (coh.label_2026 != coh.label)
    coh["in_new"] = coh.year.between(2021, 2026)
    # a variant can be newly confident more than once (confident -> not -> confident); N_new keeps the first entry
    first_new = coh[coh.in_new].sort_values("year").drop_duplicates("variation_id").index
    coh["primary_new"] = coh.index.isin(first_new)
    coh.to_parquet(PROC / "cohorts.parquet", index=False)
    cnt = coh.groupby(["cohort", "label"]).size().unstack(fill_value=0)
    cnt.loc["N_new (primary)"] = coh[coh.primary_new].groupby("label").size()
    cnt["genes"] = [coh[coh.cohort == c].gene.nunique() if c.startswith(("C", "N_2")) else coh[coh.primary_new].gene.nunique()
                    for c in cnt.index]
    cnt["missing_coords"] = [int(coh[(coh.cohort == c) if c != "N_new (primary)" else coh.primary_new].pos.isna().sum())
                             for c in cnt.index]
    cnt.to_csv(TAB / "cohort_counts.csv")
    print(cnt.to_string())
    print(f"flipped P<->B by 2026-09 among N_new: {int(coh[coh.primary_new].flipped_later.sum())}")


if __name__ == "__main__":
    sys.exit(main())
