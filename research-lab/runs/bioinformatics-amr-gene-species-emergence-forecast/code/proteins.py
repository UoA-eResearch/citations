"""Gene symbol -> reference protein sequence (plan section 1).

AMRProt.fa headers are pipe-separated: accession|?|?|allele|gene_family|...|class|product. A metadata symbol is
matched to an allele first, then to a gene family. The database version is recorded.

  proteins.py -> data/gene_proteins.parquet (gene, how, accession, length, seq), results/tables/proteins.json
"""
import json
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"


def read_fasta(p):
    name, buf = None, []
    for line in open(p):
        if line.startswith(">"):
            if name:
                yield name, "".join(buf)
            name, buf = line[1:].rstrip("\n"), []
        else:
            buf.append(line.strip())
    if name:
        yield name, "".join(buf)


def main():
    by_allele, by_family = {}, {}
    for h, seq in read_fasta(D / "raw_ref" / "AMRProt.fa"):
        f = h.split("|")
        acc, allele, family = f[0], f[3], f[4]
        if allele and (allele not in by_allele or len(seq) > len(by_allele[allele][1])):
            by_allele[allele] = (acc, seq)
        if family and (family not in by_family or len(seq) > len(by_family[family][1])):
            by_family[family] = (acc, seq)
    by_acc = {}
    for h, seq in read_fasta(D / "raw_ref" / "AMRProt.fa"):
        by_acc[h.split("|")[0]] = seq
    cat = pd.read_csv(D / "raw_ref" / "ReferenceGeneCatalog.txt", sep="\t", dtype=str, low_memory=False)
    by_catalog = {}                                        # symbol -> longest catalogued protein present in the FASTA
    for col in ("allele", "gene_family"):
        for sym, acc in zip(cat[col], cat.refseq_protein_accession.fillna(cat.genbank_protein_accession)):
            if isinstance(sym, str) and isinstance(acc, str) and acc in by_acc:
                if sym not in by_catalog or len(by_acc[acc]) > len(by_catalog[sym][1]):
                    by_catalog[sym] = (acc, by_acc[acc])
    iso = pd.read_parquet(D / "isolates.parquet", columns=["genes"])
    genes = pd.Series([g for gs in iso.genes for g in gs]).value_counts()
    rows = []
    for g, n in genes.items():
        if g in by_allele:
            acc, seq, how = *by_allele[g], "allele"
        elif g in by_family:
            acc, seq, how = *by_family[g], "gene_family"
        elif g in by_catalog:
            acc, seq, how = *by_catalog[g], "catalog_accession"
        else:
            rows.append((g, int(n), "unmatched", None, None, None)); continue
        rows.append((g, int(n), how, acc, len(seq), seq))
    d = pd.DataFrame(rows, columns=["gene", "isolates", "how", "accession", "length", "seq"])
    d.to_parquet(D / "gene_proteins.parquet")
    out = {"db_version": (D / "raw_ref" / "version.txt").read_text().strip(), "genes_seen": len(d),
           "by_match": d.how.value_counts().to_dict(),
           "isolate_share_matched": round(float(d.isolates[d.how != "unmatched"].sum() / d.isolates.sum()), 4),
           "unmatched_top": d[d.how == "unmatched"].nlargest(15, "isolates")[["gene", "isolates"]].to_dict("records")}
    (T / "proteins.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
