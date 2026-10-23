"""D4 (after the independent review): what the preregistered statistics are made of, and how robust they are.

  robustness.py utt MODEL      per-utterance substitutions, deletions, insertions, hits, hypothesis words and the loop
                               flag for every decoded test condition -> data/utt/<MODEL>.parquet
  robustness.py analyze MODEL  -> results/tables/robustness_<MODEL>.json

Scoring variants (the preregistered statistic is "prereg"):
  capped     errors per utterance capped at its reference length (utterance WER <= 100%)
  no_loops   utterances looped in any condition of this model removed (loop as plan section 5)
  sub_del    substitutions + deletions only (insertions dropped)
  short / long   segments of at most / over 30 s (decode.py's split), prereg scoring, preregistered groups
For each variant the worst-3 / best-3 groups are re-fixed from FP16 on that variant's data, as the plan fixes them
from FP16 test WER; the preregistered groups held fixed are also reported. The same speaker-bootstrap weights as
score.py (B = 2,000, seed 20261022) are used throughout.

Also: a bootstrap that resamples the three calibration draws of each composition as well as speakers; literal
(re-ranked) gap penalties; a split-half estimate of the bias from choosing the six groups on the same FP16 data the
penalties are measured on; per-utterance drivers of each condition's change (identifiers and counts, no text).
"""
import json
import re
import sys
from pathlib import Path

import jiwer
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import score  # noqa: E402

RUN = score.RUN
UTT = RUN / "data" / "utt"
B, SEED = score.B, score.SEED


def utt(model, split="test"):
    UTT.mkdir(parents=True, exist_ok=True)
    man = pd.read_csv(score.MAN / {"test": "eval_segments.csv", "cv": "cv_segments.csv"}[split], keep_default_na=False)
    man = man[(man.split == split) & (man.text != "IGNORE_TIME_SEGMENT_IN_SCORING")]
    man = man.assign(ref_n=man.text.map(score.norm))
    man = man[man.ref_n.str.len() > 0]
    rows = []
    for c in score.conditions(model, split):
        h = pd.read_json(score.HYP / model / f"{c}_{split}.jsonl", lines=True)
        d = man.merge(h, on=["shard", "row"], how="left", validate="1:1")
        assert d.hyp.notna().all(), c
        for r in d.itertuples():
            y = score.norm(r.hyp)
            o = jiwer.process_words(r.ref_n, y if y else "")
            rows.append((c, r.shard, r.row, r.speaker, r.group, r.dur, o.substitutions, o.deletions, o.insertions,
                         o.hits, len(y.split()), score.looped(y, r.ref_n)))
        print(c, flush=True)
    out = pd.DataFrame(rows, columns=["cond", "shard", "row", "speaker", "group", "dur", "sub", "del", "ins", "hits",
                                      "hyp_words", "loop"])
    out.to_parquet(UTT / (f"{model}.parquet" if split == "test" else f"{model}_{split}.parquet"), index=False)
    print(len(out), "rows")


def load(model, split="test"):
    d = pd.read_parquet(UTT / (f"{model}.parquet" if split == "test" else f"{model}_{split}.parquet"))
    conds = sorted(d.cond.unique())
    base = d[d.cond == "fp16"].sort_values(["shard", "row"]).reset_index(drop=True)
    X = {}
    for c in conds:
        x = d[d.cond == c].sort_values(["shard", "row"]).reset_index(drop=True)
        assert (x.shard.to_numpy() == base.shard.to_numpy()).all() and (x.row.to_numpy() == base.row.to_numpy()).all()
        X[c] = x
    return conds, base, X


