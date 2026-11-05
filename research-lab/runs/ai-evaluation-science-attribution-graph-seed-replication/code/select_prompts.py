"""Prompt selection (plan section 0): keep a candidate if Qwen3-0.6B's top-1 next token is the target's first token
and its logit exceeds the runner-up's by at least 2. Uses only the model, never a transcoder (G1).

  select_prompts.py -> data/prompts.jsonl, results/tables/prompt_selection.json
"""
import json
from collections import Counter
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
tok = AutoTokenizer.from_pretrained("Qwen/Qwen3-0.6B")
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen3-0.6B", torch_dtype=torch.bfloat16).cuda().eval()
rows = [json.loads(l) for l in open(D / "prompt_candidates.jsonl")]
kept, drops = [], Counter()
with torch.no_grad():
    for r in rows:
        ids = tok(r["prompt"], return_tensors="pt").input_ids.cuda()
        logits = model(ids).logits[0, -1].float()
        tid = tok(r["target"], add_special_tokens=False).input_ids[0]
        top2 = torch.topk(logits, 2)
        if int(top2.indices[0]) != tid:
            drops["top-1 is not the target"] += 1; continue
        margin = float(top2.values[0] - top2.values[1])
        if margin < 2:
            drops["margin below 2"] += 1; continue
        kept.append({**r, "target_id": tid, "target_token": tok.decode([tid]), "margin": round(margin, 3)})
with open(D / "prompts.jsonl", "w") as f:
    for r in kept:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
out = {"candidates": len(rows), "kept": len(kept), "drops": dict(drops),
       "kept_by_family": dict(Counter(r["family"] for r in kept)), "candidates_by_family": dict(Counter(r["family"] for r in rows))}
T.mkdir(parents=True, exist_ok=True); (T / "prompt_selection.json").write_text(json.dumps(out, indent=1) + "\n"); print(out)
