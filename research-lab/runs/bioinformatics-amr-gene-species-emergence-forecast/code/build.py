"""Isolate table and pair first-observation table (plan sections 0-1).

  build.py -> data/isolates.parquet (biosample, year, species, bioproject, country, genes: list of symbols)
              data/pairs.parquet (gene, species, first_year_any, first_year_2bp: year the pair reached two BioProjects)
              results/tables/build.json (counts per step, AMRFinderPlus / reference-database versions seen)
"""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
RAW, D, T = RUN / "data" / "raw", RUN / "data", RUN / "results" / "tables"
COLS = ["biosample_acc", "scientific_name", "collection_date", "geo_loc_name", "bioproject_acc", "AMR_genotypes_core",
        "amrfinder_version", "refgene_db_version"]
SPECIES = re.compile(r"^([A-Z][a-z]+) ([a-z][a-z-]+)\b")


def species_of(name):
    m = SPECIES.match(str(name))
    return f"{m.group(1)} {m.group(2)}" if m and m.group(2) not in ("sp", "spp", "bacterium") else None


def year_of(d):
    m = re.match(r"^(\d{4})", str(d))
    return int(m.group(1)) if m else None


def genes_of(s):
    """AMRFinderPlus core calls 'symbol=TYPE', comma-separated; point mutations (=POINT) are dropped."""
    if not isinstance(s, str) or not s or s in ("NULL",):
        return []
    out = []
    for tok in s.split(","):
        sym, _, typ = tok.strip().strip('"').partition("=")
        if sym and typ != "POINT":
            out.append(sym)
    return sorted(set(out))


def main():
    stats, parts, vers = {"files": 0, "rows": 0}, [], {}
    for f in sorted(RAW.glob("*.metadata.tsv")):
        d = pd.read_csv(f, sep="\t", usecols=lambda c: c.lstrip("#") in COLS, dtype=str, low_memory=False)
        d.columns = [c.lstrip("#") for c in d.columns]
        for c in COLS:                                     # column sets differ between organism groups
            if c not in d.columns:
                d[c] = None
        stats["files"] += 1; stats["rows"] += len(d)
        for c in ("amrfinder_version", "refgene_db_version"):
            for k, v in d[c].value_counts().head(3).items():
                vers.setdefault(c, {}); vers[c][k] = vers[c].get(k, 0) + int(v)
        parts.append(d.assign(group=f.name.split(".")[0]))
    d = pd.concat(parts, ignore_index=True)
    d = d.drop_duplicates("biosample_acc")
    stats["unique_biosamples"] = len(d)
    d["species"] = d.scientific_name.map(species_of)
    d["year"] = d.collection_date.map(year_of)
    stats["no_species"] = int(d.species.isna().sum())
    stats["no_year_or_out_of_range"] = int((d.year.isna() | (d.year < 1990) | (d.year > 2025)).sum())
    d = d[d.species.notna() & d.year.between(1990, 2025)]
    stats["no_amr_call_field"] = int(d.AMR_genotypes_core.isna().sum())
    d = d[d.AMR_genotypes_core.notna()]
    d["genes"] = d.AMR_genotypes_core.map(genes_of)
    d["country"] = d.geo_loc_name.fillna("").str.split(":").str[0].str.strip()
    iso = d[["biosample_acc", "year", "species", "bioproject_acc", "country", "genes", "group"]].rename(columns={"biosample_acc": "biosample"})
    iso["year"] = iso.year.astype(int)
    iso.to_parquet(D / "isolates.parquet")
    stats["isolates_kept"] = len(iso); stats["isolates_with_any_gene"] = int((iso.genes.str.len() > 0).sum())
    stats["species"] = int(iso.species.nunique()); stats["versions_top"] = vers
    # pair first observations: any isolate, and the year the pair reaches two distinct BioProjects
    ex = iso[["species", "year", "bioproject_acc", "genes"]].explode("genes").dropna(subset=["genes"]).rename(columns={"genes": "gene"})
    ex = ex.sort_values("year")
    first_any = ex.groupby(["gene", "species"]).year.min().rename("first_year_any")
    bp_first = ex.groupby(["gene", "species", "bioproject_acc"]).year.min().reset_index()
    second = bp_first.sort_values("year").groupby(["gene", "species"]).year.apply(lambda y: y.iloc[1] if len(y) > 1 else np.nan).rename("first_year_2bp")
    pairs = pd.concat([first_any, second], axis=1).reset_index()
    pairs.to_parquet(D / "pairs.parquet")
    stats["genes"] = int(pairs.gene.nunique()); stats["observed_pairs"] = len(pairs)
    (T / "build.json").write_text(json.dumps(stats, indent=1) + "\n")
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main()
