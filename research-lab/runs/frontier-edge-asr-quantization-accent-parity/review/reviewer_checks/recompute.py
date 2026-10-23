"""Reviewer check: recompute the gaps, penalties, intervals and verdicts from the per-utterance table
(utt_errors_small.csv), replicating code/score.py's speaker-clustered paired bootstrap exactly, then stress it.

Variants:
  baseline        as the study (must reproduce analysis_small.json)
  capped          per-utterance errors capped at the reference length (WER <= 100 % per utterance)
  noloop_any      drop utterances flagged as looped in ANY condition (same utterance set for every condition)
  short_only      segments <= 30 s (short-form decoding)
  long_only       segments > 30 s (sequential long-form decoding)
  no_insertions   errors = substitutions + deletions
Plus: literal (re-ranked) gap penalties; a split-half check of the selection / regression-to-the-mean bias in
fixing worst-3/best-3 on FP16 test WER; per-seed decomposition; a bootstrap that also resamples calibration draws;
the utterances that drive the biggest group swings.
"""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RUN = HERE.parents[1]
B, SEED = 2000, 20261022
df = pd.read_csv(HERE / "utt_errors_small.csv", keep_default_na=False)
conds = sorted(df.cond.unique())
base = df[df.cond == "fp16"].sort_values(["shard", "row"]).reset_index(drop=True)
U = len(base)
ukey = {k: i for i, k in enumerate(zip(base.shard, base.row))}
spk = sorted(base.speaker.unique())
spk_i = {s: i for i, s in enumerate(spk)}
sgroup = base.groupby("speaker").group.first().reindex(spk)
named = sorted(g for g in sgroup.unique() if g != "other")
G = np.stack([(sgroup == g).to_numpy(float) for g in named], axis=1)
u_spk = base.speaker.map(spk_i).to_numpy()
u_long = base.long.to_numpy(bool)
nref_u = base.nref.to_numpy(float)
# utterance x condition matrices
ERR, SUB, DEL, INS, LOOP, HYPW = ({} for _ in range(6))
for c in conds:
    d = df[df.cond == c].sort_values(["shard", "row"]).reset_index(drop=True)
    assert len(d) == U and (d.shard.to_numpy() == base.shard.to_numpy()).all()
    ERR[c], SUB[c], DEL[c], INS[c] = (d[k].to_numpy(float) for k in ("err", "sub", "del", "ins"))
    LOOP[c], HYPW[c] = d.loop.to_numpy(bool), d.hyp_words.to_numpy(float)

# the study's bootstrap weights, reproduced exactly
rng = np.random.default_rng(SEED)
C = np.zeros((B + 1, len(spk)))
C[0] = 1.0
for gname in list(sgroup.unique()):
    idx = np.where((sgroup == gname).to_numpy())[0]
    draws = rng.integers(0, len(idx), size=(B, len(idx)))
    for b in range(B):
        np.add.at(C[b + 1], idx[draws[b]], 1.0)


def speaker_sums(x, mask):
    out = np.zeros(len(spk))
    np.add.at(out, u_spk[mask], x[mask])
    return out


def ci(x):
    if len(x) < 2:
        return [None, None]
    return [round(float(np.percentile(x[1:], 2.5)), 4), round(float(np.percentile(x[1:], 97.5)), 4)]


