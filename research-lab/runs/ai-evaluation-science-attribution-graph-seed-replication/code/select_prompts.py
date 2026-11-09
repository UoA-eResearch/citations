"""Prompt selection (plan section 0): keep a candidate if Qwen3-0.6B's top-1 next token is the target's first token
and its logit exceeds the runner-up's by at least 2. Uses only the model, never a transcoder (G1).

  select_prompts.py -> data/prompts.jsonl, results/tables/prompts.jsonl, results/tables/prompt_selection.json

D4 (after the independent review):
  - the arithmetic candidates were rebuilt (prompts.py) so the target is the answer digit, not the space before it;
  - every kept prompt carries a stable index "i". Prompts kept in the first selection (results/tables/prompts_v1.jsonl)
    keep their old index, so their graphs and match rows are reused unchanged; new prompts are numbered from 212;
  - invariant (G3): no target token is whitespace or punctuation, and its stripped text equals the intended answer or
    is a prefix of it (antonym targets after an opening quote are first-token prefixes such as "f" for "froid"; they
    are listed, and the family is kept out of family-level statements);
  - the margin is also computed on the BOS-prefixed tokens the graphs use (circuit-tracer ensure_tokenized), and
    reported; selection itself keeps the frozen rule (no prefix), so non-arithmetic selections cannot change.
"""
import json
import unicodedata
from collections import Counter
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
tok = AutoTokenizer.from_pretrained("Qwen/Qwen3-0.6B")
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen3-0.6B", torch_dtype=torch.bfloat16).cuda().eval()
BOS = next(filter(None, [tok.bos_token_id, tok.pad_token_id, tok.eos_token_id] + tok.all_special_ids))   # as circuit-tracer


def margin_of(ids, tid):
    logits = model(ids).logits[0, -1].float()
    top2 = torch.topk(logits, 2)
    return int(top2.indices[0]), float(top2.values[0] - top2.values[1])


def invariant(target, ttok):
    s = ttok.strip()
    if not s or all(unicodedata.category(c)[0] in "PZ" for c in s):
        return "whitespace or punctuation"
    if s == target.strip():
        return "whole answer"
    if target.strip().startswith(s):
        return "prefix of the answer"
    return "not the answer"


rows = [json.loads(l) for l in open(D / "prompt_candidates.jsonl")]
v1_path = T / "prompts_v1.jsonl"
v1 = [json.loads(l) for l in open(v1_path)] if v1_path.exists() else []
v1_index = {(r["family"], r["prompt"], r["target_token"]): r.get("i", n) for n, r in enumerate(v1)}
kept, drops = [], Counter()
with torch.no_grad():
    for r in rows:
        ids = tok(r["prompt"], return_tensors="pt").input_ids.cuda()
        tid = tok(r["target"], add_special_tokens=False).input_ids[0]
        top1, margin = margin_of(ids, tid)
        if top1 != tid:
            drops["top-1 is not the target"] += 1; continue
        if margin < 2:
            drops["margin below 2"] += 1; continue
        ids_bos = torch.cat([torch.tensor([[BOS]], device="cuda"), tok(r["prompt"], return_tensors="pt", add_special_tokens=False).input_ids.cuda()], 1)
        top1_b, margin_b = margin_of(ids_bos, tid)
        ttok = tok.decode([tid])
        kept.append({**r, "target_id": tid, "target_token": ttok, "margin": round(margin, 3),
                     "bos_top1_is_target": top1_b == tid, "bos_margin": round(margin_b, 3) if top1_b == tid else None,
                     "target_check": invariant(r["target"], ttok)})
nxt = max(v1_index.values(), default=-1) + 1
new = []
for r in kept:
    k = (r["family"], r["prompt"], r["target_token"])
    if k in v1_index:
        r["i"] = v1_index[k]
    else:
        r["i"] = nxt; nxt += 1; new.append(r["i"])
kept.sort(key=lambda r: r["i"])
for path in (D / "prompts.jsonl", T / "prompts.jsonl"):
    with open(path, "w") as f:
        for r in kept:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
v1_non_arith = {k for k in v1_index if k[0] != "arithmetic"}
now_non_arith = {(r["family"], r["prompt"], r["target_token"]) for r in kept if r["family"] != "arithmetic"}
out = {"candidates": len(rows), "kept": len(kept), "drops": dict(drops),
       "kept_by_family": dict(Counter(r["family"] for r in kept)), "candidates_by_family": dict(Counter(r["family"] for r in rows)),
       "D4": {"new_prompt_indices": new, "v1_prompts": len(v1), "v1_arithmetic_dropped": sum(k[0] == "arithmetic" for k in v1_index),
              "non_arithmetic_selection_unchanged": v1_non_arith == now_non_arith,
              "target_check": dict(Counter(r["target_check"] for r in kept)),
              "target_check_by_family": {f: dict(Counter(r["target_check"] for r in kept if r["family"] == f)) for f in sorted({r["family"] for r in kept})},
              "bos_prefixed": {"top1_is_target": sum(r["bos_top1_is_target"] for r in kept),
                               "margin_ge_2": sum((r["bos_margin"] or 0) >= 2 for r in kept),
                               "by_family_margin_ge_2": {f: f"{sum((r['bos_margin'] or 0) >= 2 for r in kept if r['family'] == f)}/{sum(r['family'] == f for r in kept)}"
                                                         for f in sorted({r["family"] for r in kept})}},
              "bos_token_id": BOS}}
assert all(r["target_check"] != "whitespace or punctuation" for r in kept), "a target is whitespace or punctuation"
T.mkdir(parents=True, exist_ok=True); (T / "prompt_selection.json").write_text(json.dumps(out, indent=1) + "\n"); print(json.dumps(out, indent=1))
