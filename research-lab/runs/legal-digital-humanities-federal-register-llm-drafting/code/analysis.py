"""Primary and secondary analyses (plan sections 5-6), written and committed before the outcome issues are unsealed.
Inputs: data/paragraphs_raw.parquet (2019-2025), data/paragraphs_sealed.parquet (2026, parsed only after unsealing),
data/pools/*, data/llm_ref/*.jsonl. Outputs: results/tables/{primary,placebos,event_study,splits,logo,excess_words}.csv
and results/tables/summary.json.

Estimator: pooled LLM reference over all generators (D2), human reference = human pool (2019-21). Units for every
estimate: non-templated, non-procedural paragraphs of DOT or other-cabinet documents, after MinHash near-duplicate
filtering (plan section 2). 2019-21 baselines for placebo P1 use only documents NOT in the human-reference pool."""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from datasketch import MinHash, MinHashLSH

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mle import Estimator, adj_adv_words, alpha_mle, sentences  # noqa: E402
from validate import llm_sentences  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
RNG = np.random.default_rng(20261007)
DEREG = re.compile(r"rescind|rescission|remov|withdraw|deregulat|eliminat", re.I)


def load_paragraphs():
    parts = [pd.read_parquet(RUN / "data" / "paragraphs_raw.parquet")]
    s = RUN / "data" / "paragraphs_sealed.parquet"
    if s.exists():
        parts.append(pd.read_parquet(s))
    p = pd.concat(parts, ignore_index=True)
    p = p[p.group.isin(["DOT", "other_cabinet"]) & ~p.templated]
    return p


def dedup(p):
    """MinHash near-duplicate families (Jaccard >= 0.8 on word 5-shingles of the non-procedural preamble); within a
    family keep one document per quarter."""
    txt = p[~p.procedural].groupby("document_number").text.apply(" ".join)
    lsh, mh = MinHashLSH(threshold=0.8, num_perm=64), {}
    for doc, t in txt.items():
        w = t.lower().split()
        m = MinHash(num_perm=64)
        for i in range(max(1, len(w) - 4)):
            m.update(" ".join(w[i:i + 5]).encode())
        mh[doc] = m
        lsh.insert(doc, m)
    meta = p.drop_duplicates("document_number").set_index("document_number")
    q = pd.PeriodIndex(pd.to_datetime(meta.publication_date), freq="Q").astype(str)
    keep, seen = set(), set()
    for doc in txt.index:
        fam = tuple(sorted(lsh.query(mh[doc])))
        key = (fam, q[doc])
        if key not in seen:
            seen.add(key)
            keep.add(doc)
    return p[p.document_number.isin(keep)], len(txt) - len(keep)


def doc_sents(p, procedural=False):
    """Sentences per document, tokenised once and reused by every estimator variant."""
    out = {}
    for doc, g in p[p.procedural == procedural].groupby("document_number"):
        s = [x for t in g.text for x in sentences(t)]
        if s:
            out[doc] = s
    return out


def doc_d(sents_by_doc, est):
    return {doc: est.d(s) for doc, s in sents_by_doc.items()}


def alpha_boot(docs, dmap, B=2000):
    arr = [dmap[d] for d in docs if d in dmap]
    full = alpha_mle(np.concatenate(arr)) if arr else np.nan
    draws = np.empty(B)
    n = len(arr)
    for b in range(B):
        idx = RNG.integers(0, n, n)
        draws[b] = alpha_mle(np.concatenate([arr[i] for i in idx]))
    return full, draws, n


