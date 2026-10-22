"""Confirmation pass (review/confirmation.md), PMC arm: finding 4 of review/review.md and the cohort-mixing check.

1. Rerun the committed code/post_review.py into a scratch directory and compare with results/tables/primary_d5.json.
2. Recompute the D5 headline independently: cohort.parquet + parsed.parquet + documents_d3.csv.gz + the overlay's
   date_source, an index-resampling cluster bootstrap with a different seed (as in tables_check.py): H1-H3, the D3
   own-marker share, the residue, the moved documents, the undated stratum after D5, the publisher table, Hindawi vs
   rest; the recent stratum's self-update documents; the preregistered-cohort figures the report still quotes.

Run: venv/bin/python -I confirm_primary.py > confirm_primary.log
Identifiers, counts and shares only.
"""
import contextlib
import io
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RUN = HERE.parents[1]
T = RUN / "results" / "tables"
sys.path.insert(0, str(RUN / "code"))
import analysis as A  # noqa: E402
import post_review as PR  # noqa: E402

SELF = "crossref-self-update (issue date)"


def boot(cluster, k, seed=1, B=2000):
    df = pd.DataFrame({"c": cluster, "k": k, "n": 1.0})
    g = df.groupby("c")[["k", "n"]].sum()
    K, N = g.k.to_numpy(float), g.n.to_numpy(float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(g), size=(B, len(g)))
    bs = K[idx].sum(1) / N[idx].sum(1)
    return (round(float(K.sum() / N.sum()), 4),
            [round(float(np.percentile(bs, 2.5)), 4), round(float(np.percentile(bs, 97.5)), 4)], len(g))