class Panel:
    """Speaker-level sums for one scoring variant, with score.py's bootstrap weights."""

    def __init__(self, base, err, mask, C, spk, sgroup, named, groups=None):
        sidx = pd.Index(spk).get_indexer(base.speaker)
        nref = (base["sub"] + base["del"] + base["hits"]).to_numpy(float)
        self.N = np.bincount(sidx[mask], nref[mask], minlength=len(spk))
        self.E = {c: np.bincount(sidx[mask], e[mask], minlength=len(spk)) for c, e in err.items()}
        self.G = np.stack([(sgroup == g).to_numpy(float) for g in named], axis=1)
        self.C, self.named = C, named
        if groups is None:
            w = (self.E["fp16"] @ self.G) / (self.N @ self.G)
            o = np.argsort(w)
            groups = (o[:3], o[-3:])
        self.best3, self.worst3 = groups
        self.S = {c: self.stats(c) for c in err}
        self.P = {c: self.S[c]["gap"] - self.S["fp16"]["gap"] for c in err}
        self.PL = {c: self.S[c]["literal"] - self.S["fp16"]["literal"] for c in err}

    def stats(self, c):
        eg, ng = (self.C * self.E[c]) @ self.G, (self.C * self.N) @ self.G
        wg = eg / ng
        w3 = eg[:, self.worst3].sum(1) / ng[:, self.worst3].sum(1)
        b3 = eg[:, self.best3].sum(1) / ng[:, self.best3].sum(1)
        return {"gap": w3 - b3, "agg": (self.C * self.E[c]).sum(1) / (self.C * self.N).sum(1),
                "literal": wg.max(1) - wg.min(1)}

    def comp(self, prefix, lit=False):
        cs = [c for c in self.P if re.fullmatch(prefix + r"_s\d", c)]
        src = self.PL if lit else self.P
        return (np.mean([src[c] for c in cs], axis=0), cs) if cs else (None, [])


def ci(x):
    return [round(float(np.percentile(x[1:], 2.5)), 5), round(float(np.percentile(x[1:], 97.5)), 5)]


def decide(p, ref, arm):
    """score.py's decision rule, with R and seed R left null when the control fails or P(ref) <= 0 (D4)."""
    pr, rcs = p.comp(ref)
    pa, acs = p.comp(arm)
    if pr is None or pa is None:
        return None
    d = pr - pa
    control = ci(pr)[0] > 0
    agg = lambda cs: np.mean([p.S[c]["agg"] for c in cs], axis=0)
    dagg = agg(acs) - agg(rcs)
    R = 1 - pa[0] / pr[0] if (control and pr[0] > 0) else None
    seedR = {}
    for c in acs:
        rc = f"{ref}_{c.rsplit('_', 1)[1]}"
        if rc in p.P:
            seedR[c[-2:]] = round(float(1 - p.P[c][0] / p.P[rc][0]), 4) if (control and p.P[rc][0] > 0) else None
    if control and R is not None and R >= 0.5 and ci(d)[0] > 0 and dagg[0] <= 0.005:
        v = "Supported" + (" (fragile across seeds)" if any(r is not None and r < 0.25 for r in seedR.values()) else "")
    elif control and ci(d)[1] < 0.5 * pr[0]:
        v = "Refuted"
    else:
        v = "Inconclusive"
    return {"verdict": v, "ref_penalty": round(float(pr[0]), 5), "ref_penalty_ci": ci(pr), "control_holds": bool(control),
            "arm_penalty": round(float(pa[0]), 5), "arm_penalty_ci": ci(pa),
            "R": None if R is None else round(float(R), 4), "difference": round(float(d[0]), 5), "difference_ci": ci(d),
            "agg_change": round(float(dagg[0]), 5), "seed_R": seedR}


def tests(model, split="test"):
    if split == "cv":                                       # D5: the replication tests H1/H2 at W3 only
        return {"H1_w3": ("gptq_w3_us", "gptq_w3_balanced"), "H2_w3": ("gptq_w3_us", "gptq_w3_worst")}
    if model == "small":
        return {"H1_w4": ("gptq_w4_us", "gptq_w4_balanced"), "H2_w4": ("gptq_w4_us", "gptq_w4_worst"),
                "H1_w3": ("gptq_w3_us", "gptq_w3_balanced"), "H2_w3": ("gptq_w3_us", "gptq_w3_worst"),
                "H3_w3": ("gptq_w3_us", "mp3_us")}
    return {"H4_w4_balanced": ("gptq_w4_us", "gptq_w4_balanced"), "H4_w4_worst": ("gptq_w4_us", "gptq_w4_worst"),
            "H4_w3_balanced": ("gptq_w3_us", "gptq_w3_balanced"), "H4_w3_worst": ("gptq_w3_us", "gptq_w3_worst")}


