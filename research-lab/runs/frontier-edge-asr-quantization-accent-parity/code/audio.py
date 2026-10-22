"""Decode EdAcc audio once to 16 kHz int16 and cache it per split (data/audio/<split>.npy + index CSV)."""
import glob
import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import soundfile as sf
import torch
import torchaudio.functional as AF

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw" / "edacc" / "data"
OUT = RUN / "data" / "audio"


def build(split):
    OUT.mkdir(parents=True, exist_ok=True)
    chunks, idx, off = [], [], 0
    for f in sorted(glob.glob(str(RAW / f"{split}-*.parquet"))):
        t = pq.read_table(f, columns=["text", "audio"]).to_pandas()
        for row, (txt, a) in enumerate(zip(t.text, t.audio)):
            if txt == "IGNORE_TIME_SEGMENT_IN_SCORING":
                continue
            x, sr = sf.read(io.BytesIO(a["bytes"]), dtype="float32", always_2d=True)
            x = torch.from_numpy(x.mean(axis=1))
            if sr != 16000:
                x = AF.resample(x, sr, 16000)
            y = (x.clamp(-1, 1) * 32767).round().to(torch.int16).numpy()
            chunks.append(y); idx.append((Path(f).name, row, off, len(y))); off += len(y)
    np.save(OUT / f"{split}.npy", np.concatenate(chunks))
    pd.DataFrame(idx, columns=["shard", "row", "offset", "n"]).to_csv(OUT / f"{split}_index.csv", index=False)
    print(split, len(idx), "segments", round(off / 16000 / 3600, 2), "h")


class Audio:
    def __init__(self, split):
        self.a = np.load(OUT / f"{split}.npy", mmap_mode="r")
        ix = pd.read_csv(OUT / f"{split}_index.csv")
        self.ix = {(s, int(r)): (int(o), int(n)) for s, r, o, n in ix.itertuples(index=False)}

    def get(self, shard, row):
        o, n = self.ix[(shard, int(row))]
        return np.asarray(self.a[o:o + n], dtype=np.float32) / 32767.0


if __name__ == "__main__":
    for s in sys.argv[1:]:
        build(s)
