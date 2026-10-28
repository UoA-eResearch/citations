"""POST HOC (after the corrected primary run): Auckland, the region that motivated the lead, has no gauge meeting the
preregistered inclusion rule (8 complete, resolved out-of-sample years; G1 moves Auckland's start to 2018/19, leaving
exactly 8, and Auckland's 2021/22-2022/23 data are mostly graded 2xx). This reports Auckland with unverified data kept
(S3) and relaxed minimum years, labelled exploratory. Uses analyse.py's functions unchanged.

  posthoc_auckland.py -> results/tables/posthoc_auckland.json
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyse as A  # noqa: E402


def main():
    M, H, S = A.load()
    g = A.gauge_meta(H, S)
    m6 = A.qualify(M, 6, "primary")
    g, _ = A.dedupe(g, m6[m6.ok].groupby("file").size())
    out = {}
    for variant in ("primary", "S3"):
        for k in (8, 7, 6):
            A.MIN_OOS = k
            r, x = A.run(M, H, g, rng=np.random.default_rng(A.SEED + 500 + k), variant=variant, servers=["Auckland"])
            out[f"{variant}_min{k}"] = r
    A.MIN_OOS = 8
    (A.T / "posthoc_auckland.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    print(json.dumps({k: (v.get("OE"), v.get("ci"), v.get("gauges"), v.get("O"), v.get("E")) for k, v in out.items()}, indent=0))


if __name__ == "__main__":
    main()
