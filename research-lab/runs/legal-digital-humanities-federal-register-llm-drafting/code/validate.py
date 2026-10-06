"""Validation before unsealing (plan section 4), using 2019-2021 text and generated text only.

Estimator (D5, after the first V1 failed): paired LLM reference (mle.Estimator(paired=...)) plus a two-point linear
calibration fitted on 2019-21 data that V1 never sees: a = raw alpha on the generation pool's human documents,
b = raw alpha on the calibration half (C) of the held-out generated sentences, minus a; calibrated alpha =
(raw - a) / b, applied to point estimates and bootstrap draws alike. Held-out paragraph keys are split into halves C
and V by the parity of the md5 of the key.

V1: synthetic mixtures of validation-pool human text and the V half of the held-out generated sentences at alpha in
    {0,2,5,10,25}%, 50 replicates each, at the sentence count of the DOT post period. Two constructions (D5):
    "pseudo-documents" (as first coded: sentences shuffled into 290 equal chunks) and "documents" (290 real validation
    documents sampled per replicate, each sentence replaced by a generated one with probability alpha), so that the
    document bootstrap faces real between-document heterogeneity as in the analysis. Criteria: |bias| < 1 pp at
    alpha <= 10% and coverage >= 90%.
V2: power. Four pseudo-groups with the real document counts of DOT-pre, DOT-post, other-pre and other-post, each
    drawn independently WITH replacement from the 2019-21 generation and validation pools' human documents (D3); a
    DiD of delta injected into DOT-post; power = share of replicates whose 95% document-bootstrap CI excludes 0; MDE =
    smallest delta with power >= 0.8. `validate.py capped` runs the first-coded capped design as a sensitivity.
Writes results/tables/validation_v1.csv, validation_v2.csv (or validation_v2_capped.csv), calibration.json and
estimator_vocab.txt."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mle import Estimator, adj_adv_words, alpha_mle, bootstrap_alpha, sentences  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
RNG = np.random.default_rng(20261007)


def llm_sentences(heldout_frac=0.2):
    """Generated sentences from all generators and both tasks; a held-out 20% of paragraph keys is kept for
    validation (same split as before D5: a fresh generator seeded 20261006)."""
    rows = []
    for f in sorted((RUN / "data" / "llm_ref").glob("*.jsonl")):
        for j in map(json.loads, open(f)):
            for task in ("polish", "draft"):
                if j.get(task):
                    rows.append(dict(gen=f.stem, task=task, key=f'{j["document_number"]}:{j["para_idx"]}', text=j[task]))
    g = pd.DataFrame(rows)
    keys = np.array(sorted(g.key.unique()))
    np.random.default_rng(20261006).shuffle(keys)
    held = set(keys[: int(heldout_frac * len(keys))])
    g["held"] = g.key.isin(held)
    g["half"] = np.where(~g.held, "ref", np.where([int(hashlib.md5(k.encode()).hexdigest(), 16) % 2 == 0 for k in g.key], "C", "V"))
    ref = [s for t in g[~g.held].text for s in sentences(t)]
    val = [s for t in g[g.held].text for s in sentences(t)]
    return ref, val, g


def doc_sentences(df):
    out = {}
    for doc, grp in df[~df.procedural].groupby("document_number"):
        s = [x for t in grp.text for x in sentences(t)]
        if s:
            out[doc] = s
    return out


def build_estimator(gens=None, human_sents=None):
    """The D5 estimator: paired reference from the kept generators (all if gens is None), calibrated on the
    generation pool's human documents and the C half. Returns (est, info, V-half sentences); est.cal maps raw alpha
    to the calibrated scale."""
    if human_sents is None:
        human = pd.read_parquet(RUN / "data" / "pools" / "human.parquet")
        human_sents = [s for t in human[~human.procedural].text for s in sentences(t)]
    _, _, g = llm_sentences()
    if gens is not None:
        g = g[g.gen.isin(gens)]
    ref = [s for t in g[g.half == "ref"].text for s in sentences(t)]
    src = pd.read_parquet(RUN / "data" / "pools" / "generation_pool_sample.parquet")
    src["key"] = src.document_number + ":" + src.para_idx.astype(int).astype(str)
    src_sents = [s for t in src[src.key.isin(set(g[g.half == "ref"].key))].text for s in sentences(t)]
    est = Estimator(human_sents, ref, adj_adv_words(), paired=(src_sents, ref))
    gen_docs = doc_sentences(pd.read_parquet(RUN / "data" / "pools" / "generation.parquet"))
    a = alpha_mle(np.concatenate([est.d(v) for v in gen_docs.values()]))
    c_sents = [s for t in g[g.half == "C"].text for s in sentences(t)]
    b = alpha_mle(est.d(c_sents)) - a
    est.a, est.b = a, b
    est.cal = lambda x: (np.asarray(x) - a) / b
    info = dict(a_raw_alpha_generation_pool=a, b_slope=b, raw_alpha_C_half=a + b, n_ref_sentences=len(ref),
                n_source_sentences=len(src_sents), n_C_sentences=len(c_sents), vocab=len(est.vocab),
                generators=sorted(g.gen.unique()))
    v_sents = [s for t in g[g.half == "V"].text for s in sentences(t)]
    return est, info, v_sents


def main():
    design = sys.argv[1] if len(sys.argv) > 1 else "resample"  # "capped": the first-coded V2 design, run as a sensitivity
    est, info, v_sents = build_estimator()
    (TAB / "estimator_vocab.txt").write_text("\n".join(est.vocab))
    print(json.dumps(info), flush=True)
    vdocs = doc_sentences(pd.read_parquet(RUN / "data" / "pools" / "validation.parquet"))
    vd = {k: est.d(v) for k, v in vdocs.items()}
    gen_docs = doc_sentences(pd.read_parquet(RUN / "data" / "pools" / "generation.parquet"))
    bg = dict(vd, **{k: est.d(v) for k, v in gen_docs.items()})  # V2 background (D3): human text only
    d_llm = est.d(v_sents)
    info.update(raw_alpha_validation_pool=alpha_mle(np.concatenate(list(vd.values()))), raw_alpha_V_half=alpha_mle(d_llm))
    info["calibrated_alpha_validation_pool"] = float(est.cal(info["raw_alpha_validation_pool"]))
    info["calibrated_alpha_V_half"] = float(est.cal(info["raw_alpha_V_half"]))
    if design == "resample":
        json.dump(info, open(TAB / "calibration.json", "w"), indent=1, default=float)
    print(json.dumps({k: info[k] for k in info if "validation" in k or "V_half" in k}, default=float), flush=True)
    # sentence count of the DOT post period: 290 documents x mean sentences per DOT document in 2024-25 (a count only)
    raw = pd.read_parquet(RUN / "data" / "paragraphs_raw.parquet", columns=["document_number", "publication_date", "group", "templated", "procedural", "text"])
    dot_pre = raw[(raw.group == "DOT") & ~raw.templated & ~raw.procedural & (raw.publication_date >= "2024-01-01")]
    spd = dot_pre.groupby("document_number").text.apply(lambda t: sum(len(sentences(x)) for x in t))
    n_post = int(290 * spd.mean())
    print(f"DOT 2024-25 mean sentences per document {spd.mean():.1f}; post-period sentence count ~ {n_post}", flush=True)
    pool_d = np.concatenate(list(vd.values()))
    vkeys = list(vd)
    rows = []
    for a in ((0.0, 0.02, 0.05, 0.10, 0.25) if design == "resample" else ()):  # V1 runs once, with the main design
        for construction in ("pseudo-documents", "documents"):
            for r in range(50):
                if construction == "pseudo-documents":
                    k = int(round(a * n_post))
                    hum = RNG.choice(pool_d, n_post - k, replace=False)
                    ai = RNG.choice(d_llm, k, replace=k > len(d_llm)) if k else np.array([])
                    docs = np.array_split(RNG.permutation(np.concatenate([hum, ai])), 290)
                else:
                    docs = []
                    for key in RNG.choice(vkeys, 290, replace=False):
                        arr = vd[key].copy()
                        m = RNG.random(len(arr)) < a
                        if m.any():
                            arr[m] = RNG.choice(d_llm, int(m.sum()))
                        docs.append(arr)
                raw_a, draws = bootstrap_alpha(docs, B=300, rng=RNG)
                e, dr = float(est.cal(raw_a)), est.cal(draws)
                lo, hi = np.percentile(dr, [2.5, 97.5])
                rows.append(dict(construction=construction, alpha=a, rep=r, raw=raw_a, est=e, lo=lo, hi=hi, covered=lo <= a <= hi))
            v = pd.DataFrame([x for x in rows if x["alpha"] == a and x["construction"] == construction])
            print(f"V1 {construction} alpha={a:.2f}: mean est {v.est.mean():.4f} bias {v.est.mean() - a:+.4f} coverage {v.covered.mean():.2f} mean CI width {(v.hi - v.lo).mean():.4f}", flush=True)
    if rows:
        pd.DataFrame(rows).to_csv(TAB / "validation_v1.csv", index=False)
    # V2: power for the DiD (calibrated scale)
    counts = {"dot_pre": 732, "dot_post": 290, "oth_pre": 3295, "oth_post": 1178}  # D1 corrected counts
    keys = list(bg) if design == "resample" else list(vd)
    rows2 = []
    for delta in (0.0, 0.01, 0.02, 0.03, 0.05, 0.075):
        for r in range(40):
            groups = {}
            if design == "resample":  # D3: real counts, independent draws with replacement
                for gname, n in counts.items():
                    groups[gname] = [bg[k] for k in RNG.choice(keys, n, replace=True)]
            else:  # first-coded design: disjoint groups from the validation pool, capped at pool/4
                perm, cut = RNG.permutation(keys), 0
                for gname, n in counts.items():
                    take = min(n, len(perm) // 4)
                    groups[gname] = [vd[k] for k in perm[cut:cut + take]]
                    cut += take
            post = []
            for arr in groups["dot_post"]:
                arr = arr.copy()
                m = RNG.random(len(arr)) < delta
                if m.any():
                    arr[m] = RNG.choice(d_llm, int(m.sum()))
                post.append(arr)
            groups["dot_post"] = post
            ests, draws = {}, {}
            for gname, docs in groups.items():
                ra, rd = bootstrap_alpha(docs, B=300, rng=RNG)
                ests[gname], draws[gname] = float(est.cal(ra)), est.cal(rd)
            did = (ests["dot_post"] - ests["dot_pre"]) - (ests["oth_post"] - ests["oth_pre"])
            dd = (draws["dot_post"] - draws["dot_pre"]) - (draws["oth_post"] - draws["oth_pre"])
            lo, hi = np.percentile(dd, [2.5, 97.5])
            rows2.append(dict(delta=delta, rep=r, did=did, lo=lo, hi=hi, detect=lo > 0 or hi < 0, group_sizes=json.dumps({k: len(v) for k, v in groups.items()})))
        v = pd.DataFrame([x for x in rows2 if x["delta"] == delta])
        print(f"V2 delta={delta:.3f}: mean DiD {v.did.mean():+.4f} power {v.detect.mean():.2f} mean CI width {(v.hi - v.lo).mean():.4f}", flush=True)
    v2 = pd.DataFrame(rows2)
    v2.to_csv(TAB / ("validation_v2.csv" if design == "resample" else "validation_v2_capped.csv"), index=False)
    pw = v2.groupby("delta").detect.mean()
    mde = pw[pw >= 0.8].index.min() if (pw >= 0.8).any() else np.nan
    print(f"MDE (80% power, {design} design):", mde)


if __name__ == "__main__":
    main()
