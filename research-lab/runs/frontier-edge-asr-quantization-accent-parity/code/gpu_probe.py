"""Feasibility probe before preregistration: load a Whisper model on the shared GPU, decode 30 s of synthetic noise
in batches, report peak memory and throughput. No evaluation data is touched."""
import sys
import time

import numpy as np
import torch
from transformers import WhisperForConditionalGeneration, WhisperProcessor

name = sys.argv[1] if len(sys.argv) > 1 else "openai/whisper-small"
proc = WhisperProcessor.from_pretrained(name)
model = WhisperForConditionalGeneration.from_pretrained(name, torch_dtype=torch.float16).cuda().eval()
torch.cuda.reset_peak_memory_stats()
audio = [np.random.default_rng(i).normal(0, 0.01, 16000 * 30).astype(np.float32) for i in range(16)]
feats = proc(audio, sampling_rate=16000, return_tensors="pt").input_features.cuda().half()
t0 = time.time()
with torch.no_grad():
    out = model.generate(feats, max_new_tokens=64)
torch.cuda.synchronize()
print(name, "batch 16 x 30 s:", round(time.time() - t0, 2), "s; peak GPU", round(torch.cuda.max_memory_allocated() / 2**30, 2), "GiB")
