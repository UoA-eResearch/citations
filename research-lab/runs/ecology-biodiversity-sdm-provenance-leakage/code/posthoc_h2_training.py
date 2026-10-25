"""POST HOC (written after the G3 hand trace found a co-located Dutch presence whose cell has no SAGE training cell):
H2 counts flagged *snapshot* records in the test cell, not SAGE training presences, so it is an upper bound. This
script splits source-cell test presences into: (a) a flagged snapshot record in the cell (H2 as run); (b) the same,
and SAGE's training targets hold that species in that cell; (c) SAGE holds that species in that cell at all, from
any source (the same-cell overlap SAGE accepts by design); (d) (b) and the presence is provenance-only (removed by C1).
-> results/tables/posthoc_h2_training.json
"""
import json
import sys
from pathlib import Path

import h5py
import hdf5plugin  # noqa: F401
import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
from audit import B, T, W, csr, eval_cells, train_cells  # noqa: E402

meta = pd.read_csv(RUN / "data" / "raw" / "eval_plot_metadata.csv", low_memory=False)
flags = pd.read_csv(T / "provenance_flags.csv")
core_src = set(flags[flags.flag == "core"].givd_source)
test = set(np.load(B / "test_indices.npy").tolist())
src_cells = set(meta[meta.GIVD_ID.isin(core_src)].cell_row) & test
eptr, eidx = csr(B / "targets" / "eval_targets.h5")
with h5py.File(B / "range_masks_1km" / "eval_range_mask.h5") as h:
    cl, si = h["cumulative_lengths"][:], h["species_index"][:]
rows = []
for c in sorted(src_cells):
    inrange = set(si[cl[c]:cl[c + 1]].tolist())
    rows += [(c, int(s)) for s in eidx[eptr[c]:eptr[c + 1]] if int(s) in inrange]
tp = pd.DataFrame(rows, columns=["ecell", "sp"]).merge(eval_cells(), on="ecell")
sup = pd.read_parquet(W / "support.parquet")
tp = tp.merge(sup[["sp", "gx", "gy", "n_core"]], on=["sp", "gx", "gy"], how="left")
tp["a"] = tp.n_core.fillna(0) > 0
tc = train_cells()
tptr, tidx = csr(B / "targets" / "train_targets_1km.h5")
tp = tp.merge(tc, on=["gx", "gy"], how="left")
has = []
for cell, s in zip(tp.cell.to_numpy(), tp.sp.to_numpy()):
    has.append(bool(cell == cell) and int(s) in set(tidx[tptr[int(cell)]:tptr[int(cell) + 1]].tolist()))
tp["c"] = has
tp["b"] = tp.a & tp.c
po = pd.read_parquet(W / "prov_only.parquet")
po["po"] = True
tp = tp.merge(po, on=["sp", "cell"], how="left")
tp["d"] = tp.po.fillna(False).astype(bool) & tp.b
cs = meta[meta.cell_row.isin(src_cells) & meta.GIVD_ID.isin(core_src)][["cell_row", "Dataset"]].drop_duplicates()


def shares(g):
    return {"presences": int(len(g)), "a_flagged_snapshot_record": round(float(g.a.mean()), 4),
            "b_and_sage_training_presence": round(float(g.b.mean()), 4),
            "c_sage_training_presence_any_source": round(float(g.c.mean()), 4),
            "d_b_and_provenance_only": round(float(g.d.mean()), 4)}


out = {"all": shares(tp), "by_source_db": {k: shares(g) for k, g in tp.merge(cs, left_on="ecell", right_on="cell_row").groupby("Dataset")}}
(T / "posthoc_h2_training.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
