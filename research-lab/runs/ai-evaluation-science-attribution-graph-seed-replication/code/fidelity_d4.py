"""Fidelity diagnostics after the independent review (D4, finding 6 and the position-1 question of finding 2).
Runs on the guest A100. -> results/tables/fidelity_d4.json

Per set (A-D, public), on the first 244 held-out sequences (250k tokens; position 0 excluded as before):
  - skip term: does the transcoder carry W_skip, and does encode/decode equal its full forward (tc(x))?
  - dead fraction counted two ways: never in the top-k (a != 0; how training counted it) and never positive (a > 0;
    how fidelity.py counted it); and the share of top-k values that are negative (TopK keeps them: neither the trainer
    nor circuit-tracer applies a ReLU);
  - the replacement model (every MLP output replaced) with position 0 replaced, as fidelity.py did, and with position 0
    keeping the true MLP output, as circuit-tracer does (it zeroes features at position 0 and keeps error nodes);
On the prompt battery, with the BOS-prefixed tokens the graphs use:
  - normalised reconstruction error per layer at position 1 (the first token after BOS) and at positions >= 2,
    sum ||y - r||^2 / sum ||y - mean||^2, with the per-layer mean of y taken over the held-out tokens.
"""
import json
import sys
from pathlib import Path

import numpy as np
import torch

RUN = Path(__file__).resolve().parents[1]
D = RUN / "data"
sys.path.insert(0, str(RUN / "code"))
import graphs as G  # noqa: E402

BATCH, NSEQ = 4, 244