def analyze(err_of, mask=None, fixed_groups=None, Cw=C):
    """err_of(c) -> per-utterance errors; mask -> utterance subset. Returns stats per condition and decisions."""
    mask = np.ones(U, bool) if mask is None else mask
    N = speaker_sums(nref_u, mask)
    E = {c: speaker_sums(err_of(c), mask) for c in conds}
    wer_fp = (E["fp16"] @ G) / (N @ G)
    if fixed_groups is None:
        order = np.argsort(wer_fp)
        best3, worst3 = order[:3], order[-3:]
    else:
        best3, worst3 = fixed_groups
    S, P = {}, {}
    for c in conds:
        e, n = Cw * E[c], Cw * N
        eg, ng = e @ G, n @ G
        w3 = eg[:, worst3].sum(1) / ng[:, worst3].sum(1)
        b3 = eg[:, best3].sum(1) / ng[:, best3].sum(1)
        wg = eg / ng
        S[c] = {"gap": w3 - b3, "w3": w3, "b3": b3, "agg": e.sum(1) / n.sum(1), "lit": wg.max(1) - wg.min(1)}
    for c in conds:
        P[c] = S[c]["gap"] - S["fp16"]["gap"]
        S[c]["litP"] = S[c]["lit"] - S["fp16"]["lit"]

    def comp(prefix):
        cs = [c for c in conds if re.fullmatch(prefix + r"_s\d", c)]
        return (np.mean([P[c] for c in cs], axis=0), cs) if cs else (None, [])

    def decide(ref, arm):
        pr, rcs = comp(ref)
        pa, acs = comp(arm)
        if pr is None or pa is None:
            return None
        d = pr - pa
        R = 1 - pa[0] / pr[0] if pr[0] != 0 else float("nan")
        control = ci(pr)[0] > 0
        dagg = np.mean([S[c]["agg"] for c in acs], 0) - np.mean([S[c]["agg"] for c in rcs], 0)
        seedR = {}
        for c in acs:
            s = c.rsplit("_", 1)[1]
            rc = f"{ref}_{s}"
            if rc in P and P[rc][0] != 0:
                seedR[s] = round(float(1 - P[c][0] / P[rc][0]), 3)
        if control and R >= 0.5 and ci(d)[0] > 0 and dagg[0] <= 0.005:
            v = "Supported" + (" (fragile)" if any(r < 0.25 for r in seedR.values()) else "")
        elif control and ci(d)[1] < 0.5 * pr[0]:
            v = "Refuted"
        else:
            v = "Inconclusive"
        return {"verdict": v, "P_ref": round(float(pr[0]), 4), "P_ref_ci": ci(pr), "control": bool(control),
                "P_arm": round(float(pa[0]), 4), "P_arm_ci": ci(pa), "R": round(float(R), 3), "diff": round(float(d[0]), 4),
                "diff_ci": ci(d), "dagg": round(float(dagg[0]), 4), "seed_R": seedR,
                "seed_P_ref": {c: round(float(P[c][0]), 4) for c in rcs}, "seed_P_arm": {c: round(float(P[c][0]), 4) for c in acs}}

    out = {"worst3": [named[i] for i in worst3], "best3": [named[i] for i in best3],
           "per_condition": {c: {"agg": round(float(S[c]["agg"][0]), 4), "gap": round(float(S[c]["gap"][0]), 4),
                                 "penalty": round(float(P[c][0]), 4), "penalty_ci": ci(P[c]),
                                 "w3": round(float(S[c]["w3"][0]), 4), "b3": round(float(S[c]["b3"][0]), 4),
                                 "literal_gap": round(float(S[c]["lit"][0]), 4), "literal_penalty": round(float(S[c]["litP"][0]), 4),
                                 "literal_penalty_ci": ci(S[c]["litP"])} for c in conds}}
    if Cw.shape[0] > 1:     # decisions need the bootstrap; the split-half check only needs point estimates
        out.update({"H1_w4": decide("gptq_w4_us", "gptq_w4_balanced"), "H2_w4": decide("gptq_w4_us", "gptq_w4_worst"),
                    "H1_w3": decide("gptq_w3_us", "gptq_w3_balanced"), "H2_w3": decide("gptq_w3_us", "gptq_w3_worst"),
                    "H3_w4": decide("gptq_w4_us", "mp_us"), "H3_w3": decide("gptq_w3_us", "mp3_us")})
    return out, (best3, worst3), S, P


