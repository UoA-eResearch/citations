"""Species name -> genus and family, from the NCBI taxonomy dump (plan section 1).

  taxonomy.py -> data/taxonomy.parquet (species, taxid, genus, family), results/tables/taxonomy.json
"""
import json
import tarfile
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"


def main():
    with tarfile.open(D / "raw_ref" / "taxdump.tar.gz") as tf:
        names = {}
        for line in tf.extractfile("names.dmp"):
            f = [x.strip() for x in line.decode("utf-8", "replace").split("|")]
            if f[3] == "scientific name":
                names[int(f[0])] = f[1]
        nodes = {}
        for line in tf.extractfile("nodes.dmp"):
            f = [x.strip() for x in line.decode("utf-8", "replace").split("|")]
            nodes[int(f[0])] = (int(f[1]), f[2])
    by_name = {}
    for tid, nm in names.items():
        by_name.setdefault(nm, tid)                      # first (lowest) taxid for a name
    iso = pd.read_parquet(D / "isolates.parquet", columns=["species"])
    sp = sorted(iso.species.unique())
    rows = []
    for s in sp:
        tid = by_name.get(s)
        genus, family = s.split(" ")[0], None
        if tid:
            cur, seen = tid, 0
            while cur in nodes and seen < 40:
                parent, rank = nodes[cur]
                if rank == "family":
                    family = names.get(cur); break
                if parent == cur:
                    break
                cur, seen = parent, seen + 1
        rows.append((s, tid, genus, family))
    d = pd.DataFrame(rows, columns=["species", "taxid", "genus", "family"])
    d.to_parquet(D / "taxonomy.parquet")
    out = {"species": len(d), "with_taxid": int(d.taxid.notna().sum()), "with_family": int(d.family.notna().sum()),
           "genera": int(d.genus.nunique()), "families": int(d.family.nunique())}
    (T / "taxonomy.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
