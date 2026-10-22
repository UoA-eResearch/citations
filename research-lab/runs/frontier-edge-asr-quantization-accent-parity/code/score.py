"""WER, accent gaps, compression penalties, speaker-clustered bootstrap and decisions (plan section 5).

  score.py valgroups MODEL   FP16 validation WER by accent -> results/tables/fp16_validation_group_wer_<MODEL>.json
  score.py analyze MODEL     every decoded test condition -> results/tables/analysis_<MODEL>.json
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import jiwer
import numpy as np
import pandas as pd
from transformers import WhisperTokenizer

RUN = Path(__file__).resolve().parents[1]
MAN = RUN / "data" / "manifest"
TAB = RUN / "results" / "tables"
HYP = RUN / "data" / "hyps"
B, SEED = 2000, 20261022
_tok = WhisperTokenizer.from_pretrained("openai/whisper-small")
TAG = re.compile(r"<[A-Z\-_]+>")


def norm(t):
    return _tok.normalize(TAG.sub(" ", t or "")).strip()


def looped(h, r):
    w = h.split()
    if len(w) > 2 * len(r.split()) + 10:
        return True
    grams = defaultdict(int)
    for i in range(len(w) - 2):
        grams[tuple(w[i:i + 3])] += 1
    return any(v >= 5 for v in grams.values())


def utterances(model, cond, split):
    man = pd.read_csv(MAN / ("eval_segments.csv" if split == "test" else "edacc_all_segments.csv"), keep_default_na=False)
    man = man[(man.split == split) & (man.text != "IGNORE_TIME_SEGMENT_IN_SCORING")]
    if "group" not in man:
        man = man.assign(group=man.accent)
    h = pd.read_json(HYP / model / f"{cond}_{split}.jsonl", lines=True)
    d = man.merge(h, on=["shard", "row"], how="left", validate="1:1")
    assert d.hyp.notna().all(), f"{cond}: missing hypotheses"
    d["ref_n"], d["hyp_n"] = d.text.map(norm), d.hyp.map(norm)
    d = d[d.ref_n.str.len() > 0].copy()
    err, nref, loop = [], [], []
    for r, y in zip(d.ref_n, d.hyp_n):
        o = jiwer.process_words(r, y if y else "")
        err.append(o.substitutions + o.deletions + o.insertions)
        nref.append(o.substitutions + o.deletions + o.hits)
        loop.append(looped(y, r))
    d["err"], d["nref"], d["loop"] = err, nref, loop
    return d[["shard", "row", "speaker", "accent", "group", "err", "nref", "loop"]]


def valgroups(model):
    d = utterances(model, "fp16", "validation")
    g = d.groupby("accent")[["err", "nref"]].sum()
    out = (g.err / g.nref).round(5).to_dict()
    (TAB / f"fp16_validation_group_wer_{model}.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


def conditions(model):
    return sorted(p.name[:-len("_test.jsonl")] for p in (HYP / model).glob("*_test.jsonl"))


def analyze(model):
    conds = conditions(model)
    assert "fp16" in conds
    U = {c: utterances(model, c, "test") for c in conds}
    base = U["fp16"]
    spk = sorted(base.speaker.unique())
    sgroup = base.groupby("speaker").group.first().reindex(spk)
    named = sorted(g for g in sgroup.unique() if g != "other")
    E = {c: U[c].groupby("speaker").err.sum().reindex(spk).to_numpy(float) for c in conds}
    N = base.groupby("speaker").nref.sum().reindex(spk).to_numpy(float)
    L = {c: U[c].groupby("speaker").loop.sum().reindex(spk).to_numpy(float) for c in conds}
    nutt = base.groupby("speaker").size().reindex(spk).to_numpy(float)
    G = np.stack([(sgroup == g).to_numpy(float) for g in named], axis=1)      # S x groups
    wer_fp = (E["fp16"] @ G) / (N @ G)
    order = np.argsort(wer_fp)
    best3, worst3 = order[:3], order[-3:]

    rng = np.random.default_rng(SEED)
    C = np.zeros((B + 1, len(spk)))
    C[0] = 1.0                                                                # row 0 = observed data
    for gname in list(sgroup.unique()):
        idx = np.where((sgroup == gname).to_numpy())[0]
        draws = rng.integers(0, len(idx), size=(B, len(idx)))
        for b in range(B):
            np.add.at(C[b + 1], idx[draws[b]], 1.0)

    def stats(c):
        e, n = C * E[c], C * N
        eg, ng = e @ G, n @ G
        gap = eg[:, worst3].sum(1) / ng[:, worst3].sum(1) - eg[:, best3].sum(1) / ng[:, best3].sum(1)
        wg = eg / ng
        return {"gap": gap, "agg": e.sum(1) / n.sum(1), "literal_gap": wg.max(1) - wg.min(1), "group_wer": wg}

    S = {c: stats(c) for c in conds}
    P = {c: S[c]["gap"] - S["fp16"]["gap"] for c in conds}

    def comp(prefix):
        cs = [c for c in conds if re.fullmatch(prefix + r"_s\d", c)]
        if not cs:
            return None, []
        return np.mean([P[c] for c in cs], axis=0), cs

    def ci(x):
        return [round(float(np.percentile(x[1:], 2.5)), 5), round(float(np.percentile(x[1:], 97.5)), 5)]

    def agg_mean(cs):
        return np.mean([S[c]["agg"] for c in cs], axis=0)

    def decide(ref_prefix, arm_prefix):
        pr, rcs = comp(ref_prefix)
        pa, acs = comp(arm_prefix)
        if pr is None or pa is None:
            return {"status": "not run", "ref": ref_prefix, "arm": arm_prefix}
        d = pr - pa
        R = 1 - pa[0] / pr[0] if pr[0] != 0 else float("nan")
        control = ci(pr)[0] > 0
        dagg = agg_mean(acs) - agg_mean(rcs)
        seedR = {}
        for c in acs:
            s = c.rsplit("_", 1)[1]
            rc = f"{ref_prefix}_{s}"
            if rc in P:
                seedR[s] = round(float(1 - P[c][0] / P[rc][0]), 4) if P[rc][0] != 0 else None
        if control and R >= 0.5 and ci(d)[0] > 0 and dagg[0] <= 0.005:
            v = "Supported" + (" (fragile across seeds)" if any(r is not None and r < 0.25 for r in seedR.values()) else "")
        elif control and ci(d)[1] < 0.5 * pr[0]:
            v = "Refuted"
        else:
            v = "Inconclusive"
        return {"verdict": v, "ref": rcs, "arm": acs, "positive_control_penalty": round(float(pr[0]), 5),
                "positive_control_ci": ci(pr), "positive_control_holds": bool(control), "arm_penalty": round(float(pa[0]), 5),
                "arm_penalty_ci": ci(pa), "reduction_R": round(float(R), 4), "penalty_difference": round(float(d[0]), 5),
                "penalty_difference_ci": ci(d), "agg_wer_change": round(float(dagg[0]), 5), "agg_wer_change_ci": ci(dagg),
                "seed_R": seedR}

    out = {"model": model, "conditions": conds, "named_groups": named,
           "fp16_group_wer": {g: round(float(w), 5) for g, w in zip(named, wer_fp)},
           "worst3_fp16": [named[i] for i in worst3], "best3_fp16": [named[i] for i in best3],
           "per_condition": {}}
    for c in conds:
        out["per_condition"][c] = {
            "agg_wer": round(float(S[c]["agg"][0]), 5), "agg_wer_ci": ci(S[c]["agg"]),
            "gap": round(float(S[c]["gap"][0]), 5), "gap_ci": ci(S[c]["gap"]),
            "penalty": round(float(P[c][0]), 5), "penalty_ci": ci(P[c]),
            "literal_gap": round(float(S[c]["literal_gap"][0]), 5),
            "loop_rate": round(float(L[c].sum() / nutt.sum()), 5),
            "group_wer": {g: round(float(w), 5) for g, w in zip(named, S[c]["group_wer"][0])}}
    for bits in ("w4", "w3"):
        out[f"H1_{bits}"] = decide(f"gptq_{bits}_us", f"gptq_{bits}_balanced")
        out[f"H2_{bits}"] = decide(f"gptq_{bits}_us", f"gptq_{bits}_worst")
    out["H3"] = decide("gptq_w4_us", "mp_us")
    out["H3_bal"] = decide("gptq_w4_balanced", "mp_balanced")
    out["H3_w3"] = decide("gptq_w3_us", "mp3_us")                 # D1 fallback
    out["H3_bal_w3"] = decide("gptq_w3_balanced", "mp3_balanced")
    out["awq"] = {k: decide("awq_w4_us", f"awq_w4_{k}") for k in ("balanced", "worst")}
    (TAB / f"analysis_{model}.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "per_condition"}, indent=1))


if __name__ == "__main__":
    {"valgroups": valgroups, "analyze": analyze}[sys.argv[1]](sys.argv[2])
