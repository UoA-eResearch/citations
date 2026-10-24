"""H3 addendum input (confirmation pass, D4): the host organisation of each sealed forward work, as recorded at
sealing, for the publisher-clustered bootstrap in 2029. Keyed by data/forecast/forward_wid_doi.csv; the score file is
not read. Writes data/forecast/forward_wid_host.csv (local) and prints its SHA-256 and counts.
"""
import glob
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
FC = RUN / "data" / "forecast"

if __name__ == "__main__":
    want = pd.read_csv(FC / "forward_wid_doi.csv", usecols=["wid"]).wid.to_numpy(np.int64)
    rows = []
    for p in sorted(glob.glob(str(RUN / "data" / "cohort_raw" / "*.npz"))):
        z = np.load(p)
        if "wid" not in z.files or len(z["wid"]) == 0:
            continue
        m = np.isin(z["year"], [2025, 2026])     # the cohort files hold only cohort works, so year picks the forward set
        if m.any():
            rows.append(pd.DataFrame({"wid": z["wid"].astype(np.int64)[m], "host": z["host"].astype(np.int64)[m]}))
    d = pd.concat(rows).drop_duplicates("wid").sort_values("wid")
    d = d[d.wid.isin(want)]
    assert len(d) == len(np.unique(want)), (len(d), len(want))
    out = FC / "forward_wid_host.csv"
    d.to_csv(out, index=False)
    print("works", len(d), "of", len(want), "with host", int((d.host > 0).sum()), "hosts", d.host[d.host > 0].nunique())
    print("sha256", hashlib.sha256(out.read_bytes()).hexdigest())
