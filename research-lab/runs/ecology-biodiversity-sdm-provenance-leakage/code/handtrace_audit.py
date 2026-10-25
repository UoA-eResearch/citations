"""G3 hand trace of one audit unit: a Dutch source-cell test presence (seeded pick), traced from GBIF snapshot rows
to its H2 classification and its C1 status, recomputing the grid cell from coordinates independently of cells.py.
-> results/tables/handtrace_audit.json"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from pyproj import Transformer

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
from audit import B, T, W, csr, eval_cells, train_cells  # noqa: E402

import h5py  # noqa: E402
import hdf5plugin  # noqa: E402,F401

meta = pd.read_csv(RUN / "data" / "raw" / "eval_plot_metadata.csv", low_memory=False)
flags = pd.read_csv(T / "provenance_flags.csv")
core_keys = set(flags[flags.flag == "core"].datasetKey)
test = set(np.load(B / "test_indices.npy").tolist())
nl = sorted(set(meta[meta.Dataset == "Netherlands"].cell_row) & test)
rng = np.random.default_rng(20261026)
ec = eval_cells().set_index("ecell")
eptr, eidx = csr(B / "targets" / "eval_targets.h5")
with h5py.File(B / "range_masks_1km" / "eval_range_mask.h5") as h:
    cl, si = h["cumulative_lengths"][:], h["species_index"][:]
pairs = [(cc, int(sp)) for cc in nl for sp in eidx[eptr[cc]:eptr[cc + 1]] if int(sp) in set(si[cl[cc]:cl[cc + 1]].tolist())]
tr = Transformer.from_crs("EPSG:4326", "EPSG:6933", always_xy=True)
tc = train_cells()
tptr, tidx = csr(B / "targets" / "train_targets_1km.h5")


def trace(c, s):
    gx, gy = int(ec.loc[c, "gx"]), int(ec.loc[c, "gy"])
    core = pd.read_parquet(W / "core", filters=[("sp", "==", s), ("gx", "==", gx), ("gy", "==", gy)])
    x, y = tr.transform(core.decimallongitude.to_numpy(), core.decimallatitude.to_numpy())
    sup = pd.read_parquet(W / "support.parquet", filters=[("sp", "==", s), ("gx", "==", gx), ("gy", "==", gy)])
    tcell = tc[(tc.gx == gx) & (tc.gy == gy)].cell.tolist()
    po = pd.read_parquet(W / "prov_only.parquet", filters=[("sp", "==", s)])
    return {"eval_cell": int(c), "species": int(s), "grid_cell": [gx, gy], "core_records": int(len(core)),
            "core_datasets": sorted(set(core.datasetkey.str[:8])),
            "core_datasets_all_flagged": bool(core.datasetkey.isin(core_keys).all()) if len(core) else None,
            "recomputed_cells_match": bool((np.floor(x / 1000) == gx).all() and (np.floor(y / 1000) == gy).all()) if len(core) else None,
            "support_counts": sup[["n_core", "n_broad", "n_other"]].to_dict("records"),
            "h2_colocated": bool(len(core) > 0), "training_cell": tcell,
            "sage_training_presence": bool(any(s in set(tidx[tptr[t]:tptr[t + 1]].tolist()) for t in tcell)),
            "removed_by_C1": bool(po.cell.isin(tcell).any()),
            "expected_removed": bool(len(sup) and int(sup.n_core.iloc[0]) > 0 and int(sup.n_broad.iloc[0]) == 0
                                     and int(sup.n_other.iloc[0]) == 0)}


order = rng.permutation(len(pairs))
first = trace(*pairs[order[0]])
coloc = None
for i in order[1:200]:
    r = trace(*pairs[i])
    if r["h2_colocated"]:
        coloc = r
        break
out = {"random_pick": first, "first_colocated_in_same_order": coloc}
(T / "handtrace_audit.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
