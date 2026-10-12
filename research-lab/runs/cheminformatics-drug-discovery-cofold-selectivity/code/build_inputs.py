"""Turn the preregistered design (plan.md §5) into directories of Boltz-2 YAML inputs, one per complex.

  panel    §5.1  the 32 x 32 primary rectangle
  decoy    §5.2  the 32 ligands against 4 non-kinase proteins
  promisc  §5.5  8 further kinases (the least promiscuous eligible one per Manning group) x 32 ligands
  sampling §5.4  the 8 x 12 sub-rectangle, re-run with heavier affinity sampling (same YAMLs, new out dir)

Pair ids are "<protein-key>__<pubchem-cid>", so an output directory maps back to the design without a
side table. Protein keys are UniProt accessions (one Davis entry per accession by §4.1 rule 4).
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import boltzrun as B  # noqa: E402
from panel import CENSOR_NM, allocate, candidates, load  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
DECOY = {"P00918": (1, 260, "carbonic anhydrase 2"), "P07477": (24, 247, "trypsin-1 (mature chain)"),
         "P09211": (1, 210, "glutathione S-transferase P"), "P07900": (9, 236, "HSP90-alpha N-domain")}
SAMPLING_L, SAMPLING_K = 8, 12


def panel_spec():
    P = json.load(open(RUN / "data" / "panel.json"))
    lig = {c["cid"]: c["smiles"] for c in P["ligands"]}
    return [dict(pair_id=f"{k['acc']}__{cid}", protein=k["acc"], seq=k["crop_seq"], smiles=smi)
            for k in P["kinases"] for cid, smi in sorted(lig.items())]


def decoy_spec():
    P = json.load(open(RUN / "data" / "panel.json"))
    out = []
    for acc, (s, e, _) in DECOY.items():
        full = "".join(l.strip() for l in open(RUN / "data" / f"decoy_{acc}.fasta") if not l.startswith(">"))
        for c in P["ligands"]:
            out.append(dict(pair_id=f"{acc}_decoy__{c['cid']}", protein=f"{acc}_decoy",
                            seq=full[s - 1:e], smiles=c["smiles"]))
    return out


def promisc_kinases():
    """The least promiscuous eligible kinase per Manning group, with >= 5 uncensored cells among the
    panel ligands, excluding the kinases already in the rectangle."""
    Y, prot, lig, uni = load()
    P = json.load(open(RUN / "data" / "panel.json"))
    used = {k["acc"] for k in P["kinases"]}
    rows = [c["row"] for c in P["ligands"]]
    out = []
    for g in sorted({c["group"] for c in candidates(Y, prot, uni)}):
        pool = [c for c in candidates(Y, prot, uni) if c["group"] == g and c["acc"] not in used
                and (Y[np.ix_(rows, [c["col"]])] < CENSOR_NM).sum() >= 5]
        if pool:
            out.append(min(pool, key=lambda c: (c["n_unc"], c["davis_name"])))
    return out


def promisc_spec():
    P = json.load(open(RUN / "data" / "panel.json"))
    kin = promisc_kinases()
    json.dump(kin, open(RUN / "data" / "promisc_kinases.json", "w"), indent=1)
    print("promiscuity probe kinases:", [(k["davis_name"], k["group"], k["n_unc"]) for k in kin])
    return [dict(pair_id=f"{k['acc']}__{c['cid']}", protein=k["acc"], seq=k["crop_seq"], smiles=c["smiles"])
            for k in kin for c in P["ligands"]]


def sampling_subset():
    """The 8 ligands and 12 kinases of the rectangle with the most uncensored cells (ties -> name/cid)."""
    Y, prot, lig, uni = load()
    P = json.load(open(RUN / "data" / "panel.json"))
    rows = [c["row"] for c in P["ligands"]]
    cols = [k["col"] for k in P["kinases"]]
    sub = Y[np.ix_(rows, cols)] < CENSOR_NM
    kin = sorted(sorted(P["kinases"], key=lambda k: (-int(sub[:, cols.index(k["col"])].sum()),
                                                     k["davis_name"]))[:SAMPLING_K],
                 key=lambda k: k["davis_name"])
    lg = sorted(sorted(P["ligands"], key=lambda c: (-int(sub[rows.index(c["row"]), :].sum()), c["cid"]))
                [:SAMPLING_L], key=lambda c: c["cid"])
    return kin, lg


def sampling_spec():
    kin, lg = sampling_subset()
    json.dump(dict(kinases=[k["davis_name"] for k in kin], ligands=[c["cid"] for c in lg]),
              open(RUN / "data" / "sampling_subset.json", "w"), indent=1)
    print("sampling arm:", [k["davis_name"] for k in kin], [c["cid"] for c in lg])
    return [dict(pair_id=f"{k['acc']}__{c['cid']}", protein=k["acc"], seq=k["crop_seq"], smiles=c["smiles"])
            for k in kin for c in lg]


def main(arm):
    spec = dict(panel=panel_spec, decoy=decoy_spec, promisc=promisc_spec, sampling=sampling_spec)[arm]()
    d = RUN / "data" / f"inputs_{arm}"
    d.mkdir(parents=True, exist_ok=True)
    missing = sorted({c["protein"] for c in spec if not B.msa_path(c["protein"]).exists()})
    if missing:
        raise SystemExit(f"missing MSAs for {missing}")
    for c in spec:
        B.write_yaml(d, c["pair_id"], c["protein"], c["seq"], c["smiles"])
    print(f"{arm}: {len(spec)} complexes -> {d}")


if __name__ == "__main__":
    main(sys.argv[1])
