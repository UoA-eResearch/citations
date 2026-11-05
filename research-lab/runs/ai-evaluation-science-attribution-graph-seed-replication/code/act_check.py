"""Check that the activations the transcoders are trained on match circuit-tracer's hook points: the public
mwhanna/qwen3-0.6b-transcoders-lowl0 set (ReLU, 163,840 wide) should reconstruct the MLP output well from the MLP's (normalised) input as
captured by HF forward hooks, and badly from the pre-norm residual.

  act_check.py -> results/tables/act_check.json
"""
import glob
import json
from pathlib import Path

import torch
from circuit_tracer.transcoder.single_layer_transcoder import load_transcoder
from transformers import AutoModelForCausalLM, AutoTokenizer

RUN = Path(__file__).resolve().parents[1]
snap = glob.glob("/mnt/claude-lab/hf/hub/models--mwhanna--qwen3-0.6b-transcoders-lowl0/snapshots/*/")[0]
tok = AutoTokenizer.from_pretrained("Qwen/Qwen3-0.6B")
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen3-0.6B", torch_dtype=torch.bfloat16).cuda().eval()
text = ["The history of the Roman Empire spans many centuries, from the founding of the city to the fall of the West.",
        "Photosynthesis converts light energy into chemical energy that can later be released to fuel the organism.",
        "In mathematics, a prime number is a natural number greater than one that is not a product of two smaller numbers."]
enc = [tok(t).input_ids for t in text]; L = min(len(e) for e in enc)
ids = torch.tensor([e[:L] for e in enc]).cuda()   # equal lengths, no padding
cap = {}
def hk(l):
    def f(mod, inp, out):
        cap[l] = (inp[0].detach().float(), out.detach().float())
    return f
def hk_res(l):
    def f(mod, inp, out):
        cap[f"res{l}"] = inp[0].detach().float()
    return f
hs = []
for l, layer in enumerate(model.model.layers):
    hs.append(layer.mlp.register_forward_hook(hk(l)))
    hs.append(layer.post_attention_layernorm.register_forward_hook(hk_res(l)))
with torch.no_grad():
    model(ids)
out = {}
for l in (0, 7, 14, 21, 27):
    tc = load_transcoder(f"{snap}/layer_{l}.safetensors", l, device=torch.device("cuda"), lazy_encoder=False, lazy_decoder=False)
    x, y = cap[l]; r = cap[f"res{l}"]
    x, y, r = x[:, 1:], y[:, 1:], r[:, 1:]          # circuit-tracer zeroes position 0 (the attention sink)
    x, y, r = x.reshape(-1, x.shape[-1]), y.reshape(-1, y.shape[-1]), r.reshape(-1, r.shape[-1])
    with torch.no_grad():
        fvu = lambda yh: float(((yh - y) ** 2).sum() / ((y - y.mean(0)) ** 2).sum())
        out[l] = {"fvu_mlp_input": fvu(tc(x)), "fvu_prenorm_residual": fvu(tc(r))}
(RUN / "results" / "tables" / "act_check.json").write_text(json.dumps(out, indent=1) + "\n"); print(out)
