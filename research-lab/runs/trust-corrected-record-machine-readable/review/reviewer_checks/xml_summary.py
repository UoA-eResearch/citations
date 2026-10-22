"""Reviewer check: summarise xml_pass.parquet against the study's verdicts (documents_d3.csv.gz, overlay).
Notice-like documents in the cohort; where markers sit; disagreements with the D3 'own marker'.
Run: venv/bin/python -I xml_summary.py
"""
import re
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
RUN = HERE.parents[1]
T = RUN / "results" / "tables"
pd.set_option("display.width", 200, "display.max_colwidth", 110)


def main():
    x = pd.read_parquet(HERE / "xml_pass.parquet")
    c = pd.read_parquet(RUN / "data" / "cohort.parquet")[["pmcid", "stratum", "doi", "rw", "crossref", "pubmed", "openalex", "notice_id", "date", "publisher"]]
    d3 = pd.read_csv(T / "documents_d3.csv.gz")
    ov = pd.read_csv(RUN / "results" / "overlay" / "retraction_overlay.csv.gz")[["pmcid", "own_marker", "sidecar_flag", "date_source"]]
    docs = pd.read_csv(T / "documents.csv.gz")[["pmcid", "xml_kinds", "xml_structured", "xml_textual", "publisher_name"]]
    d = x.merge(c, on="pmcid").merge(d3, on="pmcid", how="left").merge(ov, on="pmcid", how="left").merge(docs, on="pmcid", how="left")
    d = d[d.article_type.fillna("").str.lower() != "retraction"]
    P = d[d.stratum == "primary"].copy()
    print("primary rows", len(P), "errors", int(P.err.notna().sum()) if "err" in P else 0)

    # ---- 1. notice-like documents
    rel = P.rel.fillna("")
    P["rel_notice_like"] = rel.str.contains(r"(retracted-article|corrected-article|object-of-concern|retraction-of)@(article-meta|front)", regex=True)
    P["rel_fwd_meta"] = rel.str.contains(r"(retraction-forward|retraction|retracted)@(article-meta|front)", regex=True) & ~rel.str.contains(r"retracted-article@(article-meta|front)", regex=True)
    P["title_noticey"] = P.title_class.isin(["retraction", "notice of retraction", "withdrawal", "expression of concern", "erratum",
                                             "corrigendum", "correction", "statement of retraction", "retraction note", "editorial expression"])
    P["type_noticey"] = P.article_type.isin(["correction", "expression-of-concern", "editorial", "other", "letter", "article-commentary", "announcement", "retraction", "discussion", "abstract"])
    print("\n--- notice-like features in the primary cohort")
    print("title begins with a notice word (retraction/withdrawal/erratum/corrigendum/correction/EoC):", int(P.title_noticey.sum()))
    print("   by title class:", P[P.title_noticey].title_class.value_counts().to_dict())
    print("   their article types:", P[P.title_noticey].article_type.value_counts().head(8).to_dict())
    print("   median body chars:", int(P[P.title_noticey].body_chars.median()), "vs cohort", int(P.body_chars.median()))
    print("   D3 own_marker among them:", round(P[P.title_noticey].own_marker.mean(), 3), "; flagged notice_id:", int(P[P.title_noticey].notice_id.sum()))
    print("related-article of a notice->original type (retracted-article/corrected-article/object-of-concern) in article-meta:", int(P.rel_notice_like.sum()))
    print("   their title classes:", P[P.rel_notice_like].title_class.replace("", "(none)").value_counts().head(6).to_dict())
    both = P[P.title_noticey | P.rel_notice_like]
    print("union title-noticey OR notice-type link:", len(both), "; share of cohort", round(len(both) / len(P), 4))
    print("   of which body < 3000 chars (notice-length):", int((both.body_chars < 3000).sum()))
    print("   D3 own_marker among union:", round(both.own_marker.mean(), 3))
    print("\n   20 sample titles (title-noticey, shortest bodies):")
    for r in P[P.title_noticey].sort_values("body_chars").head(20).itertuples():
        print(f"     {r.pmcid} [{r.article_type}, body {r.body_chars}, own {r.own_marker}, rw {r.rw} cr {r.crossref} pm {r.pubmed}] {r.title[:95]}")
    print("\n   'Withdrawal:'/'Withdrawn:' titles by article type:", P[P.title_class.isin(['withdrawal', 'withdrawn'])].article_type.value_counts().to_dict())
    print("   Titles starting 'Retraction' (not 'Retracted'):", int((P.title_class == 'retraction').sum()), "; types:",
          P[P.title_class == 'retraction'].article_type.value_counts().head(6).to_dict())
    for r in P[P.title_class == 'retraction'].sample(min(8, int((P.title_class == 'retraction').sum())), random_state=2).itertuples():
        print(f"     {r.pmcid} [{r.article_type}, body {r.body_chars}] {r.title[:100]} | rel {r.rel[:60]}")

    # ---- 2. where the markers sit
    print("\n--- related-article retraction-type links by location (primary)")
    locs = rel.str.split("|").explode()
    locs = locs[locs.str.contains("retract")]
    print(locs.str.split("@").str[1].value_counts().to_dict())
    print("types:", locs.str.split("@").str[0].value_counts().head(8).to_dict())
    P["fwd_only_nonmeta"] = ~P.rel_fwd_meta & rel.str.contains(r"retract\w*@(body|back|other|sub-article)", regex=True) & ~rel.str.contains(r"retract\w*@ref", regex=True)
    print("docs whose retraction links sit ONLY in body/back/other/sub-article (not article-meta, not ref):", int(P.fwd_only_nonmeta.sum()))
    for r in P[P.fwd_only_nonmeta].head(8).itertuples():
        print(f"     {r.pmcid} own_structured={r.own_structured} rel={r.rel[:120]} | {r.title[:60]}")
    print("sub-articles: docs with any:", int((P.n_sub > 0).sum()), "; types:", P[P.n_sub > 0].sub_types.str.split(";").explode().value_counts().head(6).to_dict())
    print("docs with retraction link in sub-article:", int(rel.str.contains(r"retract\w*@sub-article", regex=True).sum()))
    print("statement hits by location:", P.stmt_locs.fillna("").str.split(";").explode().value_counts().to_dict())
    print("token hits by location:", P.token_locs.fillna("").str.split(";").explode().value_counts().to_dict())

    # ---- 3. textual-only own markers: where, and what the text says
    P["own_struct"] = P.own_structured.fillna(False).astype(bool)
    P["own_text"] = P.own_textual.fillna(False).astype(bool)
    to = P[P.own_text & ~P.own_struct]
    print("\n--- D3 textual-only documents:", len(to))
    print("   title rule fires:", int(to.title_rule.sum()), "; title classes:", to.title_class.replace("", "(none)").value_counts().head(6).to_dict())
    nt = to[~to.title_rule]
    print("   textual-only WITHOUT title prefix:", len(nt), "; stmt locs:", nt.stmt_locs.value_counts().head(6).to_dict(), "; token locs:", nt.token_locs.value_counts().head(6).to_dict())
    for r in nt.head(14).itertuples():
        print(f"     {r.pmcid} [{r.article_type}] {r.title[:60]} || {r.snippet[:150]}")
    bodyonly = nt[(nt.stmt_locs.fillna("") == "body") | (nt.token_locs.fillna("") == "body")]
    print("   statement/token only in BODY (candidates for 'paper about retraction'):", len(bodyonly))

    # ---- 4. my strict own-marker vs D3
    P["strict"] = P.rel_fwd_meta | P.title_rule | P.stmt_locs.fillna("").str.contains("article-meta|front|body|back") | P.token_locs.fillna("").str.contains("article-meta|front|body|back") | (P.custom_meta > 0) | P.notes.fillna("").str.contains("retract")
    print("\n--- strict own marker (link in article-meta/front; title; statement/token outside refs & sub-articles) vs D3 own_structured|own_textual")
    print(pd.crosstab(P.strict, P.own_struct | P.own_text))
    dis = P[P.strict != (P.own_struct | P.own_text)]
    for r in dis.head(10).itertuples():
        print(f"     {r.pmcid} strict={r.strict} d3={r.own_struct or r.own_text} rel={r.rel[:80]} stmt={r.stmt_locs} tok={r.token_locs} | {r.title[:50]}")
    print("strict unmarked share:", round(1 - P.strict.mean(), 4), "; D3 own (no withdrawal) unmarked:", round(1 - (P.own_struct | P.own_text).mean(), 4))

    # ---- 5. D1-kept docs (notice by id but curated original)
    k = P[P.notice_id]
    print("\n--- D1-kept (notice_id) primary docs:", len(k))
    print("   title classes:", k.title_class.replace("", "(none)").value_counts().head(8).to_dict())
    print("   article types:", k.article_type.value_counts().head(8).to_dict())
    print("   notice-like (title or link):", int((k.title_noticey | k.rel_notice_like).sum()))
    for r in k[k.title_noticey | k.rel_notice_like].head(12).itertuples():
        print(f"     {r.pmcid} [{r.article_type}, body {r.body_chars}, rw {r.rw} cr {r.crossref} pm {r.pubmed}] {r.title[:90]}")

    # ---- 6. unmarked residue: what do they look like
    U = P[~P.own_marker.fillna(False).astype(bool)]
    print("\n--- unmarked residue (D3 own, incl. withdrawal):", len(U))
    print("   article types:", U.article_type.value_counts().head(6).to_dict())
    print("   any 'retract' text in refs only:", int((U.stmt_locs.fillna("").eq("ref") | U.token_locs.fillna("").eq("ref")).sum()))
    print("   rel strings present:", int((U.rel.fillna("") != "").sum()), "; sample:", U[U.rel.fillna("") != ""].rel.head(5).tolist())
    print("   publishers:", U.publisher_name.value_counts().head(8).to_dict())
    P.to_csv(HERE / "xml_pass_primary_joined.csv.gz", index=False)


if __name__ == "__main__":
    main()
