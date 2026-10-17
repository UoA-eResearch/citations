"""Response to the adversarial review (deviations D5). Every number the revised report adds comes from here.

  R1  the four exact-tuple crossings audited: df present?, p of 0 or 1?; exact crossings with df (v1, all versions)
  R3  verified crossings re-based: the version-1 census restricted to changed results and deduplicated (coding in
      results/tables/verified_coding.csv, written after unblinding from the blind notes and sentences); sensitivities
      for the reviewer's three rejections and for the pooled set
  R4  crossing rates per 1,000 determined aligned pairs by both routes
  R8  strict crossings and verified crossings containing glued table/caption text; sensitivity without them
  R13 S1 restricted to statistics removed from (added to) a sentence that survived (it holds an aligned statistic)
  R14 S2 decomposition: evaluable, verbatim unchanged, one-tailed explicable, decision inconsistencies and repairs
  R16 title-Jaccard rejections by server
  R17 posting-to-publication gap of the verified papers (Crossref), and a sensitivity excluding gaps <= 30 days
Writes results/tables/review_response.json."""
import gzip
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analysis import consistent, recompute_p  # noqa: E402
from analysis_v2 import CROSS, clopper, strict  # noqa: E402
from supplementary import paper_boot, verified  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
GLUE = re.compile(r"[a-z0-9\)%][.!?][A-Z]")


def est(g):
    k, n = int(g.up.sum()), len(g)
    return dict(n=n, up=k, share=k / n if n else None, exact_ci=list(clopper(k, n)) if n else None,
                n_papers=int(g.pair.nunique()), paper_boot_ci=paper_boot(g) if n else None)


def crossref_date(doi, kind):
    try:
        m = requests.get(f"https://api.crossref.org/works/{doi}", timeout=60,
                         headers={"User-Agent": "research-lab (mailto:noreply@anthropic.com)"}).json()["message"]
        for k in (("posted", "created") if kind == "pre" else ("published-online", "published-print", "published", "issued")):
            if m.get(k, {}).get("date-parts"):
                p = m[k]["date-parts"][0]
                return pd.Timestamp(year=p[0], month=p[1] if len(p) > 1 else 1, day=p[2] if len(p) > 2 else 1)
    except Exception:
        return None