def analyze(model, split="test"):
    conds, base, X = load(model, split)
    spk = sorted(base.speaker.unique())
    sgroup = base.groupby("speaker").group.first().reindex(spk)
    named = sorted(g for g in sgroup.unique() if g != "other")
    rng = np.random.default_rng(SEED)                       # score.py's weights, reproduced exactly
    C = np.zeros((B + 1, len(spk)))
    C[0] = 1.0
    for gname in list(sgroup.unique()):
        idx = np.where((sgroup == gname).to_numpy())[0]
        draws = rng.integers(0, len(idx), size=(B, len(idx)))
        for b in range(B):
            np.add.at(C[b + 1], idx[draws[b]], 1.0)

    nref = (base["sub"] + base["del"] + base["hits"]).to_numpy(float)
    ERR = {c: (X[c]["sub"] + X[c]["del"] + X[c]["ins"]).to_numpy(float) for c in conds}
    SD = {c: (X[c]["sub"] + X[c]["del"]).to_numpy(float) for c in conds}
    LOOP = {c: X[c].loop.to_numpy(bool) for c in conds}
    anyloop = np.any(np.stack([LOOP[c] for c in conds]), axis=0)
    allm = np.ones(len(base), bool)
    long_ = base.dur.to_numpy() > 30

    prereg = Panel(base, ERR, allm, C, spk, sgroup, named)
    fixed = (prereg.best3, prereg.worst3)
    variants = {
        "prereg": (ERR, allm), "capped": ({c: np.minimum(e, nref) for c, e in ERR.items()}, allm),
        "no_loops": (ERR, ~anyloop), "sub_del": (SD, allm), "short": (ERR, ~long_), "long": (ERR, long_)}
    out = {"model": model, "utterances": int(len(base)), "utterances_looped_in_any_condition": int(anyloop.sum()),
           "variants": {}}
    T = tests(model, split)
    for name, (err, mask) in variants.items():
        res = {}
        for label, groups in (("refixed", None), ("prereg_groups", fixed)):
            if name in ("short", "long") and label == "refixed":
                continue
            p = Panel(base, err, mask, C, spk, sgroup, named, groups)
            res[label] = {"worst3": [named[i] for i in p.worst3], "best3": [named[i] for i in p.best3],
                          "penalties": {k: {"penalty": round(float(v[0]), 5), "ci": ci(v)} for k, v in
                                        ((pre, p.comp(pre)[0]) for pre in sorted({re.sub(r"_s\d$", "", c) for c in conds}))
                                        if v is not None},
                          "tests": {t: decide(p, r, a) for t, (r, a) in T.items()}}
        out["variants"][name] = res

    # --- the calibration draws resampled as well as speakers -----------------------------------------------------
    rng2 = np.random.default_rng(SEED + 1)
    out["draw_bootstrap"] = {}
    for t, (r, a) in T.items():
        pr, rcs = prereg.comp(r)
        pa, acs = prereg.comp(a)
        if pr is None or pa is None:
            continue
        Pr, Pa = np.stack([prereg.P[c] for c in rcs]), np.stack([prereg.P[c] for c in acs])
        dd = np.empty(B + 1)
        dd[0] = pr[0] - pa[0]
        for b in range(1, B + 1):
            dd[b] = Pr[rng2.integers(0, len(rcs), len(rcs)), b].mean() - Pa[rng2.integers(0, len(acs), len(acs)), b].mean()
        per_seed = [round(float(prereg.P[rc][0] - prereg.P[ac][0]), 5) for rc, ac in zip(rcs, acs)]
        out["draw_bootstrap"][t] = {"difference": round(float(dd[0]), 5), "speaker_ci": ci(pr - pa),
                                    "speaker_and_draw_ci": ci(dd), "per_seed_difference": per_seed}

    # --- literal (re-ranked per condition) gap penalties ----------------------------------------------------------
    out["literal_gap_penalty"] = {}
    for pre in sorted({re.sub(r"_s\d$", "", c) for c in conds if c != "fp16"}):
        v, cs = prereg.comp(pre, lit=True)
        if v is None:
            v, cs = prereg.PL[pre], [pre]
        out["literal_gap_penalty"][pre] = {"penalty": round(float(v[0]), 5), "ci": ci(v)}

    # --- loop diagnostics ---------------------------------------------------------------------------------------
    out["loops"] = {}
    for c in conds:
        tot = ERR[c].sum()
        out["loops"][c] = {"loop_rate": round(float(LOOP[c].mean()), 5),
                           "error_share_in_looped": round(float(ERR[c][LOOP[c]].sum() / tot), 4),
                           "insertion_share": round(float(X[c]["ins"].sum() / tot), 4),
                           "excess_over_cap_share": round(float((ERR[c] - np.minimum(ERR[c], nref)).sum() / tot), 4)}

    # --- split-half: choose the six groups on one half of each speaker's utterances, measure on the other -------
    rng3 = np.random.default_rng(SEED + 2)
    sh = {pre: [] for pre in sorted({re.sub(r"_s\d$", "", c) for c in conds if c != "fp16"})}
    Cobs = C[:1]
    for _ in range(20):
        half = rng3.random(len(base)) < 0.5
        pa_ = Panel(base, ERR, half, Cobs, spk, sgroup, named)
        pb_out = Panel(base, ERR, ~half, Cobs, spk, sgroup, named, (pa_.best3, pa_.worst3))
        pb_in = Panel(base, ERR, ~half, Cobs, spk, sgroup, named)
        for pre in sh:
            vo, _ = pb_out.comp(pre)
            vi, _ = pb_in.comp(pre)
            if vo is None:
                vo, vi = pb_out.P[pre], pb_in.P[pre]
            sh[pre].append(float(vo[0] - vi[0]))
    out["split_half_bias"] = {k: {"mean": round(float(np.mean(v)), 5), "range": [round(float(min(v)), 5), round(float(max(v)), 5)]}
                              for k, v in sh.items()}

    # --- per-utterance drivers of each condition's change in the six groups (no text) ---------------------------
    six = set(named[i] for i in list(prereg.worst3) + list(prereg.best3))
    out["drivers"] = {}
    for c in conds:
        if c == "fp16":
            continue
        dlt = ERR[c] - ERR["fp16"]
        rows = {}
        for g in sorted(six):
            m = (base.group == g).to_numpy()
            tot = dlt[m].sum()
            top = np.argsort(-dlt * m)[:3]
            rows[g] = {"group_wer_fp16": round(float(ERR["fp16"][m].sum() / nref[m].sum()), 4),
                       "group_wer": round(float(ERR[c][m].sum() / nref[m].sum()), 4),
                       "extra_errors": int(tot),
                       "top1_share": round(float(dlt[top[0]] / tot), 3) if tot > 0 else None,
                       "top3_share": round(float(dlt[top].sum() / tot), 3) if tot > 0 else None,
                       "top1": {"utt": f"{base.shard[top[0]][:10]}:{base.row[top[0]]}", "speaker": base.speaker[top[0]],
                                "ref_words": int(nref[top[0]]), "hyp_words": int(X[c].hyp_words[top[0]]),
                                "fp16_hyp_words": int(X["fp16"].hyp_words[top[0]]), "errors": int(ERR[c][top[0]]),
                                "fp16_errors": int(ERR["fp16"][top[0]]), "loop": bool(LOOP[c][top[0]])}}
        out["drivers"][c] = rows
    (score.TAB / (f"robustness_{model}.json" if split == "test" else f"robustness_{model}_{split}.json")).write_text(json.dumps(out, indent=1))
    pv = out["variants"]
    for name in pv:
        for label, r in pv[name].items():
            print(f"{name:9s} {label:13s} worst3={r['worst3']} best3={r['best3']}")
            for t, d in r["tests"].items():
                if d:
                    print(f"   {t:15s} {d['verdict']:30s} Pref {100*d['ref_penalty']:+.1f} {[round(100*x,1) for x in d['ref_penalty_ci']]}"
                          f" diff {100*d['difference']:+.1f} {[round(100*x,1) for x in d['difference_ci']]} R {d['R']}")
    print(json.dumps(out["draw_bootstrap"], indent=1))


if __name__ == "__main__":
    {"utt": utt, "analyze": analyze}[sys.argv[1]](*sys.argv[2:])
