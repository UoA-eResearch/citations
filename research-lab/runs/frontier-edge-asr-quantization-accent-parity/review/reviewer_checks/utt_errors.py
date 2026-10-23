"""Reviewer check: per-utterance scoring of every saved Whisper-small hypothesis file, independent of code/score.py.

Writes review/reviewer_checks/utt_errors_<model>.csv with one row per (condition, utterance):
  cond, shard, row, speaker, accent, group, dur, long, nref, err, sub, del, ins, hyp_words, loop, empty_hyp
The normaliser is the same as the study's (Whisper English normaliser after removing <TAG> markup), re-implemented
here so that any difference with the study's numbers would show up when the gaps are recomputed.
"""
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
import jiwer  # noqa: E402
import pandas as pd  # noqa: E402
from transformers import WhisperTokenizer  # noqa: E402

RUN = Path(__file__).resolve().parents[2]
MAN = RUN / "data" / "manifest"
HYP = RUN / "data" / "hyps"
OUT = Path(__file__).resolve().parent
TAG = re.compile(r"<[A-Z\-_]+>")
tok = WhisperTokenizer.from_pretrained("openai/whisper-small")


def norm(t):
    return tok.normalize(TAG.sub(" ", t or "")).strip()


def looped(h, r):
    w = h.split()
    if len(w) > 2 * len(r.split()) + 10:
        return True
    grams = defaultdict(int)
    for i in range(len(w) - 2):
        grams[tuple(w[i:i + 3])] += 1
    return any(v >= 5 for v in grams.values())


def main(model):
    man = pd.read_csv(MAN / "eval_segments.csv", keep_default_na=False)
    man = man[(man.split == "test") & (man.text != "IGNORE_TIME_SEGMENT_IN_SCORING")].copy()
    man["ref_n"] = man.text.map(norm)
    n_empty_ref = int((man.ref_n.str.len() == 0).sum())
    man = man[man.ref_n.str.len() > 0].copy()
    conds = sorted(p.name[:-len("_test.jsonl")] for p in (HYP / model).glob("*_test.jsonl"))
    rows = []
    for c in conds:
        h = pd.read_json(HYP / model / f"{c}_test.jsonl", lines=True)
        d = man.merge(h, on=["shard", "row"], how="left", validate="1:1")
        assert d.hyp.notna().all(), c
        for r in d.itertuples():
            y = norm(r.hyp)
            o = jiwer.process_words(r.ref_n, y if y else "")
            rows.append((c, r.shard, r.row, r.speaker, r.accent, r.group, r.dur, r.dur > 30,
                         o.substitutions + o.deletions + o.hits, o.substitutions + o.deletions + o.insertions,
                         o.substitutions, o.deletions, o.insertions, len(y.split()), looped(y, r.ref_n), len(y) == 0))
        print(c, "done", flush=True)
    df = pd.DataFrame(rows, columns=["cond", "shard", "row", "speaker", "accent", "group", "dur", "long", "nref", "err",
                                     "sub", "del", "ins", "hyp_words", "loop", "empty_hyp"])
    df.to_csv(OUT / f"utt_errors_{model}.csv", index=False)
    meta = {"model": model, "conditions": conds, "utterances_scored": int(len(man)), "empty_refs_dropped": n_empty_ref,
            "long_utterances": int((man.dur > 30).sum()), "long_share_of_audio": float(man.dur[man.dur > 30].sum() / man.dur.sum())}
    (OUT / f"utt_errors_{model}_meta.json").write_text(json.dumps(meta, indent=1))
    print(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "small")
