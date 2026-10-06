"""Validation before unsealing (plan section 4), using 2019-2021 text and generated text only.
V1: synthetic mixtures of validation-pool human sentences and held-out generated sentences at alpha in {0,2,5,10,25}%,
    50 replicates each, at the sentence count of the DOT post period (290 documents x mean sentences per DOT document
    in 2024-25, counted without estimating anything); bias and bootstrap-CI coverage.
V2: power. Four pseudo-groups with the real document counts of DOT-pre, DOT-post, other-pre and other-post, each
    drawn independently WITH replacement from the 2019-21 generation and validation pools' human documents (D3: the
    validation pool alone has 1,283 documents, fewer than the 5,495 the four groups need); a DiD of delta injected into
    DOT-post; power = share of replicates whose 95% document-bootstrap CI excludes 0; MDE = smallest delta with power
    >= 0.8. The capped design (each group <= pool/4 documents, as first coded) is kept as a sensitivity.
Writes results/tables/validation_v1.csv, validation_v2.csv and results/tables/estimator_vocab.txt."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mle import Estimator, adj_adv_words, alpha_mle, bootstrap_alpha, sentences  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
RNG = np.random.default_rng(20261006)


def llm_sentences(heldout_frac=0.2):
    """Generated sentences from all generators and both tasks; a held-out 20% of paragraphs is kept for validation."""
    rows = []
    for f in sorted((RUN / "data" / "llm_ref").glob("*.jsonl")):
        for j in map(json.loads, open(f)):
            for task in ("polish", "draft"):
                if j.get(task):
                    rows.append(dict(gen=f.stem, task=task, key=f'{j["document_number"]}:{j["para_idx"]}', text=j[task]))
    g = pd.DataFrame(rows)
    keys = np.array(sorted(g.key.unique()))
    RNG.shuffle(keys)
    held = set(keys[: int(heldout_frac * len(keys))])
    ref = [s for t in g[~g.key.isin(held)].text for s in sentences(t)]
    val = [s for t in g[g.key.isin(held)].text for s in sentences(t)]
    return ref, val, g


def doc_sentences(df):
    out = {}
    for doc, grp in df[~df.procedural].groupby("document_number"):
        s = [x for t in grp.text for x in sentences(t)]
        if s:
            out[doc] = s
    return out


def main():
    human = pd.read_parquet(RUN / "data" / "pools" / "human.parquet")
    human_sents = [s for t in human[~human.procedural].text for s in sentences(t)]
    llm_ref, llm_val, g = llm_sentences()
    est = Estimator(human_sents, llm_ref, adj_adv_words())
    (TAB / "estimator_vocab.txt").write_text("\n".join(est.vocab))
    print(f"vocab {len(est.vocab)} | human sentences {len(human_sents)} | LLM ref sentences {len(llm_ref)} | LLM held-out {len(llm_val)}", flush=True)
    val = pd.read_parquet(RUN / "data" / "pools" / "validation.parquet")
    vdocs = doc_sentences(val)
    vd = {k: est.d(v) for k, v in vdocs.items()}
    gen_pool = pd.read_parquet(RUN / "data" / "pools" / "generation.parquet")
    bg = dict(vd, **{k: est.d(v) for k, v in doc_sentences(gen_pool).items()})  # V2 background (D3): human text only
    d_llm = est.d(llm_val)
    # sentence count of the DOT post period: 290 documents x mean sentences per DOT document in 2024-25 (a count only)
    raw = pd.read_parquet(RUN / "data" / "paragraphs_raw.parquet", columns=["document_number", "publication_date", "group", "templated", "procedural", "text"])
    dot_pre = raw[(raw.group == "DOT") & ~raw.templated & ~raw.procedural & (raw.publication_date >= "2024-01-01")]
    spd = dot_pre.groupby("document_number").text.apply(lambda t: sum(len(sentences(x)) for x in t))
    n_post = int(290 * spd.mean())
    print(f"DOT 2024-25 mean sentences per document {spd.mean():.1f}; post-period sentence count ~ {n_post}", flush=True)
    pool_d = np.concatenate(list(vd.values()))
    design = sys.argv[1] if len(sys.argv) > 1 else "resample"  # "capped": the first-coded V2 design, run as a sensitivity
    rows = []
    for a in ((0.0, 0.02, 0.05, 0.10, 0.25) if design == "resample" else ()):  # V1 runs once, with the main design
        for r in range(50):
            k = int(round(a * n_post))
            # mixtures built as 'documents' of ~mean length so the bootstrap is by document
            hum = RNG.choice(pool_d, n_post - k, replace=False)
            ai = RNG.choice(d_llm, k, replace=False) if k else np.array([])
            d = RNG.permutation(np.concatenate([hum, ai]))
            docs = np.array_split(d, 290)
            est_a, draws = bootstrap_alpha(docs, B=300, rng=RNG)
            lo, hi = np.percentile(draws, [2.5, 97.5])
            rows.append(dict(alpha=a, rep=r, est=est_a, lo=lo, hi=hi, covered=lo <= a <= hi))
        v = pd.DataFrame([x for x in rows if x["alpha"] == a])
        print(f"V1 alpha={a:.2f}: mean est {v.est.mean():.4f} bias {v.est.mean() - a:+.4f} coverage {v.covered.mean():.2f}", flush=True)
    if rows:
        pd.DataFrame(rows).to_csv(TAB / "validation_v1.csv", index=False)
    # V2: power for the DiD
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
                ests[gname], draws[gname] = bootstrap_alpha(docs, B=300, rng=RNG)
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
