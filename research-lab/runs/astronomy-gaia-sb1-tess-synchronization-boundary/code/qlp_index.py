"""QLP light curves for the matched TIC IDs, from MAST's observation table queried in batches of TIC IDs (replacing the
per-sector QLP scripts in lc_index.py, which list every FFI star, about 25 GB of text over throttled connections).
Paths match the bulk scripts' layout (the dataURL after mast:HLSP/qlp/). Appends to data/lc_index.parquet.

  qlp_index.py -> data/lc_index.parquet (product "qlp" rows)
"""
import time
from pathlib import Path

import pandas as pd
from astroquery.mast import Observations

RUN = Path(__file__).resolve().parents[1]
D = RUN / "data"
tics = pd.read_parquet(D / "tic.parquet").tic.astype("int64").astype(str).tolist()
rows = []
for b in range(0, len(tics), 300):
    for attempt in range(5):
        try:
            o = Observations.query_criteria(provenance_name="QLP", target_name=tics[b:b + 300]).to_pandas(); break
        except Exception as e:
            print("retry", b, attempt, str(e)[:80], flush=True); time.sleep(30 * (attempt + 1))
    o = o[o.dataURL.astype(str).str.startswith("mast:HLSP/qlp/") & o.dataURL.astype(str).str.endswith("_llc.fits")]
    rows.append(pd.DataFrame({"tic": o.target_name.astype("int64"), "sector": o.sequence_number.astype(int), "product": "qlp",
                              "path": o.dataURL.str.replace("mast:HLSP/qlp/", "", regex=False),
                              "url": "https://mast.stsci.edu/api/v0.1/Download/file/?uri=" + o.dataURL}))
    if (b // 300) % 10 == 0:
        print(b + 300, "of", len(tics), sum(len(r) for r in rows), flush=True)
q = pd.concat(rows).drop_duplicates(["tic", "sector"])
ix = pd.read_parquet(D / "lc_index.parquet")
ix = pd.concat([ix[ix["product"] != "qlp"], q], ignore_index=True)
ix.to_parquet(D / "lc_index.parquet")
print(len(q), "QLP light curves for", q.tic.nunique(), "stars; index now", len(ix))
