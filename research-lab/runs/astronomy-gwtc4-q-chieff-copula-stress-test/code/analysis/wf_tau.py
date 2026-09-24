#!/usr/bin/env python
"""D25: four-measure point-estimate tau of the real catalog for an alternative (single-waveform) sample table.
Usage: ../venv/bin/python analysis/wf_tau.py <sample_table.h5> <tag>"""
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("JAX_PLATFORMS", "cpu")
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))
import e2_tau as E  # noqa: E402
from io_utils import read_sample_table  # noqa: E402

table, tag = Path(sys.argv[1]), sys.argv[2]
E._init(str(HERE.parent / "config.yaml"), "full")
posts, _ = read_sample_table(table)
names = sorted(posts)
K, rng = 4000, np.random.default_rng(20260925)
arr = {c: np.empty((len(names), K)) for c in E.COLS + ("ln_prior",)}
for i, n in enumerate(names):
    d = posts[n]
    idx = rng.choice(len(d), K, replace=len(d) < K)
    for c in E.COLS + ("ln_prior",):
        arr[c][i] = d[c].values[idx]
row = E.catalog_stats(arr["mass_1"], arr["mass_ratio"], arr["chi_eff"], arr["redshift"], arr["ln_prior"], arr["ln_prior"],
                      dict(kind="real", tag=tag))
out = {k: v for k, v in row.items() if k.startswith(("tau_", "frac_"))}
json.dump(out, open(E._G["cfg"].path("tables_dir") / f"wf_tau_full_{tag}.json", "w"), indent=2)
print(tag, " ".join(f"tau_{M}={row[f'tau_{M}']:+.3f}" for M in E.MEASURES))
