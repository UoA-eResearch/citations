"""Fidelity per set (plan section 0; reported, not a gate). Runs on the guest A100. -> results/tables/fidelity.json

On the held-out FineWeb-Edu sequences (data/heldout_tokens.u32, 976 x 1,024; position 0 excluded):
  FVU per layer (MLP output vs the transcoder's reconstruction from the MLP input), dead-feature fraction (never active),
  and the replacement model (every MLP output replaced by its transcoder's reconstruction) against the true model:
  mean KL(true || replacement) per token and top-1 agreement. Sets A-D and the public lowl0 set.
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

BATCH = 4


def recon(tc, x):
    if hasattr(tc, "encode") and hasattr(tc, "decode"):
        a = tc.encode(x)
        return tc.decode(a), a
    return tc(x), None


def one_set(name, toks):
    m = G.load(name)
    L = m.cfg.n_layers
    num = torch.zeros(L, dtype=torch.float64)
    den = torch.zeros(L, dtype=torch.float64)
    ever = [None] * L
    kl_sum, top1, n_tok = 0.0, 0, 0
    for b in range(0, len(toks), BATCH):
        x = torch.tensor(toks[b:b + BATCH].astype(np.int64), device="cuda")
        cache = {}

        def save_in(t, hook):
            cache[hook.name] = t
            return t
        names = [f"blocks.{l}.mlp.hook_in" for l in range(L)] + [f"blocks.{l}.mlp.hook_out" for l in range(L)]
        with torch.no_grad():
            true_logits = m.run_with_hooks(x, fwd_hooks=[(n, save_in) for n in names])
            for l in range(L):
                xi = cache[f"blocks.{l}.mlp.hook_in"][:, 1:]
                yo = cache[f"blocks.{l}.mlp.hook_out"][:, 1:].float()
                r, a = recon(m.transcoders[l], xi)
                num[l] += ((yo - r.float()) ** 2).sum().double().cpu()
                den[l] += ((yo - yo.mean(dim=(0, 1), keepdim=True)) ** 2).sum().double().cpu()
                if a is not None:
                    act = (a > 0).flatten(0, -2).any(0)
                    ever[l] = act if ever[l] is None else (ever[l] | act)
            ins = {}

            def grab(t, hook):
                ins[hook.name.replace("hook_in", "")] = t
                return t

            def replace(t, hook):
                r, _ = recon(m.transcoders[int(hook.name.split(".")[1])], ins[hook.name.replace("hook_out", "")])
                return r.to(t.dtype)
            hooks = [(f"blocks.{l}.mlp.hook_in", grab) for l in range(L)] + [(f"blocks.{l}.mlp.hook_out", replace) for l in range(L)]
            rep_logits = m.run_with_hooks(x, fwd_hooks=hooks)
        p = torch.log_softmax(true_logits[:, 1:].float(), -1)
        q = torch.log_softmax(rep_logits[:, 1:].float(), -1)
        kl_sum += float((p.exp() * (p - q)).sum(-1).sum())
        top1 += int((p.argmax(-1) == q.argmax(-1)).sum())
        n_tok += p.shape[0] * p.shape[1]
    fvu = (num / den).tolist()
    dead = [float(1 - e.float().mean()) if e is not None else None for e in ever]
    del m
    torch.cuda.empty_cache()
    return {"fvu_by_layer": [round(v, 4) for v in fvu], "fvu_mean": round(float(np.mean(fvu)), 4),
            "dead_by_layer": [round(v, 5) if v is not None else None for v in dead],
            "dead_mean": round(float(np.mean([v for v in dead if v is not None])), 5) if any(v is not None for v in dead) else None,
            "kl_per_token": round(kl_sum / n_tok, 4), "top1_agreement": round(top1 / n_tok, 4), "tokens": n_tok}


def main():
    toks = np.fromfile(D / "heldout_tokens.u32", dtype=np.uint32).reshape(-1, 1024)
    out_f = RUN / "results" / "tables" / "fidelity.json"
    out = json.loads(out_f.read_text()) if out_f.exists() else {}
    for name in sys.argv[1:] or ["A", "B", "C", "D", "public"]:
        if name in out:
            continue
        out[name] = one_set(name, toks)
        out_f.write_text(json.dumps(out, indent=1) + "\n")
        print(name, {k: v for k, v in out[name].items() if not k.endswith("by_layer")}, flush=True)


if __name__ == "__main__":
    main()