def main():
    # ---- 1. rerun post_review.py into scratch
    tmp = Path(tempfile.mkdtemp(prefix="confirm_d5_primary_"))
    A.TAB = tmp
    with contextlib.redirect_stdout(io.StringIO()):
        PR.main()
    ja, jb = json.load(open(tmp / "primary_d5.json")), json.load(open(T / "primary_d5.json"))
    print("1. rerun of post_review.py: primary_d5.json rerun == committed:", ja == jb)
    if ja != jb:
        for k in jb:
            if ja.get(k) != jb.get(k):
                print("   differing key:", k, ja.get(k), jb.get(k))

    # ---- 2. independent recomputation
    c = pd.read_parquet(RUN / "data" / "cohort.parquet")
    p = pd.read_parquet(RUN / "data" / "parsed.parquet")
    d3 = pd.read_csv(T / "documents_d3.csv.gz")
    ov = pd.read_csv(RUN / "results" / "overlay" / "retraction_overlay.csv.gz", usecols=["pmcid", "date_source", "own_marker"])
    d = c.merge(p, on="pmcid", how="inner")
    d = d[~d.article_type.fillna("").str.lower().eq("retraction")]
    d["cluster"] = d.issn.fillna(d.journal).fillna("doc:" + d.pmcid)
    d["xml_marked"] = d.xml_structured.fillna(False) | d.xml_textual.fillna(False)
    d = d.merge(d3, on="pmcid", how="left").merge(ov, on="pmcid", how="left")
    d["own"] = (d.own_structured | d.own_textual | d.withdrawal).fillna(False).astype(bool)
    d["flag"] = d.sidecar_flag.fillna(False).astype(bool)
    prim = d[(d.stratum == "primary") & d.xml_present.fillna(False)]
    # documents_d3.csv.gz covers the 18,061 primary documents only; the overlay's own_marker covers every stratum
    print("   d3 coverage by stratum:", d[d.pmcid.isin(set(d3.pmcid))].stratum.value_counts().to_dict())
    print("   own (d3 columns) == overlay own_marker on every primary document:",
          bool((prim.own == prim.own_marker.fillna(False).astype(bool)).all()))
    moved = prim[prim.date_source == SELF]
    C = prim[prim.date_source != SELF]
    print("\n2. independent recomputation on the D5 cohort")
    print("   primary as preregistered", len(prim), "; moved (self-update dated)", len(moved), "; D5 cohort", len(C),
          "; clusters", C.cluster.nunique())
    print("   H1 unmarked (prereg detector):", boot(C.cluster, (~C.xml_marked).astype(float)), " reported", jb["H1_unmarked_share"])
    Cj = C[C.json_present.fillna(False)]
    print("   H2 sidecar flag:", boot(Cj.cluster, Cj.sidecar_flag.astype(float)), " reported", jb["H2_sidecar_flag_share"])
    Ct = C[C.txt_present.fillna(False)]
    print("   H3 xml - txt:", boot(Ct.cluster, Ct.xml_marked.astype(float) - Ct.txt_textual.fillna(False).astype(float)),
          " reported", jb["H3_xml_minus_txt"])
    print("   D3 own unmarked:", boot(C.cluster, (~C.own).astype(float)), " reported", jb["own_unmarked_D3"])
    print("   residue (no own marker, no flag) in the D5 cohort:", int((~C.own & ~C.flag).sum()), "share",
          round(float((~C.own & ~C.flag).mean()), 4), " reported", jb["residue_dated"], jb["residue_dated_share"])
    print("   residue among the moved 412:", int((~moved.own & ~moved.flag).sum()), " reported", jb["residue_moved_to_undated"])
    print("   moved: own-unmarked share", round(float((~moved.own).mean()), 4), "; publishers",
          moved.publisher.fillna(moved.xml_publisher).fillna("unknown").value_counts().head(4).to_dict())
    U = d[(d.stratum == "undated") & d.xml_present.fillna(False)]
    uo, mo = U.own_marker.fillna(False).astype(bool), moved.own_marker.fillna(False).astype(bool)
    print("   undated stratum parsed:", len(U), "own-unmarked (overlay own_marker)", int((~uo).sum()),
          "; + moved =", len(U) + len(moved), "with", int((~mo).sum()), "own-unmarked; share after D5:",
          round(float((int((~uo).sum()) + int((~mo).sum())) / (len(U) + len(moved))), 4), " reported", jb["undated_stratum_after_d5"])
    R = d[(d.stratum == "recent") & d.xml_present.fillna(False)]
    print("   recent (latency) stratum parsed:", len(R), "; of which self-update dated:", int((R.date_source == SELF).sum()),
          "(not moved by post_review.py; report says 1,106)")
    # publisher table
    pub = C.publisher.fillna(C.xml_publisher).fillna("unknown")
    rows = {}
    for pb in ("Hindawi", "Wiley", "PLoS", "Elsevier - Cell Press", "Springer - Nature Publishing Group", "Elsevier", "Springer"):
        s = pub == pb
        rows[pb] = (int(s.sum()), round(float((~C.own[s]).mean()), 4), round(float((~C.flag[s]).mean()), 4))
    print("   publisher table (n, own-unmarked, flag-missing):", rows)
    print("   reported:", {k: (v["n"], v["own_unmarked"], v["flag_missing"]) for k, v in jb["by_publisher"].items() if k in rows})
    hind = pub.str.contains("Hindawi", case=False)
    print("   Hindawi own-unmarked:", boot(C.cluster[hind], (~C.own[hind]).astype(float)), " rest:",
          boot(C.cluster[~hind], (~C.own[~hind]).astype(float)))
    print("   reported:", jb["hindawi_vs_rest_own_unmarked"])
    # the report's plain-terms numbers
    print("   marked in the file itself (1 - H1):", round(1 - float((~C.xml_marked).mean()), 4),
          "; own marker (1 - D3):", round(1 - float((~C.own).mean()), 4))
    # ---- 3. preregistered-cohort figures the report still quotes (18,061)
    print("\n3. preregistered-cohort figures still quoted")
    print("   contamination: D3 own-unmarked on 18,061:", round(float((~prim.own).mean()), 4),
          "; D5 cohort:", round(float((~C.own).mean()), 4))
    print("   date-source strata (prereg cohort, D3 own-unmarked):",
          prim.groupby("date_source").own.agg(lambda s: round(1 - s.mean(), 4)).to_dict(),
          prim.date_source.value_counts().to_dict())
    print("   manuscripts in prereg cohort:", int(prim.is_manuscript.fillna(False).sum()),
          "; in D5 cohort:", int(C.is_manuscript.fillna(False).sum()),
          "; D5 unmarked prereg-detector manuscripts vs rest:",
          round(float((~C[C.is_manuscript.fillna(False)].xml_marked).mean()), 4),
          round(float((~C[~C.is_manuscript.fillna(False)].xml_marked).mean()), 4))
    rel = prim.own_kinds.fillna("").str.contains("related-article")
    print("   related-article (own, D3) share: prereg", round(float(rel.mean()), 4),
          "; D5 cohort", round(float(C.own_kinds.fillna("").str.contains("related-article").mean()), 4))
    tp = prim.xml_kinds.fillna("").str.contains("title-prefix")
    st = prim.xml_kinds.fillna("").str.contains("statement")
    print("   title-prefix share prereg", round(float(tp.mean()), 4), "; statement", round(float(st.mean()), 4),
          "; textual-only", round(float((prim.xml_textual.fillna(False) & ~prim.xml_structured.fillna(False)).mean()), 4),
          "; XML marker without flag", int((prim.xml_marked & ~prim.flag).sum()))
    print("   same on the D5 cohort: title-prefix", round(float(C.xml_kinds.fillna("").str.contains("title-prefix").mean()), 4),
          "; statement", round(float(C.xml_kinds.fillna("").str.contains("statement").mean()), 4),
          "; textual-only", round(float((C.xml_textual.fillna(False) & ~C.xml_structured.fillna(False)).mean()), 4),
          "; XML marker without flag", int((C.xml_marked & ~C.flag).sum()))
    print("\nscratch dir:", tmp)


if __name__ == "__main__":
    main()
