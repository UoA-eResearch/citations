"""Post hoc (D4): H1 and H2 with every flagged figure mismatch (all 47 cells) replaced by the blind human label.
Inputs: the labels (data/interim/blind/labels*.json) and the comparator keys (kept outside the labeller's directory,
path given as argv[1]). -> results/tables/posthoc_figures_human.json"""
import json
import sys
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
import compare as K  # noqa: E402

keydir = Path(sys.argv[1])
B = K.D / "interim" / "blind"
keys = pd.DataFrame(json.loads((keydir / "key.json").read_text()) + json.loads((keydir / "key2.json").read_text()))
labs = pd.DataFrame(json.loads((B / "labels.json").read_text()) + json.loads((B / "labels2.json").read_text()))
M = keys.merge(labs, on="pair")
fig = M[M.stratum.str.startswith("figure_mismatch")]
same = {(a, int(c)) for a, c, l in zip(fig.nbid, fig.cell, fig.label) if l == "same"}
C = pd.read_parquet(K.D / "interim" / "cells.parquet")
C["mismatch_h"] = [m and (a, int(c)) not in same for a, c, m in zip(C.nbid, C.cell, C.mismatch)]
C["intrinsic_h"] = C.mismatch_h & (C.varies | C.envelope)
N = pd.read_csv(K.TAB / "notebooks.csv")
comp = N[N.reps_ok].nbid
g = C[C.nbid.isin(comp)].groupby("nbid")
nb = pd.DataFrame({"exact": g.mismatch_h.any(),
                   "all_intr": g.apply(lambda d: d.mismatch_h.any() and d[d.mismatch_h].intrinsic_h.all()),
                   "na_fail": g.apply(lambda d: (d.mismatch_h & ~d.intrinsic_h).any())}).reindex(comp, fill_value=False)
k, n = int(nb.all_intr.sum()), int(nb.exact.sum())
fe, fn = nb.exact.mean(), nb.na_fail.mean()
out = {"figure_mismatch_cells": int(len(fig)), "judged_same": len(same), "judged_different": int((fig.label == "different").sum()),
       "notebooks": int(len(nb)), "masked_mismatch": n, "all_intrinsic": k, "H1_share": round(k / n, 4) if n else None,
       "H1_wilson": K.wilson(k, n), "noise_aware_fail": int(nb.na_fail.sum()),
       "overstatement": round(float(fe / fn), 4) if fn else None}
(K.TAB / "posthoc_figures_human.json").write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps(out, indent=1))
