"""Quantize (or not) and decode one condition (plan sections 3-6).

  decode.py MODEL COND SPLIT
    MODEL  small | large-v3
    COND   fp16 | rtn_w8 | rtn_w4 | gptq_w4_<comp>_s<seed> | gptq_w3_<comp>_s<seed> | awq_w4_<comp>_s<seed>
           | mp_<comp>_s<seed> | mp3_<comp>_s<seed> (D1)        comp: us | balanced | worst
    SPLIT  test | validation | cv (D5: Common Voice replication)

Writes data/hyps/<MODEL>/<COND>_<SPLIT>.jsonl and appends the condition's packed size to results/tables/conditions.jsonl.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from transformers import WhisperForConditionalGeneration, WhisperProcessor

sys.path.insert(0, str(Path(__file__).resolve().parent))
import quant  # noqa: E402
from audio import Audio  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
MAN = RUN / "data" / "manifest"
TAB = RUN / "results" / "tables"
NAMES = {"small": "openai/whisper-small", "large-v3": "openai/whisper-large-v3"}
BS = {"small": 32, "large-v3": 4}           # D3: large-v3 at 16 ran out of GPU memory
LONG_BS = {"small": 8, "large-v3": 1}
GEN = dict(language="en", task="transcribe")
MANIFEST = {"test": "eval_segments.csv", "validation": "edacc_all_segments.csv", "cv": "cv_segments.csv"}   # cv: D5


def load(model):
    proc = WhisperProcessor.from_pretrained(NAMES[model])
    m = WhisperForConditionalGeneration.from_pretrained(NAMES[model], torch_dtype=torch.float16).cuda().eval()
    return proc, m


def wkey(w):
    return f"{w['speaker']}|{w['segs'][0][0]}|{w['segs'][0][1]}"


def window_audio(w, aud):
    return np.concatenate([aud.get(s, r) for s, r in w["segs"]])


def transcribe_short(proc, m, audios, bs):
    out = []
    for i in range(0, len(audios), bs):
        f = proc.feature_extractor(audios[i:i + bs], sampling_rate=16000, return_tensors="pt").input_features
        with torch.no_grad():
            ids = m.generate(f.cuda().half(), max_new_tokens=440, **GEN)
        out += proc.batch_decode(ids, skip_special_tokens=True)
    return [t.strip() for t in out]


def transcribe_long(proc, m, audios, bs):
    out = []
    for i in range(0, len(audios), bs):
        f = proc(audios[i:i + bs], sampling_rate=16000, return_tensors="pt", truncation=False, padding="longest",
                 return_attention_mask=True)
        with torch.no_grad():
            ids = m.generate(f.input_features.cuda().half(), attention_mask=f.attention_mask.cuda(),
                             return_timestamps=True, condition_on_prev_tokens=False, temperature=0.0,
                             compression_ratio_threshold=None, logprob_threshold=None, no_speech_threshold=None, **GEN)
        seqs = ids["sequences"] if isinstance(ids, dict) else ids
        out += proc.batch_decode(seqs, skip_special_tokens=True)
    return [t.strip() for t in out]


def calib_texts(model, proc, m, windows):
    """FP16 transcripts of calibration windows (cached; computed with the unquantized model)."""
    p = RUN / "data" / "calib_text" / f"{model}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    cache = json.loads(p.read_text()) if p.exists() else {}
    todo = [w for w in windows if wkey(w) not in cache]
    if todo:
        aud = Audio("validation")
        txt = transcribe_short(proc, m, [window_audio(w, aud) for w in todo], BS[model])
        cache.update({wkey(w): t for w, t in zip(todo, txt)})
        p.write_text(json.dumps(cache))
    return cache


def batches(model, proc, m, windows):
    texts = calib_texts(model, proc, m, windows)
    aud = Audio("validation")
    tok = proc.tokenizer
    tok.set_prefix_tokens(language="en", task="transcribe", predict_timestamps=False)
    out = []
    for w in windows:
        f = proc.feature_extractor([window_audio(w, aud)], sampling_rate=16000, return_tensors="pt").input_features
        ids = tok(texts[wkey(w)]).input_ids[:-1][:448]
        out.append((f.cuda().half(), torch.tensor([ids]).cuda()))
    return out


def calib_windows(model, comp, seed):
    f = MAN / (f"calib_worst_{model}_s{seed}.json" if comp == "worst" else f"calib_{comp}_s{seed}.json")
    return json.loads(f.read_text())


def apply(model, cond, proc, m):
    mods = quant.block_linears(m)
    if cond == "fp16":
        return {k: 16 for k in mods}, {}
    if cond.startswith("rtn_w"):
        b = int(cond[5:])
        quant.quantize_rtn(m, b)
        return {k: b for k in mods}, {}
    kind, rest = cond.split("_", 1)
    if kind in ("gptq", "awq"):
        b, comp, s = rest.split("_")
        b, seed = int(b[1:]), int(s[1:])
    else:                                   # mp_ / mp3_<comp>_s<seed>
        comp, s = rest.split("_")
        seed = int(s[1:])
    cal = batches(model, proc, m, calib_windows(model, comp, seed))
    if kind == "gptq":
        bits = {k: b for k in mods}
        quant.quantize_gptq(m, cal, bits)
        return bits, {}
    if kind == "awq":
        return {k: b for k in mods}, {"alpha": quant.quantize_awq(m, cal, b)}
    alloc = json.loads((TAB / f"{kind}_allocation_{model}.json").read_text())
    quant.quantize_gptq(m, cal, alloc["bits"])
    return alloc["bits"], {}


def main(model, cond, split):
    out = RUN / "data" / "hyps" / model / f"{cond}_{split}.jsonl"
    if out.exists():
        print("exists", out)
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    proc, m = load(model)
    bits, extra = apply(model, cond, proc, m)
    tq = time.time() - t0
    man = pd.read_csv(MAN / MANIFEST[split], keep_default_na=False)
    man = man[(man.split == split) & (man.text != "IGNORE_TIME_SEGMENT_IN_SCORING")]
    aud = Audio(split)
    man = man.sort_values("dur")
    short, long_ = man[man.dur <= 30], man[man.dur > 30]
    hyp = transcribe_short(proc, m, [aud.get(s, r) for s, r in zip(short.shard, short.row)], BS[model])
    hyp += transcribe_long(proc, m, [aud.get(s, r) for s, r in zip(long_.shard, long_.row)], LONG_BS[model])
    keys = list(zip(short.shard, short.row)) + list(zip(long_.shard, long_.row))
    tmp = out.with_suffix(".tmp")
    with open(tmp, "w") as fh:
        for (s, r), h in zip(keys, hyp):
            fh.write(json.dumps({"shard": s, "row": int(r), "hyp": h}) + "\n")
    tmp.rename(out)
    rec = {"model": model, "cond": cond, "split": split, "size_bits": quant.size_bits(m, bits),
           "size_ratio_vs_w4": quant.size_bits(m, bits) / quant.size_bits(m, {k: 4 for k in bits}),
           "quantize_s": round(tq, 1), "total_s": round(time.time() - t0, 1), **extra}
    with open(TAB / "conditions.jsonl", "a") as fh:
        fh.write(json.dumps(rec) + "\n")
    print(json.dumps({k: v for k, v in rec.items() if k != "alpha"}))


if __name__ == "__main__":
    main(*sys.argv[1:4])
