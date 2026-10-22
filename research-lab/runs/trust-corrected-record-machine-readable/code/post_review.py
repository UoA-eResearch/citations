"""D5: the headline after the review. Documents dated only by an Elsevier Crossref self-update (D4: the date is the
issue date, not a retraction date) move from the primary cohort to the undated stratum. H1-H3 with the preregistered
rules, the D3 own-marker share, and the residue (neither an own marker nor a sidecar flag), on the dated primary
cohort; the moved documents are counted with the undated stratum. Writes results/tables/primary_d5.json.
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402

SELF = "crossref-self-update (issue date)"


def main():
    d = A.frame()
    d = d[~d.notice_type]
    o = pd.read_csv(A.RUN / "results" / "overlay" / "retraction_overlay.csv.gz", usecols=["pmcid", "date_source", "own_marker"])
    d = d.merge(o, on="pmcid", how="left")
    prim = d[(d.stratum == "primary") & d.xml_present.fillna(False)]
    moved = prim[prim.date_source == SELF]
    C = prim[prim.date_source != SELF]
    own = C.own_marker.fillna(False).astype(bool)
    flag = C.sidecar_flag.fillna(False).astype(bool)
    h1 = A.boot(C.cluster, (~C.xml_marked).astype(float))
    Cj = C[C.json_present.fillna(False)]
    h2 = A.boot(Cj.cluster, Cj.sidecar_flag.astype(float))
    Ct = C[C.txt_present.fillna(False)]
    h3 = A.boot(Ct.cluster, Ct.xml_marked.astype(float) - Ct.txt_textual.fillna(False).astype(float))
    U = d[(d.stratum == "undated") & d.xml_present.fillna(False)]
    mown = moved.own_marker.fillna(False).astype(bool)
    mflag = moved.sidecar_flag.fillna(False).astype(bool)
    out = {"primary_cohort_dated": int(len(C)), "moved_to_undated": int(len(moved)),
           "H1_unmarked_share": h1, "H1": A.rule(h1, 0.50, above=True),
           "H2_sidecar_flag_share": h2, "H2": A.rule(h2, 0.90, above=False),
           "H3_xml_minus_txt": h3, "H3": A.rule(h3, 0.05, above=False),
           "own_unmarked_D3": A.boot(C.cluster, (~own).astype(float)),
           "residue_dated": int((~own & ~flag).sum()),
           "residue_dated_share": round(float((~own & ~flag).mean()), 4),
           "residue_moved_to_undated": int((~mown & ~mflag).sum()),
           "undated_stratum_after_d5": {"n": int(len(U) + len(moved)),
                                        "own_unmarked": round(float((~pd.concat([U.own_marker, moved.own_marker]).fillna(False).astype(bool)).mean()), 4)}}
    top = list(C.publisher_name.value_counts().head(8).index) + [x for x in ("Elsevier", "Springer") if x in set(C.publisher_name)]
    out["by_publisher"] = {pb: {"n": int((C.publisher_name == pb).sum()),
                                "own_unmarked": round(float((~own[C.publisher_name == pb]).mean()), 4),
                                "flag_missing": round(float((~flag[C.publisher_name == pb]).mean()), 4)} for pb in top}
    hind = C.publisher_name.str.contains("Hindawi", case=False)
    out["hindawi_vs_rest_own_unmarked"] = {"hindawi": A.boot(C[hind].cluster, (~own[hind]).astype(float)),
                                           "rest": A.boot(C[~hind].cluster, (~own[~hind]).astype(float))}
    json.dump(out, open(A.TAB / "primary_d5.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
