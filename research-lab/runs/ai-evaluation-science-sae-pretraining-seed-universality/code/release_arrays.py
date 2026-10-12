"""Pack the per-latent arrays for release: per layer, one .npz with each pair's best-correlation arrays
(corr_a/corr_b, float16, NaN = not assessable), keyed `pair<id>_a` / `pair<id>_b`, and each SAE's firing counts on H,
keyed `fired_<model>_s<seed>`. Pair ids are those of results/tables/pairs_L*.csv. Decoder-cosine arrays are summarised
in the pair tables and not released."""
from pathlib import Path

import numpy as np

RUN = Path(__file__).resolve().parents[1]

for L in [4, 8]:
    md, out = RUN / "data" / "match" / f"L{L}", {}
    for f in sorted(md.glob("pair_*.npz")):
        z = np.load(f)
        i = f.stem.split("_")[1]
        out[f"pair{i}_a"], out[f"pair{i}_b"] = z["corr_a"], z["corr_b"]
    for f in sorted(md.glob("fired_*.npy")):
        out[f.stem] = np.load(f).astype(np.int32)
    np.savez_compressed(RUN / "results" / f"match_arrays_L{L}.npz", **out)
    print(L, len(out), (RUN / "results" / f"match_arrays_L{L}.npz").stat().st_size / 1e6, "MB")
