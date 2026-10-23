"""D5: the Common Voice 17.0 English replication set (test + dev, single accent label), from the CC0 mirror.

  cv.py build   data/cv_raw/{test,dev}.tsv + en_{test,dev}_0.tar -> data/manifest/cv_segments.csv,
                data/audio/cv.npy + cv_index.csv, results/tables/cv_manifest_counts.json

Tar members are read in memory (never extracted to disk). Accent labels are split on commas outside parentheses;
labels with at least 30 single-label clips are named groups, other single-label clips are "other".
"""
import hashlib
import io
import json
import re
import sys
import tarfile
from pathlib import Path

import numpy as np
import pandas as pd
import soundfile as sf
import torch
import torchaudio.functional as AF

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "cv_raw"
MIN_CLIPS = 30


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def build():
    d = pd.concat([pd.read_csv(RAW / f"{s}.tsv", sep="\t", quoting=3, dtype=str, keep_default_na=False).assign(cv_split=s)
                   for s in ("test", "dev")], ignore_index=True)
    parts = d.accents.str.strip().map(lambda s: [p.strip() for p in re.split(r",(?![^()]*\))", s) if p.strip()])
    d = d[parts.map(len) == 1].copy()
    d["accent"] = parts[d.index].map(lambda p: p[0])
    vc = d.accent.value_counts()
    named = set(vc[vc >= MIN_CLIPS].index)
    d["group"] = d.accent.where(d.accent.isin(named), "other")
    want = {(s, p) for s, p in zip(d.cv_split, d.path)}
    chunks, idx, dur, off = [], {}, {}, 0
    for s in ("test", "dev"):
        with tarfile.open(RAW / f"en_{s}_0.tar") as tf:
            for mem in tf:
                name = Path(mem.name).name
                if not mem.isfile() or (s, name) not in want:
                    continue
                x, sr = sf.read(io.BytesIO(tf.extractfile(mem).read()), dtype="float32", always_2d=True)
                x = torch.from_numpy(x.mean(axis=1))
                if sr != 16000:
                    x = AF.resample(x, sr, 16000)
                y = (x.clamp(-1, 1) * 32767).round().to(torch.int16).numpy()
                chunks.append(y)
                idx[(s, name)] = (off, len(y))
                dur[(s, name)] = len(y) / 16000
                off += len(y)
    d = d[[(s, p) in idx for s, p in zip(d.cv_split, d.path)]].reset_index(drop=True)
    d["row"] = np.arange(len(d))
    np.save(RUN / "data" / "audio" / "cv.npy", np.concatenate(chunks))
    pd.DataFrame([("cv", r, *idx[(s, p)]) for r, s, p in zip(d.row, d.cv_split, d.path)],
                 columns=["shard", "row", "offset", "n"]).to_csv(RUN / "data" / "audio" / "cv_index.csv", index=False)
    man = pd.DataFrame({"speaker": d.client_id.str[:16], "text": d.sentence, "accent": d.accent, "raw_accent": d.accents,
                        "gender": d.gender, "l1": "", "split": "cv", "cv_split": d.cv_split,
                        "dur": [round(dur[(s, p)], 3) for s, p in zip(d.cv_split, d.path)], "sr": 16000,
                        "shard": "cv", "row": d.row, "group": d.group})
    man.to_csv(RUN / "data" / "manifest" / "cv_segments.csv", index=False)
    g = man.groupby("group").agg(clips=("row", "size"), speakers=("speaker", "nunique"), hours=("dur", lambda x: round(x.sum() / 3600, 3)))
    out = {"source": "huggingface.co/datasets/fsicoli/common_voice_17_0 (CC0 mirror of Common Voice 17.0)",
           "sha256": {f: sha(RAW / f) for f in ("test.tsv", "dev.tsv", "en_test_0.tar", "en_dev_0.tar")},
           "clips": int(len(man)), "speakers": int(man.speaker.nunique()), "max_dur_s": float(man.dur.max()),
           "groups": g.to_dict(orient="index")}
    (RUN / "results" / "tables" / "cv_manifest_counts.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "sha256"}, indent=1))


if __name__ == "__main__":
    {"build": build}[sys.argv[1]]()