def did(meta, dmap, pre, post, B=2000, sel=None):
    """pre/post: (start, end) date strings, inclusive. sel: optional boolean mask over meta rows."""
    m = meta if sel is None else meta[sel]
    res = {}
    for gname in ("DOT", "other_cabinet"):
        for per, (a, b) in (("pre", pre), ("post", post)):
            docs = m[(m.group == gname) & (m.publication_date >= a) & (m.publication_date <= b)].index
            res[(gname, per)] = alpha_boot(docs, dmap, B)
    d = (res[("DOT", "post")][0] - res[("DOT", "pre")][0]) - (res[("other_cabinet", "post")][0] - res[("other_cabinet", "pre")][0])
    dd = (res[("DOT", "post")][1] - res[("DOT", "pre")][1]) - (res[("other_cabinet", "post")][1] - res[("other_cabinet", "pre")][1])
    lo, hi = np.nanpercentile(dd, [2.5, 97.5])
    row = dict(DiD=d, lo=lo, hi=hi)
    for (gname, per), (a, _, n) in res.items():
        row[f"alpha_{gname}_{per}"] = a
        row[f"n_{gname}_{per}"] = n
    return row


def verdict(r, mde):
    if r["DiD"] >= 0.05 and r["lo"] > 0:
        return "Supported"
    if r["DiD"] < 0.02 and r["hi"] < 0.05 and mde <= 0.05:
        return "Refuted"
    return "Inconclusive"


