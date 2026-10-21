"""D4 sensitivity: the primary cohort without documents dated only by a Crossref self-update (whose date is the issue
date, not the retraction date), and Retraction Watch-dated documents alone. Writes results/tables/sensitivity_d4.json.
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402


def main():
    o = pd.read_csv(A.RUN / "results" / "overlay" / "retraction_overlay.csv.gz")
    d = A.frame()[["pmcid", "cluster"]]
    C = o[(o.stratum == "primary") & o.in_snapshot].merge(d, on="pmcid")
    C["unm"] = (~C.own_marker.fillna(False).astype(bool)).astype(float)
    C["noflag"] = (~C.sidecar_flag.fillna(False).astype(bool)).astype(float)
    out = {}
    for name, sub in (("all", C), ("without_crossref_self_update_dates", C[C.date_source != "crossref-self-update (issue date)"]),
                      ("retraction_watch_dated_only", C[C.date_source == "retraction-watch"])):
        out[name] = {"own_unmarked": A.boot(sub.cluster, sub.unm), "sidecar_flag_missing": A.boot(sub.cluster, sub.noflag)}
    json.dump(out, open(A.TAB / "sensitivity_d4.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
