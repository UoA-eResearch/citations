"""POST-REVIEW secondary and sensitivity analyses (deviation D9). Written after unsealing and after the independent
review (review/review.md); none of them can change the preregistered verdict, which rests on analysis.py's primary
DiD (B = 2,000, seed 20261007). Outputs (results/tables/):
  seed_sensitivity.csv      primary DiD under 12 bootstrap seeds (B = 2,000) and one B = 10,000 run
  variance_by_cell.csv      bootstrap sd of each group-period (raw and calibrated) and share of draws at raw alpha = 0
  boundary.csv              score of the log-likelihood at alpha = 0 and the alpha allowed below 0, per cell
  monitoring_by_department.csv   plan section 6: calibrated alpha by cabinet department x quarter (B = 300)
  department_pre_post.csv   by department, 2024-25 vs Feb-Sep 2026 (B = 1,000)
  dot_subagency_pre_post.csv     DOT operating administrations, 2024-25 vs Feb-Sep 2026 (B = 1,000)
  sensitivities.csv         DiD (B = 2,000) under: clean baseline, FAA/routine titles excluded, broader procedural
                            filter, FERC excluded, prompt-leak vocabulary removed
  post_review_summary.json  composition decompositions and counts"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402
import validate as V  # noqa: E402
from mle import alpha_mle, sentences  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
PRE, POST = ("2024-01-01", "2025-12-31"), ("2026-02-01", "2026-09-30")
ROUTINE = re.compile(r"special conditions?|airways?|\broutes?\b|rnav|\bvor\b|area navigation|petitions?|corrections?|correcting amendment", re.I)
PROC_BROAD = re.compile(r"regulatory impact|regulatory planning|severability|administrative procedure act|good cause|"
                        r"environmental review|international regulatory cooperation|cost[- ]benefit|regulatory analys|"
                        r"executive order|unleashing", re.I)
PROMPT_WORDS = {"every", "only", "supplementary"}  # estimator-vocabulary words that occur in the generation prompts
PREAMBLE = re.compile(r"^\s*(?:here is|here's|sure|certainly|below is)[^\n]*?(?::|\n)\s*", re.I)


class Identity:
    """Raw (uncalibrated) scale, for the variance decomposition."""
    cal = staticmethod(lambda x: np.asarray(x))
    cal_draws = staticmethod(lambda d: np.asarray(d))


def did_seed(meta, dmap, est, seed, B, pre=PRE, post=POST, sel=None):
    A.RNG = np.random.default_rng(seed)
    return A.did(meta, dmap, pre, post, B=B, sel=sel, calib=est)


def cell_docs(meta, g, per, sel=None):
    m = meta if sel is None else meta[sel]
    a, b = per
    return m[(m.group == g) & (m.publication_date >= a) & (m.publication_date <= b)].index


def alpha_ci(docs, dmap, est, B, seed):
    A.RNG = np.random.default_rng(seed)
    a, d, n = A.alpha_boot(docs, dmap, B, est)
    return a, np.nanpercentile(d, 2.5) if n else np.nan, np.nanpercentile(d, 97.5) if n else np.nan, n


def main():
    human = pd.read_parquet(RUN / "data" / "pools" / "human.parquet")
    human_docs = set(human.document_number)
    human_sents = [s for t in human[~human.procedural].text for s in sentences(t)]
    est, info, _ = V.build_estimator(human_sents=human_sents, n_cal=10000)  # first 2,000 draws = analysis.py's
    A.CAL = est
    p = A.load_paragraphs()
    p, _ = A.dedup(p)
    g = pd.read_parquet(RUN / "data" / "meta" / "fr_groups.parquet")[["document_number", "subagency", "ferc"]]
    meta = p.drop_duplicates("document_number").set_index("document_number")[["publication_date", "group", "type", "title", "dept"]]
    meta = meta.join(g.set_index("document_number"))
    meta = meta[~((meta.publication_date < "2022-01-01") & meta.index.isin(human_docs))]
    p = p[p.document_number.isin(meta.index)]
    sents = A.doc_sents(p)
    dmap = A.doc_d(sents, est)
    out = {}

    # 1. seed sensitivity (B = 2,000; 20261007 is analysis.py's seed) and one B = 10,000 run
    seeds = [20261007] + list(range(1, 12))
    rs = Parallel(n_jobs=4)(delayed(did_seed)(meta, dmap, est, s, 2000) for s in seeds)
    rs.append(did_seed(meta, dmap, est, 20261008, 10000))
    sd = pd.DataFrame([dict(seed=s, B=b, DiD=r["DiD"], lo=r["lo"], hi=r["hi"], verdict=A.verdict(r, 0.03))
                       for s, b, r in zip(seeds + [20261008], [2000] * 12 + [10000], rs)])
    sd.to_csv(TAB / "seed_sensitivity.csv", index=False)
    print(sd.round(5).to_string(), flush=True)

    # 2. variance by cell (raw scale) and share of bootstrap draws at the boundary
    vc = []
    for gname in ("DOT", "other_cabinet"):
        for per_name, per in (("pre", PRE), ("post", POST)):
            docs = cell_docs(meta, gname, per)
            A.RNG = np.random.default_rng(20261007)
            a, d, n = A.alpha_boot(docs, dmap, 2000, Identity)
            vc.append(dict(group=gname, period=per_name, n_docs=n, raw_alpha=a, raw_sd=float(np.std(d)), calibrated_sd=float(np.std(d) / est.b),
                           share_draws_at_zero=float(np.mean(d <= 1e-5))))
            # 3. boundary: score at alpha = 0 and the MLE allowed below 0 (down to where 1 + alpha (e^d - 1) stays > 0)
            dd = np.concatenate([dmap[x] for x in docs if x in dmap])
            e = np.exp(np.clip(dd, -50, 50))
            lo_bound = -1.0 / (e.max() - 1.0) * 0.999 if e.max() > 1 else -1.0
            from scipy.optimize import minimize_scalar
            r = minimize_scalar(lambda al: -np.sum(np.log1p(al * (e - 1))), bounds=(lo_bound, 1.0), method="bounded", options={"xatol": 1e-7})
            vc[-1].update(score_at_0=float(np.sum(e - 1)), score_per_sentence=float(np.mean(e - 1)), alpha_floor_allowed=lo_bound,
                          raw_alpha_unbounded=float(r.x), cal_alpha_unbounded=float(est.cal(r.x)), cal_alpha=float(est.cal(a)))
    pd.DataFrame(vc).to_csv(TAB / "variance_by_cell.csv", index=False)
    print(pd.DataFrame(vc).round(4).to_string(), flush=True)

    # 4. monitoring series by department x quarter (plan section 6) and department pre/post
    cab = meta[meta.group.isin(["DOT", "other_cabinet"])].copy()
    cab["quarter"] = pd.PeriodIndex(pd.to_datetime(cab.publication_date), freq="Q").astype(str)
    jobs = [(dept, q, list(d.index)) for (dept, q), d in cab.groupby(["dept", "quarter"]) if len(d) >= 5]
    res = Parallel(n_jobs=4)(delayed(alpha_ci)(docs, {x: dmap[x] for x in docs if x in dmap}, est, 300, 20261009) for _, _, docs in jobs)
    pd.DataFrame([dict(department=dept, quarter=q, alpha=a, lo=lo, hi=hi, n_docs=n) for (dept, q, _), (a, lo, hi, n) in zip(jobs, res)]) \
        .to_csv(TAB / "monitoring_by_department.csv", index=False)
    rows = []
    for dept, d in cab.groupby("dept"):
        r = {"department": dept}
        for per_name, (a, b) in (("pre", PRE), ("post", POST)):
            docs = d[(d.publication_date >= a) & (d.publication_date <= b)].index
            r[f"alpha_{per_name}"], r[f"lo_{per_name}"], r[f"hi_{per_name}"], r[f"n_{per_name}"] = alpha_ci(docs, dmap, est, 1000, 20261010)
        rows.append(r)
    dep = pd.DataFrame(rows)
    dep["change"] = dep.alpha_post - dep.alpha_pre
    dep.sort_values("n_pre", ascending=False).to_csv(TAB / "department_pre_post.csv", index=False)
    print(dep.round(4).to_string(), flush=True)
    oth = dep[dep.department != "DOT"]
    w_pre, w_post = oth.n_pre / oth.n_pre.sum(), oth.n_post / oth.n_post.sum()
    out["comparison_group_2026_reweighted_to_2024_25_shares"] = float((w_pre * oth.alpha_post.fillna(0)).sum())
    out["comparison_group_2024_25_reweighted_to_2026_shares"] = float((w_post * oth.alpha_pre.fillna(0)).sum())
    out["departments_rose"] = int((oth.change > 0).sum()); out["departments_fell"] = int((oth.change <= 0).sum())

    # 5. DOT operating administrations and the composition decomposition
    dot = cab[cab.group == "DOT"]
    rows = []
    for sub, d in dot.groupby("subagency"):
        r = {"subagency": sub}
        for per_name, (a, b) in (("pre", PRE), ("post", POST)):
            docs = d[(d.publication_date >= a) & (d.publication_date <= b)].index
            r[f"alpha_{per_name}"], r[f"lo_{per_name}"], r[f"hi_{per_name}"], r[f"n_{per_name}"] = alpha_ci(docs, dmap, est, 1000, 20261011)
        rows.append(r)
    sub = pd.DataFrame(rows).sort_values("n_pre", ascending=False)
    sub["share_pre"], sub["share_post"] = sub.n_pre / sub.n_pre.sum(), sub.n_post / sub.n_post.sum()
    sub.to_csv(TAB / "dot_subagency_pre_post.csv", index=False)
    print(sub.round(4).to_string(), flush=True)
    ok = sub[(sub.n_pre >= 5) & (sub.n_post >= 5)]
    wp, wq = ok.n_pre / ok.n_pre.sum(), ok.n_post / ok.n_post.sum()
    out["dot_2026_at_2024_25_mix"] = float((wp * ok.alpha_post).sum())
    out["dot_2024_25_at_2026_mix"] = float((wq * ok.alpha_pre).sum())
    out["dot_subagencies_in_decomposition"] = list(ok.subagency)

    # 6. sensitivities (DiD, B = 2,000, seed 20261007)
    sens = []

    def add(label, r, note=""):
        sens.append(dict(sensitivity=label, note=note, **{k: r[k] for k in ("DiD", "lo", "hi")},
                         **{k: r[k] for k in r if k.startswith("alpha_") or k.startswith("n_")}))
        print(label, round(r["DiD"], 4), round(r["lo"], 4), round(r["hi"], 4), flush=True)

    add("primary (reproduction)", did_seed(meta, dmap, est, 20261007, 2000))
    add("clean baseline: pre = 2024-01 to 2025-06", did_seed(meta, dmap, est, 20261007, 2000, pre=("2024-01-01", "2025-06-30")))
    routine = meta.title.fillna("").str.contains(ROUTINE)
    out["routine_titles_share"] = {f"{gname}_{pn}": float(routine[cell_docs(meta, gname, per)].mean()) for gname in ("DOT", "other_cabinet") for pn, per in (("pre", PRE), ("post", POST))}
    add("routine titles excluded (special conditions, routes, airways, petitions, corrections)", did_seed(meta, dmap, est, 20261007, 2000, sel=~routine))
    add("FERC excluded", did_seed(meta, dmap, est, 20261007, 2000, sel=~meta.ferc.fillna(False).astype(bool)))
    pb = p.copy()
    pb["procedural"] = pb.procedural | pb.heading.fillna("").str.contains(PROC_BROAD)
    out["broad_filter_extra_procedural_share"] = float((pb.procedural & ~p.procedural).mean())
    dmap_b = A.doc_d(A.doc_sents(pb), est)
    add("broader procedural filter", did_seed(meta, dmap_b, est, 20261007, 2000))
    # prompt-leak vocabulary removed and chat preambles / Markdown stripped from the generated text
    orig_adj, orig_llm = V.adj_adv_words, V.llm_sentences

    def llm_clean(*a, **k):
        ref, val, gg = orig_llm(*a, **k)
        gg = gg.assign(text=gg.text.str.replace(PREAMBLE, "", regex=True).str.replace("**", "", regex=False))
        return ref, val, gg
    V.adj_adv_words = lambda: orig_adj() - PROMPT_WORDS
    V.llm_sentences = llm_clean
    est_c, info_c, _ = V.build_estimator(human_sents=human_sents, n_cal=2000)
    V.adj_adv_words, V.llm_sentences = orig_adj, orig_llm
    out["prompt_clean_calibration"] = {k: info_c[k] for k in ("a_raw_alpha_generation_pool", "b_slope", "vocab")}
    add("prompt words removed, chat preambles stripped", did_seed(meta, A.doc_d(sents, est_c), est_c, 20261007, 2000))
    pd.DataFrame(sens).to_csv(TAB / "sensitivities.csv", index=False)
    json.dump(out, open(TAB / "post_review_summary.json", "w"), indent=1, default=float)
    print(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