def one_set(name, toks, prompts):
    m = G.load(name)
    L = m.cfg.n_layers
    tcs = [m.transcoders[l] for l in range(L)]
    has_skip = [getattr(tc, "W_skip", None) is not None for tc in tcs]
    num, den = torch.zeros(L, dtype=torch.float64), torch.zeros(L, dtype=torch.float64)
    ysum, ycnt = torch.zeros(L, m.cfg.d_model, dtype=torch.float64), 0
    ever_topk, ever_pos = [None] * L, [None] * L
    neg, tot = torch.zeros(L, dtype=torch.float64), torch.zeros(L, dtype=torch.float64)
    fwd_diff = 0.0
    kl = {"pos0_replaced": 0.0, "pos0_true": 0.0}
    top1 = {"pos0_replaced": 0, "pos0_true": 0}
    n_tok = 0
    names = [f"blocks.{l}.mlp.hook_in" for l in range(L)] + [f"blocks.{l}.mlp.hook_out" for l in range(L)]
    for b in range(0, NSEQ, BATCH):
        x = torch.tensor(toks[b:b + BATCH].astype(np.int64), device="cuda")
        cache = {}

        def save(t, hook):
            cache[hook.name] = t
            return t
        with torch.no_grad():
            true_logits = m.run_with_hooks(x, fwd_hooks=[(n, save) for n in names])
            for l in range(L):
                xi = cache[f"blocks.{l}.mlp.hook_in"][:, 1:]
                yo = cache[f"blocks.{l}.mlp.hook_out"][:, 1:].float()
                a = tcs[l].encode(xi)
                r = tcs[l].decode(a, xi)
                if b == 0:
                    fwd_diff = max(fwd_diff, float((tcs[l](xi).float() - r.float()).abs().max()))
                num[l] += ((yo - r.float()) ** 2).sum().double().cpu()
                den[l] += ((yo - yo.mean(dim=(0, 1), keepdim=True)) ** 2).sum().double().cpu()
                ysum[l] += yo.sum(dim=(0, 1)).double().cpu()
                nz, ps = (a != 0).flatten(0, -2), (a > 0).flatten(0, -2)
                ever_topk[l] = nz.any(0) if ever_topk[l] is None else ever_topk[l] | nz.any(0)
                ever_pos[l] = ps.any(0) if ever_pos[l] is None else ever_pos[l] | ps.any(0)
                neg[l] += float((a < 0).sum())
                tot[l] += float(nz.sum())
            ycnt += yo.shape[0] * yo.shape[1]
            for mode in ("pos0_replaced", "pos0_true"):
                ins = {}

                def grab(t, hook):
                    ins[hook.name.replace("hook_in", "")] = t
                    return t

                def replace(t, hook, mode=mode):
                    l = int(hook.name.split(".")[1])
                    xin = ins[hook.name.replace("hook_out", "")]
                    r = tcs[l].decode(tcs[l].encode(xin), xin).to(t.dtype)
                    if mode == "pos0_true":
                        r[:, 0] = t[:, 0]
                    return r
                hooks = [(f"blocks.{l}.mlp.hook_in", grab) for l in range(L)] + [(f"blocks.{l}.mlp.hook_out", replace) for l in range(L)]
                rep = m.run_with_hooks(x, fwd_hooks=hooks)
                p = torch.log_softmax(true_logits[:, 1:].float(), -1)
                q = torch.log_softmax(rep[:, 1:].float(), -1)
                kl[mode] += float((p.exp() * (p - q)).sum(-1).sum())
                top1[mode] += int((p.argmax(-1) == q.argmax(-1)).sum())
        n_tok += (x.shape[1] - 1) * x.shape[0]
    ymean = (ysum / ycnt).float().cuda()
    # prompt battery, BOS-prefixed: error at position 1 vs >= 2
    pn = {k: torch.zeros(L, dtype=torch.float64) for k in ("pos1", "pos2plus")}
    pd = {k: torch.zeros(L, dtype=torch.float64) for k in ("pos1", "pos2plus")}
    with torch.no_grad():
        for pr in prompts:
            t = m.ensure_tokenized(pr["prompt"]).unsqueeze(0)
            cache = {}

            def save(tn, hook):
                cache[hook.name] = tn
                return tn
            m.run_with_hooks(t, fwd_hooks=[(n, save) for n in names])
            for l in range(L):
                xi = cache[f"blocks.{l}.mlp.hook_in"][0]
                yo = cache[f"blocks.{l}.mlp.hook_out"][0].float()
                r = tcs[l].decode(tcs[l].encode(xi), xi).float()
                e = ((yo - r) ** 2).sum(-1).double().cpu()
                v = ((yo - ymean[l]) ** 2).sum(-1).double().cpu()
                pn["pos1"][l] += e[1]; pd["pos1"][l] += v[1]
                pn["pos2plus"][l] += e[2:].sum(); pd["pos2plus"][l] += v[2:].sum()
    prompt_err = {k: [round(float(pn[k][l] / pd[k][l]), 4) for l in range(L)] for k in pn}
    dead_topk = [float(1 - e.float().mean()) for e in ever_topk]
    dead_pos = [float(1 - e.float().mean()) for e in ever_pos]
    del m
    torch.cuda.empty_cache()
    return {"has_skip_any_layer": any(has_skip), "max_abs_diff_forward_vs_encode_decode": fwd_diff,
            "heldout_tokens": n_tok, "fvu_by_layer": [round(float(num[l] / den[l]), 4) for l in range(L)],
            "fvu_mean": round(float((num / den).mean()), 4),
            "dead_never_in_topk_mean": round(float(np.mean(dead_topk)), 5), "dead_never_positive_mean": round(float(np.mean(dead_pos)), 5),
            "dead_never_in_topk_by_layer": [round(v, 5) for v in dead_topk],
            "negative_share_of_topk_values_by_layer": [round(float(neg[l] / tot[l]), 4) if tot[l] else None for l in range(L)],
            "negative_share_of_topk_values_mean": round(float((neg / tot.clamp_min(1)).mean()), 4),
            "replacement": {k: {"kl_per_token": round(kl[k] / n_tok, 4), "top1_agreement": round(top1[k] / n_tok, 4)} for k in kl},
            "prompt_error_by_layer": prompt_err,
            "prompt_error_mean": {k: round(float(np.mean(v)), 4) for k, v in prompt_err.items()},
            "prompt_error_layers_0_2": {k: round(float(np.mean(v[:3])), 4) for k, v in prompt_err.items()}}


def main():
    toks = np.fromfile(D / "heldout_tokens.u32", dtype=np.uint32).reshape(-1, 1024)
    prompts = G.prompts()
    out_f = RUN / "results" / "tables" / "fidelity_d4.json"
    out = json.loads(out_f.read_text()) if out_f.exists() else {}
    for name in sys.argv[1:] or ["A", "B", "C", "D", "public"]:
        if name in out:
            continue
        out[name] = one_set(name, toks, prompts)
        out_f.write_text(json.dumps(out, indent=1) + "\n")
        print(name, {k: v for k, v in out[name].items() if "by_layer" not in k}, flush=True)


if __name__ == "__main__":
    main()
