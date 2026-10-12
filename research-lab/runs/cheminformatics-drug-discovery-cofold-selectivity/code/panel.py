"""Build the preregistered panel: which kinases and which ligands enter the rectangle.

Davis et al. 2011 (as packaged by DeepDTA) is a complete 68 ligand x 442 kinase Kd matrix: every cell is
measured, and non-binders are reported at the 10 uM assay ceiling (Kd = 10000 nM, pKd = 5). The lead's
hypothesis text has the two axes the wrong way round ("442 inhibitors x 72 kinases"); the data are 72
inhibitors profiled against 442 kinase assays, of which DeepDTA packages 68 inhibitors.

Kinase eligibility (preregistered):
  1. name contains no "(" and does not end in "p"   -> wild-type, non-phosphorylated entry;
  2. the Davis sequence matches a reviewed human UniProt sequence exactly;
  3. that entry has exactly one "Protein kinase" domain annotated, of length 220-350 aa;
  4. one Davis name per UniProt accession (keep the one with more uncensored cells, then alphabetical).
The model input is the kinase domain plus a 20-residue flank on each side (clipped to the sequence).
Kinases are stratified by the Manning group implied by UniProt's SIMILARITY annotation (TK, TKL, STE,
CK1, AGC, CAMK, CMGC, OTHER) and K of them are taken by largest-remainder allocation across groups
(floor of one per non-empty group), choosing within a group by uncensored-cell count then by name.

Ligand eligibility: RDKit-parseable isomeric SMILES, exactly one organic fragment, MW <= 700, and at
least MIN_UNC uncensored cells among the selected kinases. L ligands are taken by uncensored count then
by PubChem CID.

Writes results/tables/panel_kinases.csv, panel_ligands.csv and data/panel.json.
"""
import csv
import json
import pickle
import re
from pathlib import Path

import numpy as np

RUN = Path(__file__).resolve().parents[1]
DATA, TAB = RUN / "data", RUN / "results" / "tables"
K, L = 32, 32          # panel size, fixed in plan.md section 3 from the measured per-complex runtime
MIN_UNC = 8            # a ligand needs this many uncensored cells among the K kinases
FLANK = 20             # residues kept either side of the annotated kinase domain
CENSOR_NM = 10000.0    # Davis assay ceiling; cells at the ceiling are non-binders, pKd = 5

GROUPS = [("Tyr protein kinase family", "TK"), ("TKL Ser/Thr protein kinase family", "TKL"),
          ("STE Ser/Thr protein kinase family", "STE"), ("CK1 Ser/Thr protein kinase family", "CK1"),
          ("AGC Ser/Thr protein kinase family", "AGC"), ("CAMK Ser/Thr protein kinase family", "CAMK"),
          ("CMGC Ser/Thr protein kinase family", "CMGC")]


def pkd(nm):
    return 9.0 - np.log10(nm)


def group_of(similarity):
    for pat, g in GROUPS:
        if pat in similarity:
            return g
    return "OTHER"


def kinase_domain(dom_field):
    """Return (start, end) 1-based of the single annotated protein kinase domain, or None."""
    hits = re.findall(r'DOMAIN (\d+)\.\.(\d+); /note="Protein kinase', dom_field)
    if len(hits) != 1:
        return None
    return int(hits[0][0]), int(hits[0][1])


def load():
    Y = np.asarray(pickle.load(open(DATA / "davis_Y", "rb"), encoding="latin1"), float)  # (68, 442) nM
    prot = json.load(open(DATA / "davis_proteins.txt"))      # name -> sequence (442)
    lig = json.load(open(DATA / "davis_ligands_iso.txt"))     # PubChem CID -> isomeric SMILES (68)
    uni = {r["Sequence"]: r for r in csv.DictReader(open(DATA / "uniprot_kinases.tsv"), delimiter="\t")}
    return Y, list(prot.items()), list(lig.items()), uni


def candidates(Y, prot, uni):
    unc = Y < CENSOR_NM
    rows = []
    for j, (name, seq) in enumerate(prot):
        if "(" in name or name.endswith("p"):
            continue
        u = uni.get(seq)
        if u is None:
            continue
        dom = kinase_domain(u["Domain [FT]"])
        if dom is None or not (220 <= dom[1] - dom[0] + 1 <= 350):
            continue
        s, e = max(1, dom[0] - FLANK), min(len(seq), dom[1] + FLANK)
        rows.append(dict(davis_name=name, col=j, acc=u["Entry"], gene=u["Gene Names (primary)"],
                         group=group_of(u["Sequence similarities"]), n_unc=int(unc[:, j].sum()),
                         full_len=len(seq), dom_start=dom[0], dom_end=dom[1], crop_start=s, crop_end=e,
                         crop_len=e - s + 1, crop_seq=seq[s - 1:e]))
    best = {}
    for r in sorted(rows, key=lambda r: (-r["n_unc"], r["davis_name"])):
        best.setdefault(r["acc"], r)
    return sorted(best.values(), key=lambda r: (r["group"], -r["n_unc"], r["davis_name"]))


