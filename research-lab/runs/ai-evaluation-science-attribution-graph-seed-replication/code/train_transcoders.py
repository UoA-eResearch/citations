"""Train one TopK per-layer transcoder set for all 28 MLPs of Qwen3-0.6B (plan section 0).

Inputs are each MLP's input as HF hooks capture it (after post_attention_layernorm); targets are the MLP's output
(act_check.py: this matches circuit-tracer's mlp.hook_in/hook_out). Position 0 of every sequence is skipped, as
circuit-tracer zeroes it. Recipe: width 32,768, TopK k = 64, unit-norm decoder rows, encoder initialised to the
decoder, b_dec initialised to the first batch's mean output, aux-k dead-feature loss (k_aux 512, coefficient 1/32,
dead = no firing in the last 10M tokens), Adam lr 2e-4 with 1% linear warm-up and cosine decay to 10%, batches of 4
sequences of 1,024 tokens, 300M tokens. All 28 layers train from the same forward pass.

  train_transcoders.py NAME INIT_SEED ORDER_SEED [MAX_STEPS] -> data/sets/NAME/layer_{l}.safetensors, config.yaml, train_log.json
"""
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import torch
from safetensors.torch import save_file
from transformers import AutoModelForCausalLM

RUN = Path(__file__).resolve().parents[1]
D = RUN / "data"
D_TC, K, K_AUX, AUX_COEF, LR, SEQ, BS = 32768, 64, 512, 1 / 32, 2e-4, 1024, 4
DEAD_TOKENS = 10_000_000


def main(name, init_seed, order_seed, max_steps=None):
    init_seed, order_seed = int(init_seed), int(order_seed)
    out = D / "sets" / name; out.mkdir(parents=True, exist_ok=True)
    tokens = np.memmap(D / "train_tokens.u32", dtype=np.uint32, mode="r").reshape(-1, SEQ)
    order = np.random.default_rng(order_seed).permutation(len(tokens))
    steps = len(tokens) // BS if max_steps is None else int(max_steps)
    model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen3-0.6B", dtype=torch.bfloat16).cuda().eval()
    layers = model.model.layers; NL, DM = len(layers), model.config.hidden_size
    cap = {}
    for l, layer in enumerate(layers):
        layer.mlp.register_forward_hook(lambda m, i, o, l=l: cap.__setitem__(l, (i[0].detach(), o.detach())))
    g = torch.Generator(device="cuda").manual_seed(init_seed)
    W_dec = [torch.randn(D_TC, DM, device="cuda", generator=g) for _ in range(NL)]
    W_dec = [torch.nn.Parameter(w / w.norm(dim=1, keepdim=True)) for w in W_dec]
    W_enc = [torch.nn.Parameter(w.detach().clone()) for w in W_dec]
    b_enc = [torch.nn.Parameter(torch.zeros(D_TC, device="cuda")) for _ in range(NL)]
    b_dec = [torch.nn.Parameter(torch.zeros(DM, device="cuda")) for _ in range(NL)]
    opt = torch.optim.Adam(W_enc + W_dec + b_enc + b_dec, lr=LR)
    warm = max(1, steps // 100)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: (s + 1) / warm if s < warm else 0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * (s - warm) / max(1, steps - warm))))
    last_fired = [torch.zeros(D_TC, device="cuda", dtype=torch.long) for _ in range(NL)]
    tok_seen, log, t0 = 0, [], time.time()
    ema_fvu = [None] * NL
    for step in range(steps):
        ids = torch.from_numpy(tokens[np.sort(order[step * BS:(step + 1) * BS])].astype(np.int64)).cuda()
        with torch.no_grad():
            model(ids)
        n = BS * (SEQ - 1); tok_seen += n
        for l in range(NL):
            x = cap[l][0][:, 1:].reshape(-1, DM).float(); y = cap[l][1][:, 1:].reshape(-1, DM).float()
            if step == 0:
                with torch.no_grad():
                    b_dec[l].copy_(y.mean(0))
            var_y = ((y - y.mean(0)) ** 2).sum(-1).mean()
            with torch.autocast("cuda", dtype=torch.bfloat16):
                pre = x @ W_enc[l].T + b_enc[l]
            pre = pre.float()
            vals, idx = pre.topk(K, dim=-1)
            acts = torch.zeros_like(pre).scatter_(-1, idx, vals)
            with torch.autocast("cuda", dtype=torch.bfloat16):
                y_hat = acts @ W_dec[l] + b_dec[l]
            y_hat = y_hat.float()
            mse = ((y_hat - y) ** 2).sum(-1).mean() / var_y
            loss = mse
            with torch.no_grad():
                fired = torch.zeros(D_TC, device="cuda", dtype=torch.bool); fired[idx.reshape(-1)] = True
                last_fired[l][fired] = tok_seen
                dead = (tok_seen - last_fired[l]) > DEAD_TOKENS
            if dead.any() and step > 0:
                e = (y - y_hat).detach()
                pre_d = pre.masked_fill(~dead, float("-inf"))
                kd = min(K_AUX, int(dead.sum()))
                v2, i2 = pre_d.topk(kd, dim=-1)
                a2 = torch.zeros_like(pre).scatter_(-1, i2, torch.nan_to_num(v2, neginf=0.0))
                with torch.autocast("cuda", dtype=torch.bfloat16):
                    e_hat = a2 @ W_dec[l]
                loss = loss + AUX_COEF * ((e_hat.float() - e) ** 2).sum(-1).mean() / ((e - e.mean(0)) ** 2).sum(-1).mean().clamp_min(1e-8)
            loss.backward()
            f = float(mse.detach()); ema_fvu[l] = f if ema_fvu[l] is None else 0.99 * ema_fvu[l] + 0.01 * f
        opt.step(); sched.step(); opt.zero_grad(set_to_none=True)
        with torch.no_grad():
            for w in W_dec:
                w.div_(w.norm(dim=1, keepdim=True))
        if step % 500 == 0 or step == steps - 1:
            dead_frac = [float(((tok_seen - lf) > DEAD_TOKENS).float().mean()) for lf in last_fired]
            rec = {"step": step, "tokens": tok_seen, "sec": round(time.time() - t0), "fvu_mean": round(float(np.mean(ema_fvu)), 4),
                   "fvu_by_layer": [round(v, 4) for v in ema_fvu], "dead_frac_mean": round(float(np.mean(dead_frac)), 4)}
            log.append(rec); print(json.dumps({k: v for k, v in rec.items() if k != "fvu_by_layer"}), flush=True)
            (out / "train_log.json").write_text(json.dumps(log) + "\n")
        if (step + 1) % 10000 == 0 or step == steps - 1:
            for l in range(NL):
                save_file({"W_enc": W_enc[l].detach().contiguous().cpu(), "W_dec": W_dec[l].detach().contiguous().cpu(),
                           "b_enc": b_enc[l].detach().cpu(), "b_dec": b_dec[l].detach().cpu()}, str(out / f"layer_{l}.safetensors"))
            (out / "config.yaml").write_text('model_name: "Qwen/Qwen3-0.6B"\nmodel_kind: "transcoder_set"\nfeature_input_hook: "mlp.hook_in"\n'
                                             'feature_output_hook: "mlp.hook_out"\nactivation: "topk"\nk: 64\n')
            (out / "progress.json").write_text(json.dumps({"step": step + 1, "steps": steps, "init_seed": init_seed, "order_seed": order_seed}) + "\n")


if __name__ == "__main__":
    main(*sys.argv[1:])