results = {}
variants = {
    "baseline": (lambda c: ERR[c], None),
    "capped": (lambda c: np.minimum(ERR[c], nref_u), None),
    "noloop_any": (lambda c: ERR[c], ~np.any(np.stack([LOOP[c] for c in conds]), axis=0)),
    "short_only": (lambda c: ERR[c], ~u_long),
    "long_only": (lambda c: ERR[c], u_long),
    "no_insertions": (lambda c: SUB[c] + DEL[c], None),
}
fixed = None
for name, (f, mask) in variants.items():
    # groups fixed by FP16 on the SAME variant's data, as the plan fixes them by FP16 test WER (baseline groups are also
    # applied to the subsets so that the comparison is like for like)
    out, grp, S, P = analyze(f, mask, fixed_groups=fixed if name in ("short_only", "long_only") else None)
    if name == "baseline":
        fixed = grp
    results[name] = out
    print(f"\n=== {name} ===  worst3={out['worst3']} best3={out['best3']}"
          + (f"  utterances={int(mask.sum())}/{U}" if mask is not None else ""))
    for h in ("H1_w4", "H2_w4", "H1_w3", "H2_w3", "H3_w4", "H3_w3"):
        d = out[h]
        print(f" {h:6s} {d['verdict']:22s} P_ref {100*d['P_ref']:+5.1f} {[round(100*x,1) for x in d['P_ref_ci']]} "
              f"P_arm {100*d['P_arm']:+5.1f} R {d['R']:+.2f} diff {100*d['diff']:+5.1f} {[round(100*x,1) for x in d['diff_ci']]} "
              f"dagg {100*d['dagg']:+.2f} seedR {d['seed_R']}")
    for c in ("rtn_w4", "gptq_w4_us_s0", "gptq_w4_us_s1", "gptq_w4_us_s2", "gptq_w3_us_s0", "gptq_w3_us_s1", "gptq_w3_us_s2",
              "gptq_w3_balanced_s0", "gptq_w3_balanced_s1", "gptq_w3_balanced_s2", "gptq_w3_worst_s0", "gptq_w3_worst_s1", "gptq_w3_worst_s2"):
        v = out["per_condition"][c]
        print(f"   {c:22s} agg {100*v['agg']:5.1f} w3 {100*v['w3']:5.1f} b3 {100*v['b3']:5.1f} gap {100*v['gap']:5.1f} "
              f"pen {100*v['penalty']:+5.1f} {[round(100*x,1) for x in v['penalty_ci']]} | literal gap {100*v['literal_gap']:5.1f} "
              f"litpen {100*v['literal_penalty']:+5.1f} {[round(100*x,1) for x in v['literal_penalty_ci']]}")

# ---- loop / garbage diagnostics ----------------------------------------------------------------------------------
print("\n=== loop / runaway diagnostics (share of total errors; ins = insertions) ===")
diag = {}
for c in conds:
    tot = ERR[c].sum()
    lp = LOOP[c]
    over = ERR[c] > nref_u
    diag[c] = {"loop_utts": int(lp.sum()), "loop_err_share": round(float(ERR[c][lp].sum() / tot), 4),
               "ins_share": round(float(INS[c].sum() / tot), 4), "utts_over_100pct": int(over.sum()),
               "excess_over_cap": round(float((ERR[c] - np.minimum(ERR[c], nref_u)).sum() / tot), 4),
               "long_err_share": round(float(ERR[c][u_long].sum() / tot), 4), "max_ins_one_utt": int(INS[c].max()),
               "empty_hyps": int((HYPW[c] == 0).sum())}
    if c in ("fp16", "rtn_w4", "gptq_w4_us_s0", "gptq_w4_us_s1", "gptq_w4_us_s2", "gptq_w4_balanced_s0", "gptq_w3_us_s0",
             "gptq_w3_us_s1", "gptq_w3_us_s2", "gptq_w3_balanced_s0", "gptq_w3_balanced_s1", "gptq_w3_worst_s0", "gptq_w3_worst_s1",
             "gptq_w3_worst_s2", "mp3_us_s0"):
        print(f" {c:22s} {diag[c]}")
