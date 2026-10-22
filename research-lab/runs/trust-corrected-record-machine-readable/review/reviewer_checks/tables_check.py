"""Reviewer check: recompute the reported numbers from the study's own intermediate tables, with an independent
cluster bootstrap; cluster-key diagnostics; D2 (last-modified vs retraction date); sidecar flag vs text header per
document; date-source strata; latency; manuscripts; SHA-256 spot check. Prints everything.
Run: venv/bin/python -I tables_check.py
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RUN = HERE.parents[1]
T = RUN / "results" / "tables"
S, CUT = pd.Timestamp("2026-10-21"), pd.Timestamp("2026-04-24")


def boot(cluster, k, seed=1, B=2000):
    df = pd.DataFrame({"c": cluster, "k": k, "n": 1.0})
    g = df.groupby("c")[["k", "n"]].sum()
    K, N = g.k.to_numpy(float), g.n.to_numpy(float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(g), size=(B, len(g)))     # resample clusters with replacement, index form
    bs = K[idx].sum(1) / N[idx].sum(1)
    return round(float(K.sum() / N.sum()), 4), [round(float(np.percentile(bs, 2.5)), 4), round(float(np.percentile(bs, 97.5)), 4)], len(g)


def main():
    c = pd.read_parquet(RUN / "data" / "cohort.parquet")
    p = pd.read_parquet(RUN / "data" / "parsed.parquet")
    d3 = pd.read_csv(T / "documents_d3.csv.gz")
    ov = pd.read_csv(RUN / "results" / "overlay" / "retraction_overlay.csv.gz", parse_dates=["date"])
    snap = pd.read_parquet(RUN / "data" / "snapshot" / "latest_versions.parquet")
    d = c.merge(p, on="pmcid", how="inner")
    d["notice_type"] = d.article_type.fillna("").str.lower().eq("retraction")
    print("parsed", len(d), "notice-type", int(d.notice_type.sum()))
    d = d[~d.notice_type]
    d["cluster"] = d.issn.fillna(d.journal).fillna("doc:" + d.pmcid)
    d["xml_marked"] = d.xml_structured.fillna(False) | d.xml_textual.fillna(False)
    C = d[(d.stratum == "primary") & d.xml_present.fillna(False)].copy()
    print("primary n", len(C))
    print("180-day check: S - CUT =", (S - CUT).days, "days; max primary date", C.date.max(), "min recent date",
          d[d.stratum == "recent"].date.min())
    # independent bootstrap
    print("H1 unmarked (prereg detector):", boot(C.cluster, (~C.xml_marked).astype(float)))
    print("H2 sidecar:", boot(C.cluster, C.sidecar_flag.fillna(False).astype(float)))
    print("H3 xml - txt:", boot(C.cluster, C.xml_marked.astype(float) - C.txt_textual.fillna(False).astype(float)))
    C = C.merge(d3, on="pmcid", how="left")
    C["own"] = C.own_structured | C.own_textual | C.withdrawal
    print("H1 own+wd unmarked:", boot(C.cluster, (~C.own).astype(float)))
    # cluster-key diagnostics
    print("\n--- cluster key")
    print("issn null:", int(C.issn.isna().sum()), "journal null too (doc: clusters):", int((C.issn.isna() & C.journal.isna()).sum()))
    jn = C[C.issn.notna() & C.journal.notna()].groupby("journal").issn.nunique()
    print("RW journal names with >1 ISSN cluster:", int((jn > 1).sum()), "of", len(jn), "; docs in them:",
          int(C[C.journal.isin(jn[jn > 1].index)].shape[0]))
    ij = C[C.issn.notna() & C.journal.notna()].groupby("issn").journal.nunique()
    print("ISSNs with >1 RW journal name:", int((ij > 1).sum()), "of", len(ij))
    mixed = C[C.issn.isna() & C.journal.notna()].journal
    print("docs clustered by journal NAME whose journal also has ISSN-keyed docs:",
          int(mixed.isin(C[C.issn.notna()].journal.dropna()).sum()))
    sizes = C.cluster.value_counts()
    print("largest clusters:", sizes.head(5).to_dict(), "; singletons:", int((sizes == 1).sum()))
    # alternative key: RW journal name first, then ISSN
    C["cluster2"] = C.journal.fillna(C.issn).fillna("doc:" + C.pmcid)
    print("H1 own+wd unmarked, journal-name-first key:", boot(C.cluster2, (~C.own).astype(float)))
    pubc = C.publisher.fillna(C.xml_publisher).fillna("unknown")
    print("H1 own+wd unmarked, PUBLISHER clusters:", boot(pubc, (~C.own).astype(float)))
    # D2
    print("\n--- D2 last-modified vs retraction date (primary)")
    lm = C.merge(snap[["pmcid", "last_modified"]], on="pmcid")
    lm["lm"] = pd.to_datetime(lm.last_modified, utc=True).dt.tz_localize(None)
    print("last_modified after retraction date:", int((lm.lm > lm.date).sum()), "of", len(lm))
    print("last_modified by month:", lm.lm.dt.to_period("M").value_counts().sort_index().to_dict())
    print("inventory last_modified after S (2026-10-21):", int((lm.lm > S).sum()))
    print("version in primary:", C.version.value_counts().to_dict())
    print("version 319 docs:", C[C.version == 319][["pmcid", "doi", "date"]].to_dict("records"))
    # sidecar flag vs text header
    print("\n--- sidecar flag vs txt header, per document")
    print(pd.crosstab(C.sidecar_flag.fillna(False), C.txt_header.fillna(False)))
    print("flag set but own-unmarked:", int((C.sidecar_flag.fillna(False) & ~C.own).sum()))
    print("own-unmarked & no flag:", int((~C.own & ~C.sidecar_flag.fillna(False)).sum()))
    # date source
    print("\n--- date source (overlay, primary in snapshot)")
    O = ov[(ov.stratum == "primary") & ov.in_snapshot]
    g = O.groupby("date_source").agg(n=("pmcid", "size"), unmarked=("own_marker", lambda s: round(1 - s.mean(), 4)),
                                    noflag=("sidecar_flag", lambda s: round(1 - s.fillna(False).astype(bool).mean(), 4)))
    print(g)
    print("unmarked residue by date source (count):", O[~O.own_marker].date_source.value_counts().to_dict())
    print("self-update docs: publishers:", C[C.pmcid.isin(O[O.date_source.str.startswith("crossref-self")].pmcid)]
          .publisher.fillna(C.xml_publisher).fillna("unknown").value_counts().head(8).to_dict())
    print("self-update docs: date (=issue date) by year:",
          O[O.date_source.str.startswith("crossref-self")].date.dt.year.value_counts().sort_index().to_dict())
    R = ov[(ov.stratum == "recent") & ov.in_snapshot]
    print("recent stratum by date source:", R.date_source.value_counts().to_dict())
    # latency with own marker
    R = R.copy()
    R["m"] = ((S - R.date).dt.days // 30).clip(0, 5)
    print("\n--- latency (own marker / flag) by month:")
    print(R.groupby("m").agg(n=("pmcid", "size"), own=("own_marker", "mean"), flag=("sidecar_flag", lambda s: s.fillna(False).astype(bool).mean())).round(4))
    # manuscripts
    print("\n--- manuscripts")
    print("is_manuscript:", int(C.is_manuscript.fillna(False).sum()),
          "unmarked prereg:", round(float((~C[C.is_manuscript.fillna(False)].xml_marked).mean()), 4),
          "unmarked own:", round(float((~C[C.is_manuscript.fillna(False)].own).mean()), 4),
          "non-manuscript unmarked prereg:", round(float((~C[~C.is_manuscript.fillna(False)].xml_marked).mean()), 4),
          "own:", round(float((~C[~C.is_manuscript.fillna(False)].own).mean()), 4))
    # notice_id kept
    print("\n--- D1: documents flagged as notices by identifier but kept as curated originals")
    k = d[d.notice_id & ~d.notice]
    print("kept, parsed:", len(k), "by stratum:", k.stratum.value_counts().to_dict())
    print("article types:", k.article_type.fillna("").value_counts().head(10).to_dict())
    print("primary kept: n", int((k.stratum == "primary").sum()), "unmarked prereg:",
          round(float((~k[k.stratum == "primary"].xml_marked).mean()), 4) if (k.stratum == "primary").any() else None)
    # article types across the primary cohort
    print("\n--- article types in primary cohort:", C.article_type.fillna("").value_counts().head(12).to_dict())
    # textual-only
    to = C[C.xml_textual.fillna(False) & ~C.xml_structured.fillna(False)]
    print("textual-only (prereg):", len(to), "kinds:", to.xml_kinds.value_counts().head(8).to_dict())
    print("textual-only, own detector:", int((C.own_textual & ~C.own_structured).sum()))
    # sha spot check
    print("\n--- SHA-256 spot check (30 random files)")
    sha = pd.read_csv(T / "snapshot_files_sha256.csv.gz")
    smp = sha.sample(30, random_state=7)
    bad = 0
    for f, h in zip(smp.file, smp.sha256):
        if hashlib.sha256((RUN / "data" / "files" / f).read_bytes()).hexdigest() != h:
            bad += 1
    print("mismatches:", bad, "of", len(smp), "; table rows", len(sha), "; files on disk", len(list((RUN / "data" / "files").iterdir())))
    # overlay counts
    print("\n--- overlay")
    print("rows", len(ov), "in snapshot", int(ov.in_snapshot.sum()), "neither (snapshot):",
          int((ov.in_snapshot & ~ov.own_marker & ~ov.sidecar_flag.fillna(False).astype(bool)).sum()))
    print("overlay not-in-snapshot by stratum:", ov[~ov.in_snapshot].stratum.value_counts().to_dict())
    # registry composition sanity
    print("\n--- primary by layer: crossref-only (no RW):", int((C.crossref & ~C.rw).sum()), "; RW-dated:", int(C.rw.sum()))
    print("primary dated 2026 (<= CUT):", int((C.date.dt.year == 2026).sum()), "; of them self-update:",
          int(C[C.date.dt.year == 2026].pmcid.isin(O[O.date_source.str.startswith("crossref-self")].pmcid).sum()))


if __name__ == "__main__":
    main()
