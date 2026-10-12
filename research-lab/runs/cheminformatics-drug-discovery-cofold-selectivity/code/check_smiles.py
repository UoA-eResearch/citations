"""Data-integrity check on the DeepDTA packaging of the Davis ligands (plan.md §3.4).

DAVIS-complete (arXiv 2512.00708) reports ligand-structure errors in circulating copies of Davis, so the
68 isomeric SMILES are re-fetched from PubChem by CID and compared by InChIKey (full key and the
connectivity-only first block). Writes results/tables/smiles_check.csv.
"""
import csv
import json
import time
from pathlib import Path
from urllib.request import urlopen

from rdkit import Chem
from rdkit import RDLogger

RDLogger.DisableLog("rdApp.*")
RUN = Path(__file__).resolve().parents[1]
URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{}/property/SMILES,ConnectivitySMILES/JSON"


def key(smi):
    m = Chem.MolFromSmiles(smi) if smi else None
    return Chem.MolToInchiKey(m) if m else ""


def main():
    lig = json.load(open(RUN / "data" / "davis_ligands_iso.txt"))
    rows = []
    for i, (cid, smi) in enumerate(sorted(lig.items()), 1):
        pub = ""
        for attempt in range(3):
            try:
                d = json.load(urlopen(URL.format(cid), timeout=60))["PropertyTable"]["Properties"][0]
                pub = d.get("SMILES") or d.get("ConnectivitySMILES") or ""
                break
            except Exception as e:  # noqa: BLE001
                print(f"  {cid} attempt {attempt + 1}: {type(e).__name__}", flush=True)
                time.sleep(5)
        a, b = key(smi), key(pub)
        rows.append(dict(cid=cid, deepdta_smiles=smi, pubchem_smiles=pub, inchikey_deepdta=a,
                         inchikey_pubchem=b, same_full=a == b and a != "",
                         same_skeleton=a[:14] == b[:14] and a != ""))
        print(f"[{i}/{len(lig)}] {cid} full={rows[-1]['same_full']} skeleton={rows[-1]['same_skeleton']}",
              flush=True)
        time.sleep(0.25)
    out = RUN / "results" / "tables" / "smiles_check.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    n_full = sum(r["same_full"] for r in rows)
    n_skel = sum(r["same_skeleton"] for r in rows)
    print(f"{n_full}/{len(rows)} identical InChIKey, {n_skel}/{len(rows)} identical skeleton -> {out}")


if __name__ == "__main__":
    main()