print(f" long-form share of reference words: {nref_u[u_long].sum() / nref_u.sum():.3f}")

# ---- which utterances drive the biggest group swings ---------------------------------------------------------------
print("\n=== drivers of group swings: top utterances by error increase over FP16 ===")
drivers = {}
for c, g in [("gptq_w4_us_s0", "Latin American"), ("gptq_w4_us_s1", "Latin American"), ("gptq_w4_us_s2", "Latin American"),
             ("gptq_w4_us_s0", "Southern British English"), ("gptq_w4_us_s2", "Chinese"),
             ("gptq_w3_worst_s1", "Bulgarian"), ("gptq_w3_worst_s0", "Bulgarian"), ("gptq_w3_us_s0", "Southern British English"),
             ("gptq_w3_us_s2", "Scottish English"), ("gptq_w3_balanced_s1", "Irish English"),
             ("gptq_w3_us_s0", "Jamaican English"), ("gptq_w3_us_s1", "Vietnamese"), ("gptq_w3_us_s1", "Jamaican English")]:
    m = (base.group == g).to_numpy()
    delta = ERR[c] - ERR["fp16"]
    gd = delta[m].sum()
    top = np.argsort(-delta * m)[:3]
    rows = [{"utt": f"{base.shard[i]}:{base.row[i]}", "spk": base.speaker[i], "dur": round(float(base.dur[i]), 1), "nref": int(nref_u[i]),
             "err_fp16": int(ERR["fp16"][i]), "err_c": int(ERR[c][i]), "ins_c": int(INS[c][i]), "hyp_words": int(HYPW[c][i]),
             "loop": bool(LOOP[c][i])} for i in top]
    share = sum(delta[i] for i in top) / gd if gd else float("nan")
    drivers[f"{c}|{g}"] = {"group_err_change": int(gd), "group_nref": int(nref_u[m].sum()), "top3_share_of_change": round(float(share), 2), "top3": rows}
    print(f" {c} / {g}: group errors {int(ERR['fp16'][m].sum())} -> {int(ERR[c][m].sum())} (nref {int(nref_u[m].sum())}); "
          f"top-3 utterances carry {100*share:.0f}% of the change")
    for r in rows:
        print("    ", r)

# ---- per-seed decomposition at W3 -----------------------------------------------------------------------------------
print("\n=== W3 per-seed decomposition (vs the same-seed US-only draw; points) ===")
pc = results["baseline"]["per_condition"]
for arm in ("balanced", "worst"):
    for s in (0, 1, 2):
        u, a = pc[f"gptq_w3_us_s{s}"], pc[f"gptq_w3_{arm}_s{s}"]
        dw, db = 100 * (u["w3"] - a["w3"]), 100 * (a["b3"] - u["b3"])
        print(f" {arm:9s} s{s}: worst3 improves {dw:+5.1f}, best3 worsens {db:+5.1f}, narrowing {dw+db:+5.1f}, "
              f"share from best worsening {db/(dw+db) if dw+db else float('nan'):.2f}; P_us {100*u['penalty']:+.1f} P_arm {100*a['penalty']:+.1f}")

