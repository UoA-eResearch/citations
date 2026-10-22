"""Segment manifest, accent groups and calibration windows (plan sections 2-3).

  manifest.py build          evaluation manifest (test), group floors, US-only and balanced calibration windows
  manifest.py worst MODEL    worst-weighted calibration windows from MODEL's FP16 validation WER (after FP16 decoding)

Inputs: data/manifest/edacc_all_segments.csv (shard, row, speaker, accent, text, dur, split), built from the parquet
shards by reading only metadata and audio durations.
"""
import json
import random
import sys
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
MAN = RUN / "data" / "manifest"
TAB = RUN / "results" / "tables"
N_WIN, MIN_WIN, MAX_WIN = 48, 20.0, 30.0
TARGET, TOL = 48 * 25.0, 0.05
SEEDS = (0, 1, 2)
US = "Mainstream US English"


def segments():
    d = pd.read_csv(MAN / "edacc_all_segments.csv", keep_default_na=False)
    return d[d.text != "IGNORE_TIME_SEGMENT_IN_SCORING"].reset_index(drop=True)


def windows(d):
    """Pack consecutive segments (<= 30 s each) of one speaker, in corpus order, into 20-30 s windows."""
    out = []
    for spk, g in d[(d.split == "validation") & (d.dur <= MAX_WIN) & (d.dur >= 0.5)].groupby("speaker", sort=True):
        cur, tot = [], 0.0
        for r in g.sort_values(["shard", "row"]).itertuples():
            if tot + r.dur > MAX_WIN:
                if tot >= MIN_WIN:
                    out.append({"speaker": spk, "accent": r.accent, "segs": cur, "dur": round(tot, 3)})
                cur, tot = [], 0.0
            cur.append([r.shard, int(r.row)]); tot += r.dur
        if tot >= MIN_WIN:
            out.append({"speaker": spk, "accent": g.accent.iloc[0], "segs": cur, "dur": round(tot, 3)})
    return out


def draw(pool_by_group, alloc, seed):
    """Sample alloc[g] windows from each group; redraw (seed stream) until total speech is TARGET +/- 5%."""
    rng = random.Random(seed)
    for _ in range(10_000):
        pick = []
        for g, k in sorted(alloc.items()):
            if k:
                pick += rng.sample(pool_by_group[g], k)
        tot = sum(w["dur"] for w in pick)
        if abs(tot - TARGET) <= TOL * TARGET:
            return pick
    raise RuntimeError("no draw within tolerance")


def build():
    d = segments()
    test = d[d.split == "test"]
    g = test.groupby("accent").agg(speakers=("speaker", "nunique"), minutes=("dur", lambda x: x.sum() / 60))
    named = sorted(a for a, r in g.iterrows() if r.speakers >= 2 and r.minutes >= 10 and a != "Don't know")
    test = test.assign(group=test.accent.where(test.accent.isin(named), "other"))
    test.to_csv(MAN / "eval_segments.csv", index=False)
    W = windows(d)
    by = {}
    for w in W:
        by.setdefault(w["accent"], []).append(w)
    cal_groups = sorted(a for a in by if a != "Don't know")
    counts = {"test_segments": len(test), "test_hours": round(test.dur.sum() / 3600, 2),
              "named_groups": {a: {"speakers": int(g.at[a, "speakers"]), "minutes": round(float(g.at[a, "minutes"]), 1)}
                               for a in named},
              "other_stratum": {"speakers": int(test[test.group == "other"].speaker.nunique()),
                                "minutes": round(test[test.group == "other"].dur.sum() / 60, 1)},
              "long_segments_over_30s": int((test.dur > 30).sum()),
              "calibration_windows_available": {a: len(by[a]) for a in sorted(by)},
              "calibration_groups_balanced": cal_groups}
    assert len(cal_groups) * 2 == N_WIN, cal_groups
    sets = {}
    for s in SEEDS:
        sets[f"us_s{s}"] = draw(by, {US: N_WIN}, 1000 + s)
        sets[f"balanced_s{s}"] = draw(by, {a: 2 for a in cal_groups}, 2000 + s)
    for k, v in sets.items():
        json.dump(v, open(MAN / f"calib_{k}.json", "w"))
        counts.setdefault("calibration_sets", {})[k] = {"windows": len(v), "speech_s": round(sum(w["dur"] for w in v), 1),
                                                       "speakers": len({w["speaker"] for w in v})}
    assert not ({w["speaker"] for v in sets.values() for w in v} & set(test.speaker)), "calibration/test overlap"
    json.dump(counts, open(TAB / "manifest_counts.json", "w"), indent=1)
    print(json.dumps(counts, indent=1))


def worst(model):
    """Allocate 48 windows over the 24 calibration accents in proportion to FP16 validation WER (largest remainder)."""
    d = segments()
    W = windows(d)
    by = {}
    for w in W:
        by.setdefault(w["accent"], []).append(w)
    wer = json.load(open(TAB / f"fp16_validation_group_wer_{model}.json"))
    groups = sorted(a for a in by if a != "Don't know")
    tot = sum(wer[a] for a in groups)
    raw = {a: N_WIN * wer[a] / tot for a in groups}
    alloc = {a: min(int(raw[a]), len(by[a])) for a in groups}
    for a in sorted(groups, key=lambda a: raw[a] - int(raw[a]), reverse=True):
        if sum(alloc.values()) >= N_WIN:
            break
        if alloc[a] < len(by[a]):
            alloc[a] += 1
    assert sum(alloc.values()) == N_WIN, alloc
    out = {"allocation": alloc}
    for s in SEEDS:
        v = draw(by, alloc, 3000 + s)
        json.dump(v, open(MAN / f"calib_worst_{model}_s{s}.json", "w"))
        out[f"worst_{model}_s{s}"] = {"windows": len(v), "speech_s": round(sum(w["dur"] for w in v), 1)}
    json.dump(out, open(TAB / f"manifest_worst_{model}.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    build() if sys.argv[1] == "build" else worst(sys.argv[2])
