"""Reviewer check 1: re-derive the panel rectangle from the Davis release + UniProt, independently.

Does NOT import code/panel.py. Re-implements the plan.md 4.1 / 5.1 rules from the prose and compares
the resulting rectangle with data/panel.json.
"""
import csv
import json
import pickle
import re
import sys
from pathlib import Path

import numpy as np

RUN = Path("/mnt/citations/research-lab/runs/cheminformatics-drug-discovery-cofold-selectivity")
DATA = RUN / "data"
CENSOR = 10000.0

Y = np.asarray(pickle.load(open(DATA / "davis_Y", "rb"), encoding="latin1"), float)
prot = list(json.load(open(DATA / "davis_proteins.txt")).items())
lig = list(json.load(open(DATA / "davis_ligands_iso.txt")).items())
uni_rows = list(csv.DictReader(open(DATA / "uniprot_kinases.tsv"), delimiter="\t"))
uni = {r["Sequence"]: r for r in uni_rows}

print(f"Y shape {Y.shape}; proteins {len(prot)}; ligands {len(lig)}; uniprot entries {len(uni_rows)}")
print(f"whole matrix uncensored share: {(Y < CENSOR).mean():.4f}  censored {(Y >= CENSOR).mean():.4f}")

# ---- rule 1: wild-type, non-phospho
step1 = [(j, n, s) for j, (n, s) in enumerate(prot) if "(" not in n and not n.endswith("p")]
print(f"\nrule 1 (no '(' and not ending 'p'): {len(step1)} of {len(prot)}")

# ---- rule 2: exact sequence match to a reviewed human UniProt entry
step2 = [(j, n, s) for j, n, s in step1 if s in uni]
print(f"rule 2 (exact UniProt sequence match): {len(step2)}")

# ---- rule 3: exactly one 'Protein kinase' domain, 220-350 aa
GROUPS = [("Tyr protein kinase family", "TK"), ("TKL Ser/Thr protein kinase family", "TKL"),
          ("STE Ser/Thr protein kinase family", "STE"), ("CK1 Ser/Thr protein kinase family", "CK1"),
          ("AGC Ser/Thr protein kinase family", "AGC"), ("CAMK Ser/Thr protein kinase family", "CAMK"),
          ("CMGC Ser/Thr protein kinase family", "CMGC")]


def group_of(sim):
    for pat, g in GROUPS:
        if pat in sim:
            return g
    return "OTHER"


step3 = []
n_multi = n_nodom = n_badlen = 0
for j, n, s in step2:
    hits = re.findall(r'DOMAIN (\d+)\.\.(\d+); /note="Protein kinase', uni[s]["Domain [FT]"])
    if len(hits) == 0:
        n_nodom += 1
        continue
    if len(hits) > 1:
        n_multi += 1
        continue
    a, b = int(hits[0][0]), int(hits[0][1])
    if not (220 <= b - a + 1 <= 350):
        n_badlen += 1
        continue
    cs, ce = max(1, a - 20), min(len(s), b + 20)
    step3.append(dict(davis_name=n, col=j, acc=uni[s]["Entry"], group=group_of(uni[s]["Sequence similarities"]),
                      n_unc=int((Y[:, j] < CENSOR).sum()), dom_start=a, dom_end=b,
                      crop_start=cs, crop_end=ce, crop_len=ce - cs + 1, full_len=len(s),
                      crop_seq=s[cs - 1:ce]))
print(f"rule 3 (one PK domain 220-350aa): {len(step3)}   "
      f"[excluded: no domain {n_nodom}, multi-domain {n_multi}, bad length {n_badlen}]")

# ---- rule 4: one Davis name per accession, more uncensored wins then alphabetical
best = {}
for r in sorted(step3, key=lambda r: (-r["n_unc"], r["davis_name"])):
    best.setdefault(r["acc"], r)
cands = sorted(best.values(), key=lambda r: (r["group"], -r["n_unc"], r["davis_name"]))
print(f"rule 4 (one name per accession): {len(cands)} candidate kinases")
counts = {}
for r in cands:
    counts[r["group"]] = counts.get(r["group"], 0) + 1
print("  per group:", dict(sorted(counts.items())))

# ---- largest remainder allocation, floor 1 per non-empty group
K = L = 32
gs = sorted(counts)
tot = sum(counts.values())
quota = {g: 1 + (K - len(gs)) * counts[g] / tot for g in gs}
alloc = {g: min(counts[g], int(np.floor(quota[g]))) for g in gs}
while sum(alloc.values()) < K:
    g = max((g for g in gs if alloc[g] < counts[g]), key=lambda g: (quota[g] - alloc[g], counts[g] - alloc[g], g))
    alloc[g] += 1
print(f"\nmy allocation:   {dict(sorted(alloc.items()))}  (sum {sum(alloc.values())})")
print("  exact quotas:", {g: round(quota[g], 3) for g in gs})

kin = []
for g in sorted(alloc):
    pool = [r for r in cands if r["group"] == g]
    kin += sorted(pool, key=lambda r: (-r["n_unc"], r["davis_name"]))[:alloc[g]]
kin = sorted(kin, key=lambda r: (r["group"], r["davis_name"]))
cols = [r["col"] for r in kin]

# ---- ligands
from rdkit import Chem  # noqa: E402
from rdkit.Chem import Descriptors  # noqa: E402
from rdkit import RDLogger  # noqa: E402
RDLogger.DisableLog("rdApp.*")

