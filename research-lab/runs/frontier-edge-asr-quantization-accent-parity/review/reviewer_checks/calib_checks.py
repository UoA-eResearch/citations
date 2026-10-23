"""Reviewer check: calibration sets (plan section 3). Read-only; nothing under the study is written except this
directory's calib_checks.json.

Checks: speaker disjointness from test; window construction (one speaker, consecutive segments, 20-30 s); matched
durations; per-composition window counts (US-only, 2 per accent, worst allocation); exact reproduction of the saved
draws from code/manifest.py with the recorded seeds; the largest-remainder allocation; teacher-forcing transcripts;
how different the worst-weighted and balanced sets really are; validation-vs-test accent WER agreement.
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd


def spearmanr(x, y):
    rx, ry = pd.Series(x).rank().to_numpy(), pd.Series(y).rank().to_numpy()
    return float(np.corrcoef(rx, ry)[0, 1]), float("nan")

RUN = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RUN / "code"))
import manifest  # noqa: E402  (study code; only pure functions are called, nothing is written)

MAN = RUN / "data" / "manifest"
TAB = RUN / "results" / "tables"
out = {}

seg = pd.read_csv(MAN / "edacc_all_segments.csv", keep_default_na=False)
seg = seg[seg.text != "IGNORE_TIME_SEGMENT_IN_SCORING"].reset_index(drop=True)
key = {(r.shard, int(r.row)): r for r in seg.itertuples()}
test_spk = set(seg[seg.split == "test"].speaker)
val_spk = set(seg[seg.split == "validation"].speaker)
out["split_speaker_overlap"] = sorted(test_spk & val_spk)

# order of segments per speaker in corpus order, to check consecutiveness
order = defaultdict(list)
for r in seg[seg.split == "validation"].sort_values(["shard", "row"]).itertuples():
    order[r.speaker].append((r.shard, int(r.row)))
pos = {spk: {k: i for i, k in enumerate(v)} for spk, v in order.items()}

sets = {}
for comp in ("us", "balanced", "worst_small"):
    for s in (0, 1, 2):
        sets[f"{comp}_s{s}"] = json.loads((MAN / f"calib_{comp}_s{s}.json").read_text())

checks = {}
for name, W in sets.items():
    c = {"windows": len(W), "speech_s": round(sum(w["dur"] for w in W), 1), "speakers": len({w["speaker"] for w in W}),
         "bad_speaker": 0, "bad_consecutive": 0, "bad_duration": 0, "bad_segment": 0, "in_test": 0, "not_validation": 0}
    acc = Counter()
    for w in W:
        acc[w["accent"]] += 1
        spk = w["speaker"]
        if spk in test_spk:
            c["in_test"] += 1
        if spk not in val_spk:
            c["not_validation"] += 1
        rows = [key[tuple(sg)] for sg in w["segs"]]
        if any(r.speaker != spk or r.split != "validation" for r in rows):
            c["bad_speaker"] += 1
        # consecutive in the speaker's corpus order, after the <=30 s / >=0.5 s filter used by manifest.windows
        filt = [k for k in order[spk] if 0.5 <= key[k].dur <= 30.0]
        fpos = {k: i for i, k in enumerate(filt)}
        idx = [fpos[tuple(sg)] for sg in w["segs"]]
        if idx != list(range(idx[0], idx[0] + len(idx))):
            c["bad_consecutive"] += 1
        tot = sum(r.dur for r in rows)
        if not (20.0 <= tot <= 30.0) or abs(tot - w["dur"]) > 0.01:
            c["bad_duration"] += 1
        if any(r.dur > 30.0 or r.dur < 0.5 for r in rows):
            c["bad_segment"] += 1
    c["within_5pct_of_1200s"] = abs(c["speech_s"] - 1200) <= 60
    c["accents"] = dict(sorted(acc.items()))
    checks[name] = c
out["sets"] = checks

# matched durations across compositions
sp = [c["speech_s"] for c in checks.values()]
out["duration_spread_pct"] = round(100 * (max(sp) - min(sp)) / 1200, 2)

# reproduce the draws exactly with the study's own functions and seeds
W = manifest.windows(manifest.segments())
by = defaultdict(list)
for w in W:
    by[w["accent"]].append(w)
cal_groups = sorted(a for a in by if a != "Don't know")
alloc_saved = json.loads((TAB / "manifest_worst_small.json").read_text())["allocation"]
repro = {}
for s in (0, 1, 2):
    repro[f"us_s{s}"] = manifest.draw(by, {manifest.US: 48}, 1000 + s) == sets[f"us_s{s}"]
    repro[f"balanced_s{s}"] = manifest.draw(by, {a: 2 for a in cal_groups}, 2000 + s) == sets[f"balanced_s{s}"]
    repro[f"worst_small_s{s}"] = manifest.draw(by, alloc_saved, 3000 + s) == sets[f"worst_small_s{s}"]
out["draws_reproduced_from_seeds"] = repro
out["windows_available"] = {a: len(by[a]) for a in sorted(by)}
out["balanced_needs_2_per_accent_ok"] = all(len(by[a]) >= 2 for a in cal_groups)

# largest-remainder allocation recomputed
wer = json.loads((TAB / "fp16_validation_group_wer_small.json").read_text())
tot = sum(wer[a] for a in cal_groups)
raw = {a: 48 * wer[a] / tot for a in cal_groups}
alloc = {a: int(raw[a]) for a in cal_groups}
for a in sorted(cal_groups, key=lambda a: raw[a] - int(raw[a]), reverse=True):
    if sum(alloc.values()) >= 48:
        break
    alloc[a] += 1
out["worst_allocation_matches"] = alloc == alloc_saved
out["worst_allocation_raw"] = {a: round(raw[a], 2) for a in cal_groups}
out["worst_vs_balanced_window_moves"] = sum(abs(alloc[a] - 2) for a in cal_groups) // 2

# overlap of actual windows between compositions (same seed index is not the same seed stream, but check anyway)
def wk(w):
    return (w["speaker"], tuple(map(tuple, w["segs"])))
ov = {}
for s in (0, 1, 2):
    b = {wk(w) for w in sets[f"balanced_s{s}"]}
    wst = {wk(w) for w in sets[f"worst_small_s{s}"]}
    u = {wk(w) for w in sets[f"us_s{s}"]}
    ov[f"s{s}"] = {"balanced&worst": len(b & wst), "balanced&us": len(b & u), "worst&us": len(wst & u),
                   "balanced_speakers": len({w["speaker"] for w in sets[f"balanced_s{s}"]}),
                   "worst_speakers": len({w["speaker"] for w in sets[f"worst_small_s{s}"]}),
                   "speakers_shared_bal_worst": len({w["speaker"] for w in sets[f"balanced_s{s}"]} & {w["speaker"] for w in sets[f"worst_small_s{s}"]})}
out["window_overlap"] = ov

# teacher-forcing transcripts
ct = json.loads((RUN / "data" / "calib_text" / "small.json").read_text())
need = {f"{w['speaker']}|{w['segs'][0][0]}|{w['segs'][0][1]}" for W_ in sets.values() for w in W_}
def loopy(t):
    w = t.split()
    g = Counter(tuple(w[i:i + 3]) for i in range(len(w) - 2))
    return bool(g) and max(g.values()) >= 5
texts = [ct[k] for k in need if k in ct]
out["calib_text"] = {"cached_keys": len(ct), "needed_keys": len(need), "missing": len(need - set(ct)),
                     "empty": sum(1 for t in texts if not t.strip()), "looping_3gram_x5": sum(1 for t in texts if loopy(t)),
                     "words_min_median_max": [min(len(t.split()) for t in texts),
                                              sorted(len(t.split()) for t in texts)[len(texts) // 2],
                                              max(len(t.split()) for t in texts)]}

# validation vs test accent WER agreement (shared accents)
an = json.loads((TAB / "analysis_small.json").read_text())
shared = sorted(set(an["fp16_group_wer"]) & set(wer))
rho, p = spearmanr([wer[a] for a in shared], [an["fp16_group_wer"][a] for a in shared])
out["val_vs_test_accent_wer"] = {"shared_accents": shared, "spearman_rho": round(float(rho), 3), "p": round(float(p), 3),
                                 "validation_worst3": sorted(wer, key=wer.get)[-3:], "validation_best3": sorted(wer, key=wer.get)[:3],
                                 "test_worst3": an["worst3_fp16"], "test_best3": an["best3_fp16"],
                                 "pairs": {a: [wer[a], an["fp16_group_wer"][a]] for a in shared}}

# test speakers per group and minutes (for the limits section)
ev = pd.read_csv(MAN / "eval_segments.csv", keep_default_na=False)
ev = ev[ev.text != "IGNORE_TIME_SEGMENT_IN_SCORING"]
out["test_groups"] = {g: {"speakers": int(d.speaker.nunique()), "minutes": round(d.dur.sum() / 60, 1)} for g, d in ev.groupby("group")}
out["test_only_accents"] = sorted(set(ev.accent) - set(seg[seg.split == "validation"].accent))

Path(__file__).with_name("calib_checks.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