def allocate(cands, k):
    """Largest-remainder allocation of k slots across groups, floor of 1 for every non-empty group."""
    counts = {}
    for r in cands:
        counts[r["group"]] = counts.get(r["group"], 0) + 1
    gs = sorted(counts)
    tot = sum(counts.values())
    quota = {g: 1 + (k - len(gs)) * counts[g] / tot for g in gs}
    alloc = {g: min(counts[g], int(np.floor(quota[g]))) for g in gs}
    while sum(alloc.values()) < k:
        g = max(gs, key=lambda g: (quota[g] - alloc[g], counts[g] - alloc[g], g) if alloc[g] < counts[g]
                else (-9, -9, g))
        if alloc[g] >= counts[g]:
            break
        alloc[g] += 1
    return alloc


def pick_kinases(cands, k):
    alloc = allocate(cands, k)
    out = []
    for g in sorted(alloc):
        pool = [r for r in cands if r["group"] == g]
        out += sorted(pool, key=lambda r: (-r["n_unc"], r["davis_name"]))[:alloc[g]]
    return sorted(out, key=lambda r: (r["group"], r["davis_name"])), alloc


def pick_ligands(Y, lig, cols, l):
    from rdkit import Chem
    from rdkit.Chem import Descriptors
    unc = Y < CENSOR_NM
    rows = []
    for i, (cid, smi) in enumerate(lig):
        m = Chem.MolFromSmiles(smi)
        if m is None or len(Chem.GetMolFrags(m)) != 1 or Descriptors.MolWt(m) > 700:
            continue
        n = int(unc[i, cols].sum())
        if n < MIN_UNC:
            continue
        rows.append(dict(cid=cid, row=i, smiles=smi, n_unc_panel=n, mw=round(Descriptors.MolWt(m), 2),
                         n_unc_all=int(unc[i].sum())))
    return sorted(sorted(rows, key=lambda r: (-r["n_unc_panel"], r["cid"]))[:l], key=lambda r: r["cid"])


def main():
    Y, prot, lig, uni = load()
    cands = candidates(Y, prot, uni)
    print(f"candidate kinases: {len(cands)}")
    for g in sorted({r['group'] for r in cands}):
        print(f"  {g:6s} {sum(r['group'] == g for r in cands):3d}")
    kin, alloc = pick_kinases(cands, K)
    print("allocation:", alloc)
    cols = [r["col"] for r in kin]
    lg = pick_ligands(Y, lig, cols, L)
    print(f"kinases {len(kin)} (crop len {min(r['crop_len'] for r in kin)}-{max(r['crop_len'] for r in kin)}), "
          f"ligands {len(lg)}, complexes {len(kin) * len(lg)}")
    sub = Y[np.ix_([r['row'] for r in lg], cols)]
    print(f"uncensored cells in the rectangle: {(sub < CENSOR_NM).sum()} / {sub.size} "
          f"({(sub < CENSOR_NM).mean():.1%}); per-ligand uncensored: "
          f"min {(sub < CENSOR_NM).sum(1).min()} median {int(np.median((sub < CENSOR_NM).sum(1)))} "
          f"max {(sub < CENSOR_NM).sum(1).max()}")
    TAB.mkdir(parents=True, exist_ok=True)
    with open(TAB / "panel_kinases.csv", "w", newline="") as f:
        w = csv.DictWriter(f, [c for c in kin[0] if c != "crop_seq"])
        w.writeheader()
        for r in kin:
            w.writerow({c: v for c, v in r.items() if c != "crop_seq"})
    with open(TAB / "panel_ligands.csv", "w", newline="") as f:
        w = csv.DictWriter(f, list(lg[0]))
        w.writeheader()
        w.writerows(lg)
    json.dump(dict(K=K, L=L, MIN_UNC=MIN_UNC, FLANK=FLANK, kinases=kin, ligands=lg,
                   candidate_count=len(cands), allocation=alloc),
              open(DATA / "panel.json", "w"), indent=1)
    print("wrote", TAB / "panel_kinases.csv", TAB / "panel_ligands.csv", DATA / "panel.json")


if __name__ == "__main__":
    main()