ligrows = []
nbad = nfrag = nmw = nunc = 0
for i, (cid, smi) in enumerate(lig):
    m = Chem.MolFromSmiles(smi)
    if m is None:
        nbad += 1
        continue
    if len(Chem.GetMolFrags(m)) != 1:
        nfrag += 1
        continue
    if Descriptors.MolWt(m) > 700:
        nmw += 1
        continue
    n = int((Y[i, cols] < CENSOR).sum())
    if n < 8:
        nunc += 1
        continue
    ligrows.append(dict(cid=cid, row=i, smiles=smi, n_unc_panel=n, mw=round(Descriptors.MolWt(m), 2)))
print(f"\nligand filter: {len(ligrows)} eligible of {len(lig)}  "
      f"[unparseable {nbad}, multi-fragment {nfrag}, MW>700 {nmw}, <8 uncensored {nunc}]")
ligs = sorted(sorted(ligrows, key=lambda r: (-r["n_unc_panel"], r["cid"]))[:L], key=lambda r: r["cid"])

# ---- compare with the study's panel
P = json.load(open(DATA / "panel.json"))
mine_k = [r["acc"] for r in kin]
theirs_k = [k["acc"] for k in P["kinases"]]
mine_l = [r["cid"] for r in ligs]
theirs_l = [c["cid"] for c in P["ligands"]]
print("\n==== comparison with data/panel.json ====")
print(f"candidate_count  mine {len(cands):4d}  theirs {P['candidate_count']}")
print(f"allocation       mine {dict(sorted(alloc.items()))}")
print(f"                 theirs {dict(sorted(P['allocation'].items()))}")
print(f"kinase set identical: {sorted(mine_k) == sorted(theirs_k)}  (order identical: {mine_k == theirs_k})")
if sorted(mine_k) != sorted(theirs_k):
    print("  only mine:", set(mine_k) - set(theirs_k), " only theirs:", set(theirs_k) - set(mine_k))
print(f"ligand set identical: {sorted(mine_l) == sorted(theirs_l)}")
if sorted(mine_l) != sorted(theirs_l):
    print("  only mine:", set(mine_l) - set(theirs_l), " only theirs:", set(theirs_l) - set(mine_l))

# crop check against UniProt annotation, all 32
print("\n==== crop check (kinase domain +/- 20, clipped) ====")
bad = 0
for k in P["kinases"]:
    seq = dict(prot)[k["davis_name"]]
    u = uni[seq]
    hits = re.findall(r'DOMAIN (\d+)\.\.(\d+); /note="Protein kinase', u["Domain [FT]"])
    a, b = int(hits[0][0]), int(hits[0][1])
    cs, ce = max(1, a - 20), min(len(seq), b + 20)
    ok = (cs == k["crop_start"] and ce == k["crop_end"] and ce - cs + 1 == k["crop_len"]
          and k["crop_seq"] == seq[cs - 1:ce] and u["Entry"] == k["acc"]
          and a == k["dom_start"] and b == k["dom_end"])
    if not ok:
        bad += 1
        print(f"  MISMATCH {k['davis_name']} mine {cs}-{ce} theirs {k['crop_start']}-{k['crop_end']}")
print(f"all 32 crops reproduce exactly: {bad == 0}")
dom_lens = [k["dom_end"] - k["dom_start"] + 1 for k in P["kinases"]]
print(f"domain lengths {min(dom_lens)}-{max(dom_lens)}; crop lengths "
      f"{min(k['crop_len'] for k in P['kinases'])}-{max(k['crop_len'] for k in P['kinases'])}")
print(f"full lengths {min(k['full_len'] for k in P['kinases'])}-{max(k['full_len'] for k in P['kinases'])}, "
      f"median {int(np.median([k['full_len'] for k in P['kinases']]))}")
print(f"median crop fraction of full length: "
      f"{np.median([k['crop_len'] / k['full_len'] for k in P['kinases']]):.3f}")

# ---- censoring arithmetic
rows_t = [c["row"] for c in P["ligands"]]
cols_t = [k["col"] for k in P["kinases"]]
sub = Y[np.ix_(rows_t, cols_t)]
print("\n==== censoring arithmetic ====")
print(f"rectangle uncensored: {(sub < CENSOR).mean():.4f}  censored: {(sub >= CENSOR).mean():.4f}")
print(f"whole matrix uncensored: {(Y < CENSOR).mean():.4f}  censored: {(Y >= CENSOR).mean():.4f}")
pl = (sub < CENSOR).sum(1)
print(f"per-ligand uncensored: min {pl.min()} median {int(np.median(pl))} max {pl.max()}")
print(f"per-kinase uncensored: min {(sub < CENSOR).sum(0).min()} median "
      f"{int(np.median((sub < CENSOR).sum(0)))} max {(sub < CENSOR).sum(0).max()}")
# the whole-panel figure the plan quotes
print(f"\nplan 3 says 69.6%% of ALL cells are at the ceiling: actual {(Y >= CENSOR).mean():.4f}")
print(f"plan 5.1 says rectangle is 72.9%% uncensored vs 30.4%% for the whole panel: "
      f"actual {(sub < CENSOR).mean():.4f} vs {(Y < CENSOR).mean():.4f}")