def main():
    human = pd.read_parquet(RUN / "data" / "pools" / "human.parquet")
    human_docs = set(human.document_number)
    human_sents = [s for t in human[~human.procedural].text for s in sentences(t)]
    llm_ref, _, gen = llm_sentences()
    cand = adj_adv_words()
    est = Estimator(human_sents, llm_ref, cand)
    p = load_paragraphs()
    p, n_dropped = dedup(p)
    meta = p.drop_duplicates("document_number").set_index("document_number")[["publication_date", "group", "type", "title"]]
    meta = meta[~((meta.publication_date < "2022-01-01") & meta.index.isin(human_docs))]
    sents = doc_sents(p[p.document_number.isin(meta.index)])
    dmap = doc_d(sents, est)
    v2 = pd.read_csv(TAB / "validation_v2.csv")
    pw = v2.groupby("delta").detect.mean()
    mde = float(pw[pw >= 0.8].index.min()) if (pw >= 0.8).any() else float("inf")
    out = {"near_duplicates_dropped": int(n_dropped), "MDE_80": mde}
    prim = did(meta, dmap, ("2024-01-01", "2025-12-31"), ("2026-02-01", "2026-09-30"))
    prim["verdict"] = verdict(prim, mde)
    pd.DataFrame([prim]).to_csv(TAB / "primary.csv", index=False)
    out["primary"] = prim
    pl = [dict(name="P1 2022 vs 2019-21", **did(meta, dmap, ("2019-01-01", "2021-12-31"), ("2022-01-01", "2022-12-31"), B=1000)),
          dict(name="P2 2025H1 vs 2024", **did(meta, dmap, ("2024-01-01", "2024-12-31"), ("2025-01-01", "2025-06-30"), B=1000))]
    pd.DataFrame(pl).to_csv(TAB / "placebos.csv", index=False)
    out["placebo_max_abs"] = max(abs(x["DiD"]) for x in pl)
    if prim["verdict"] == "Supported" and out["placebo_max_abs"] >= 0.02:
        out["verdict_final"] = "Inconclusive (Supported downgraded: placebo |DiD| >= 2 pp)"
    else:
        out["verdict_final"] = prim["verdict"]
    # event study: quarterly alpha by group
    q = pd.PeriodIndex(pd.to_datetime(meta.publication_date), freq="Q").astype(str)
    ev = []
    for gname in ("DOT", "other_cabinet"):
        for qq in sorted(set(q)):
            docs = meta[(meta.group == gname) & (q == qq)].index
            if len(docs) < 5:
                continue
            a, draws, n = alpha_boot(docs, dmap, B=300)
            ev.append(dict(group=gname, quarter=qq, alpha=a, lo=np.nanpercentile(draws, 2.5), hi=np.nanpercentile(draws, 97.5), n_docs=n))
    pd.DataFrame(ev).to_csv(TAB / "event_study.csv", index=False)
    # splits (secondary)
    sp = []
    for name, sel in [("final rules", meta.type == "Rule"), ("proposed rules", meta.type == "Proposed Rule"),
                      ("deregulatory titles", meta.title.fillna("").str.contains(DEREG)), ("other titles", ~meta.title.fillna("").str.contains(DEREG))]:
        sp.append(dict(split=name, **did(meta, dmap, ("2024-01-01", "2025-12-31"), ("2026-02-01", "2026-09-30"), B=1000, sel=sel)))
    # procedural paragraphs
    dproc = doc_d(doc_sents(p[p.document_number.isin(meta.index)], procedural=True), est)
    sp.append(dict(split="procedural paragraphs", **did(meta, dproc, ("2024-01-01", "2025-12-31"), ("2026-02-01", "2026-09-30"), B=1000)))
    pd.DataFrame(sp).to_csv(TAB / "splits.csv", index=False)
    # leave-one-generator-out and Gemini proxy (point estimates)
    lg = []
    gens = sorted(gen.gen.unique())
    for drop in gens + ["ONLY:gemma"]:
        if drop.startswith("ONLY:"):
            keep = gen[gen.gen == drop.split(":")[1]]
            label = "Gemma 4 only (Gemini proxy)"
        else:
            keep = gen[gen.gen != drop]
            label = f"without {drop}"
        if keep.empty:
            continue
        ref = [s for t in keep.text for s in sentences(t)]
        e2 = Estimator(human_sents, ref, cand)
        dm2 = doc_d(sents, e2)
        r = did(meta, dm2, ("2024-01-01", "2025-12-31"), ("2026-02-01", "2026-09-30"), B=300)
        lg.append(dict(reference=label, **r))
    pd.DataFrame(lg).to_csv(TAB / "logo.csv", index=False)
    # excess vocabulary (Kobak-style): document frequency of words in 2026 vs 2024-25, by group
    rows = []
    for gname in ("DOT", "other_cabinet"):
        for per, (a, b) in (("pre", ("2024-01-01", "2025-12-31")), ("post", ("2026-02-01", "2026-09-30"))):
            docs = meta[(meta.group == gname) & (meta.publication_date >= a) & (meta.publication_date <= b)].index
            txt = p[p.document_number.isin(docs) & ~p.procedural].groupby("document_number").text.apply(" ".join)
            n = len(txt)
            from collections import Counter
            c = Counter(w for t in txt for w in set(re.findall(r"[a-z]+", t.lower())))
            for w, k in c.items():
                rows.append(dict(group=gname, period=per, word=w, df=k / n, n=n))
    ex = pd.DataFrame(rows).pivot_table(index=["group", "word"], columns="period", values="df").fillna(0).reset_index()
    ex["excess"] = ex["post"] - ex["pre"]
    ex["ratio"] = (ex["post"] + 1e-3) / (ex["pre"] + 1e-3)
    ex.sort_values("excess", ascending=False).groupby("group").head(40).to_csv(TAB / "excess_words.csv", index=False)
    # typographic markers (secondary, D4): share of documents whose non-procedural text contains a non-breaking hyphen
    # (U+2011) or narrow no-break space (U+202F), characters absent from every 2019-2025 document and frequent in some
    # generators' output; plus em dashes per 1,000 words. Model-free; not part of the decision rule.
    tm = []
    for gname in ("DOT", "other_cabinet"):
        for per, (a, b) in (("2019-21", ("2019-01-01", "2021-12-31")), ("pre", ("2024-01-01", "2025-12-31")), ("post", ("2026-02-01", "2026-09-30"))):
            docs = meta[(meta.group == gname) & (meta.publication_date >= a) & (meta.publication_date <= b)].index
            txt = p[p.document_number.isin(docs) & ~p.procedural].groupby("document_number").text.apply(" ".join)
            nw = txt.str.split().str.len().sum()
            tm.append(dict(group=gname, period=per, n_docs=len(txt), share_nb_marks=float(txt.str.contains("[\u2011\u202f]", regex=True).mean()) if len(txt) else np.nan,
                           em_dash_per_1000_words=float(txt.str.count("\u2014").sum() / nw * 1000) if nw else np.nan))
    pd.DataFrame(tm).to_csv(TAB / "typographic_markers.csv", index=False)
    json.dump(out, open(TAB / "summary.json", "w"), indent=1, default=float)
    print(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