def main():
    out = {}
    pairs = pd.DataFrame([json.loads(l) for l in open(RUN / "data" / "aligned" / "pairs.jsonl")])
    v1 = set(pairs[pairs.version_used.astype(str) == "1"].preprint_doi)
    rows = [json.loads(l) for l in gzip.open(RUN / "data" / "aligned" / "statistics.jsonl.gz", "rt")]
    # R1
    ex = [r for r in rows if r["status"] == "aligned" and r["how"] == "exact" and r["cls"] in CROSS]
    aud = lambda rs: dict(n=len(rs), with_df=sum(bool(r["pre"]["df"]) for r in rs),
                          p0_or_p1=sum(r["pre"]["p"] in (0.0, 1.0) or r["pub"]["p"] in (0.0, 1.0) for r in rs),
                          with_df_and_no_p01=sum(bool(r["pre"]["df"]) and r["pre"]["p"] not in (0.0, 1.0) and r["pub"]["p"] not in (0.0, 1.0) for r in rs))
    out["R1_exact_crossings"] = dict(v1=aud([r for r in ex if r["pair"] in v1]), all_versions=aud(ex),
                                     exact_matches_without_df=sum(1 for r in rows if r["status"] == "aligned" and r["how"] == "exact" and not r["pre"]["df"]),
                                     exact_matches=sum(1 for r in rows if r["status"] == "aligned" and r["how"] == "exact"))
    out["R1_exact_crossings"]["v1_list"] = [dict(pair=r["pair"], pre=f'{r["pre"]["test"]}({r["pre"]["df"]})={r["pre"]["stat"]} {r["pre"]["cmp"]} {r["pre"]["p"]}',
                                                 pub=f'{r["pub"]["test"]}({r["pub"]["df"]})={r["pub"]["stat"]} {r["pub"]["cmp"]} {r["pub"]["p"]}', cls=r["cls"])
                                            for r in ex if r["pair"] in v1]
    # R3
    v = verified(); v = v[v.correct == 1].copy()
    v["key"] = v.pair + "|" + v.pre + "|" + v.pub
    v = v.sort_values("sample", ascending=False)          # keep the v2 (census) id when both samples verified it
    cod = pd.read_csv(TAB / "verified_coding.csv")
    v = v.drop_duplicates("key").merge(cod, on="id", how="left")
    assert v.code.notna().all(), "uncoded verified crossing"
    v["in_v1"] = v.pair.isin(v1)
    changed = v.code.str.startswith("changed")
    rej = v.id.isin(["v136", "w053", "w057"])
    census = v[(v["sample"] == "v2") & changed]
    out["R3_verified"] = dict(
        codes=v.groupby("code").up.agg(["count", "sum"]).rename(columns={"count": "n", "sum": "up"}).to_dict("index"),
        census_changed_v1=est(census),
        census_changed_v1_minus_reviewer_rejections=est(census[~rej]),
        census_changed_v1_new_data_only=est(census[census.code == "changed_data"]),
        pooled_changed_in_v1_population=est(v[changed & v.in_v1]),
        pooled_all_52_as_drafted=est(v),
        outside_v1_population=int((~v.in_v1).sum()))
    # R8 glued text
    al2 = [json.loads(l) for l in gzip.open(RUN / "data" / "aligned_v2" / "statistics.jsonl.gz", "rt")]
    sc = [r for r in al2 if r["status"] == "aligned" and r["pair"] in v1 and strict(r) and r["cls"] in CROSS]
    glued = lambda r: bool(GLUE.search(r["pre"]["sentence"]) or GLUE.search(r["pub"]["sentence"]) or max(len(r["pre"]["sentence"]), len(r["pub"]["sentence"])) > 600)
    gl_keys = {(r["pair"], round(r["pre"]["p"] or -1, 8), round(r["pub"]["p"] or -1, 8)) for r in sc if glued(r)}
    s2 = {json.loads(l)["id"]: json.loads(l) for l in open(RUN / "data" / "validation" / "sample_v2.jsonl")}
    def is_glued(row):
        x = s2.get(row.id)
        return bool(x) and bool(GLUE.search(x["sentence_1"]) or GLUE.search(x["sentence_2"]) or max(len(x["sentence_1"]), len(x["sentence_2"])) > 600)
    census = census.assign(glued=[is_glued(r) for r in census.itertuples()])
    out["R8_glued"] = dict(strict_v1_crossings=len(sc), glued=len(gl_keys),
                           census_changed_glued=int(census.glued.sum()), census_changed_without_glued=est(census[~census.glued]))
    # R4 rates
    det_all = sum(1 for r in rows if r["status"] == "aligned" and r["pair"] in v1 and r["cls"] != "undetermined")
    det_strict = sum(1 for r in al2 if r["status"] == "aligned" and r["pair"] in v1 and strict(r) and r["cls"] != "undetermined")
    out["R4_rates_per_1000"] = dict(prereg_route=1000 * 1411 * 0.12 / det_all, prereg_determined=det_all,
                                    strict_route=1000 * len(sc) * 42 / 64 / det_strict, strict_determined=det_strict)
    # R13 S1 within surviving sentences
    rv1 = [r for r in rows if r["pair"] in v1]
    keep = {}
    for r in rv1:
        if r["status"] == "aligned":
            keep.setdefault(r["pair"], [set(), set()]); keep[r["pair"]][0].add(r["pre"]["sentence"]); keep[r["pair"]][1].add(r["pub"]["sentence"])
    S = []
    for r in rv1:
        if r["status"] == "dropped" and r["pre"]["sig"] is not None and r["pre"]["sentence"] in keep.get(r["pair"], [set(), set()])[0]:
            S.append((r["pair"], "dropped", r["pre"]["sig"]))
        if r["status"] == "added" and r["pub"]["sig"] is not None and r["pub"]["sentence"] in keep.get(r["pair"], [set(), set()])[1]:
            S.append((r["pair"], "added", r["pub"]["sig"]))
    s1 = pd.DataFrame(S, columns=["pair", "status", "sig"])
    g = s1.groupby(["pair", "status"]).sig.agg(["sum", "count"]).unstack(fill_value=0)
    sa, na, sd, nd = (g[("sum", "added")].to_numpy(), g[("count", "added")].to_numpy(), g[("sum", "dropped")].to_numpy(), g[("count", "dropped")].to_numpy())
    idx = np.random.default_rng(20261017).integers(0, len(g), size=(2000, len(g)))
    diff = sa[idx].sum(1) / np.maximum(na[idx].sum(1), 1) - sd[idx].sum(1) / np.maximum(nd[idx].sum(1), 1)
    out["R13_S1_surviving_sentences"] = dict(n_dropped=int(nd.sum()), share_sig_dropped=float(sd.sum() / nd.sum()),
                                             n_added=int(na.sum()), share_sig_added=float(sa.sum() / na.sum()),
                                             diff=float(sa.sum() / na.sum() - sd.sum() / nd.sum()),
                                             ci=[float(np.percentile(diff, 2.5)), float(np.percentile(diff, 97.5))], n_papers=int(len(g)))
    # R14 S2
    tup = [r for r in rv1 if r["status"] == "aligned" and r["pre"]["kind"] == "tuple" and r["pub"]["kind"] == "tuple"]
    inc = [(consistent(r["pre"]), consistent(r["pub"]), r) for r in tup]
    bad = [(a, b, r) for a, b, r in inc if a is False]
    def one_tail(x):
        p2 = recompute_p(x["test"], x["df"], abs(x["stat"]))
        return p2 is not None and x["cmp"] == "=" and abs(x["p"] - p2 / 2) <= max(0.005, 0.1 * p2)
    def dec(x):
        p2 = recompute_p(x["test"], x["df"], abs(x["stat"]))
        return p2 is not None and x["sig"] is not None and ((p2 < 0.05) != x["sig"])
    out["R14_S2"] = dict(aligned_tuple_pairs=len(tup), evaluable=sum(a is not None for a, _, _ in inc), preprint_inconsistent=len(bad),
                         verbatim_unchanged=sum(1 for a, b, r in bad if r["pre"]["p"] == r["pub"]["p"] and r["pre"]["stat"] == r["pub"]["stat"]),
                         one_tailed_explicable=sum(one_tail(r["pre"]) for _, _, r in bad), repaired=sum(b is True for _, b, _ in bad),
                         decision_inconsistent=sum(dec(r["pre"]) for _, _, r in bad), decision_repaired=sum(dec(r["pre"]) and b is True for _, b, r in bad))
    # R16 title-Jaccard rejections by server
    pc = pd.DataFrame([json.loads(l) for l in open(TAB / "pairs_candidates.jsonl")])
    rejd = pc[~pc.confirmed.astype(bool)]
    out["R16_title_rejections"] = dict(candidates=int(len(pc)), rejected=int(len(rejd)), by_server=rejd.groupby("server").size().to_dict())
    # R17 posting gaps for verified papers in the census
    pub = pairs.set_index("preprint_doi").published_doi.to_dict()
    gaps = {}
    for d in sorted(set(census.pair)):
        a, b = crossref_date(d, "pre"), crossref_date(pub.get(d), "pub"); time.sleep(0.3)
        gaps[d] = (b - a).days if (a is not None and b is not None) else None
    census = census.assign(gap=census.pair.map(gaps))
    out["R17_posting_gap"] = dict(papers=len(gaps), known=sum(g is not None for g in gaps.values()),
                                  gap_le_30=sum(1 for g in gaps.values() if g is not None and g <= 30),
                                  gap_negative=sum(1 for g in gaps.values() if g is not None and g < 0),
                                  census_changed_gap_over_30=est(census[census.gap.isna() | (census.gap > 30)]))
    json.dump(out, open(TAB / "review_response.json", "w"), indent=1, default=float)
    print(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    sys.exit(main())
