"""D1 (2026-11-07): the first sample.parquet held Gaia source_ids rounded through float64, so 41 pairs of different
stars shared an ID and their light curves were stored together. This remaps the light-curve shards to the true IDs
(data/lc_v2/), drops the colliding IDs, and re-fetches those stars' light curves by position into
data/lc_v2/shard_fix.parquet. -> data/id_map.parquet"""
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
import fetch_lc as F  # noqa: E402

D = RUN / "data"
s = pd.read_parquet(D / "sample.parquet")
s["rounded"] = s.source_id.astype(np.float64).astype(np.int64)
assert set(s.rounded) == set(pd.read_parquet(D / "sample_v1_rounded_ids.parquet").source_id)
n = s.groupby("rounded").source_id.transform("size")
s["collision"] = n > 1
s[["source_id", "rounded", "collision"]].to_parquet(D / "id_map.parquet", index=False)
m = dict(zip(s[~s.collision].rounded, s[~s.collision].source_id))
coll = set(s[s.collision].rounded)
(D / "lc_v2").mkdir(exist_ok=True)
for f in sorted((D / "lc").glob("shard_*.parquet")):
    t = pd.read_parquet(f)
    t = t[~t.source_id.isin(coll)].copy()
    t["source_id"] = t.source_id.map(m)
    assert t.source_id.notna().all()
    t.to_parquet(D / "lc_v2" / f.name, index=False)
redo = s[s.collision]
with ThreadPoolExecutor(8) as ex:
    res = list(ex.map(F.one, redo.itertuples(index=False)))
frames = [x for _, x in res if x is not None and len(x)]
pd.concat(frames).to_parquet(D / "lc_v2" / "shard_fix.parquet", index=False)
print(len(coll), "colliding IDs,", len(redo), "stars re-fetched,", sum(1 for _, x in res if x is None), "failed,", len(frames), "with data")