# ---- bootstrap that also resamples the calibration draws -------------------------------------------------------------
print("\n=== speaker + calibration-draw bootstrap for the W3 penalty differences ===")
_, _, S0, P0 = analyze(lambda c: ERR[c])
rng2 = np.random.default_rng(SEED + 1)
drawboot = {}
for arm in ("balanced", "worst"):
    diffs = np.empty(B)
    for b in range(B):
        sr = rng2.integers(0, 3, 3)
        sa = rng2.integers(0, 3, 3)
        pr = np.mean([P0[f"gptq_w3_us_s{s}"][b + 1] for s in sr])
        pa = np.mean([P0[f"gptq_w3_{arm}_s{s}"][b + 1] for s in sa])
        diffs[b] = pr - pa
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    drawboot[arm] = [round(float(lo), 4), round(float(hi), 4)]
    # and a plain t-interval on the three per-seed differences (df = 2)
    ds = np.array([P0[f"gptq_w3_us_s{s}"][0] - P0[f"gptq_w3_{arm}_s{s}"][0] for s in range(3)])
    tci = (ds.mean() - 4.303 * ds.std(ddof=1) / np.sqrt(3), ds.mean() + 4.303 * ds.std(ddof=1) / np.sqrt(3))
    print(f" {arm:9s}: speaker-only CI {[round(100*x,1) for x in results['baseline'][('H1_w3' if arm=='balanced' else 'H2_w3')]['diff_ci']]}  "
          f"speaker+draw CI {[round(100*x,1) for x in drawboot[arm]]}  per-seed diffs {np.round(100*ds,1).tolist()}  t-CI(df=2) {[round(100*x,1) for x in tci]}")

# ---- split-half check of selection bias -----------------------------------------------------------------------------
print("\n=== split-half: groups chosen on one half of each speaker's utterances, penalty measured on the other ===")
rng3 = np.random.default_rng(7)
targets = {"rtn_w4": ["rtn_w4"], "gptq_w4_us": [f"gptq_w4_us_s{s}" for s in range(3)], "gptq_w3_us": [f"gptq_w3_us_s{s}" for s in range(3)],
           "gptq_w3_balanced": [f"gptq_w3_balanced_s{s}" for s in range(3)], "gptq_w3_worst": [f"gptq_w3_worst_s{s}" for s in range(3)]}
acc = {k: {"in": [], "out": []} for k in targets}
C1 = C[:1]
for rep in range(20):
    half = np.zeros(U, int)
    for s in range(len(spk)):
        ids = np.where(u_spk == s)[0]
        rng3.shuffle(ids)
        half[ids[: len(ids) // 2]] = 1
    for h in (0, 1):
        sel_mask, eval_mask = half == h, half != h
        N_sel = speaker_sums(nref_u, sel_mask)
        wer_sel = (speaker_sums(ERR["fp16"], sel_mask) @ G) / (N_sel @ G)
        o = np.argsort(wer_sel)
        grp_sel = (o[:3], o[-3:])
        for k, cs in targets.items():
            out_o, _, _, _ = analyze(lambda c: ERR[c], eval_mask, fixed_groups=grp_sel, Cw=C1)
            out_i, _, _, _ = analyze(lambda c: ERR[c], eval_mask, fixed_groups=None, Cw=C1)
            acc[k]["out"].append(np.mean([out_o["per_condition"][c]["penalty"] for c in cs]))
            acc[k]["in"].append(np.mean([out_i["per_condition"][c]["penalty"] for c in cs]))
splithalf = {}
for k in targets:
    i, o = np.array(acc[k]["in"]), np.array(acc[k]["out"])
    splithalf[k] = {"in_sample_penalty": round(float(100 * i.mean()), 2), "out_of_sample_penalty": round(float(100 * o.mean()), 2),
                    "bias_in_minus_out": round(float(100 * (i - o).mean()), 2), "sd_out": round(float(100 * o.std()), 2)}
    print(f" {k:18s} in-sample {100*i.mean():+5.2f}  out-of-sample {100*o.mean():+5.2f}  (in - out) {100*(i-o).mean():+5.2f} pp, "
          f"sd across splits {100*o.std():.2f}")

json.dump({"variants": results, "diagnostics": diag, "drivers": drivers, "draw_bootstrap_diff_ci": drawboot, "split_half": splithalf},
          open(HERE / "recompute.json", "w"), indent=1, default=str)
