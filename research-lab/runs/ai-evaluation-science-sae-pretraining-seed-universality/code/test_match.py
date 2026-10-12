"""Plan section 9.2: tests of match.py on the pilot SAEs (original model, layer 4), before any full-budget SAE exists.

  1. an SAE against itself                         -> f = 1
  2. an SAE against itself with latents permuted   -> f = 1
  3. an SAE against a randomly initialised SAE     -> f near 0
  4. a pilot SAE against EleutherAI's reference SAE (context only)
  5. decoder cosine: 1 for self and the permuted copy; the Procrustes rotation of a model onto itself is the identity
Uses the first 128 sequences of H. Usage: test_match.py <pilot_save_dir>"""
import copy
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import match as M  # noqa: E402

RUN = Path(__file__).resolve().parents[1]


def main(pilot):
    tokens = np.fromfile(RUN / "data" / "heldout_tokens.bin", dtype=np.uint16).reshape(-1, M.CTX)[:128]
    a = M.SAE(Path(pilot) / "p160m" / "layers.4" / "seed0")
    perm = torch.randperm(M.NLAT, generator=torch.Generator().manual_seed(1)).to(M.DEV)
    p = copy.copy(a)
    p.W_enc, p.b_enc, p.W_dec = a.W_enc[perm], a.b_enc[perm], a.W_dec[perm]
    r = copy.copy(a)
    g = torch.Generator(device=M.DEV).manual_seed(2)
    r.W_enc = torch.randn(a.W_enc.shape, generator=g, device=M.DEV) / a.W_enc.shape[1] ** 0.5
    r.b_enc = torch.zeros_like(a.b_enc)
    r.W_dec = r.W_enc / r.W_enc.norm(dim=1, keepdim=True)
    ref = M.SAE(RUN / "data" / "raw" / "eai_sae_ref" / "layers.4")
    res, keep, n = M.encode_model("p160m", 4, tokens, dict(a=a, p=p, r=r, ref=ref))
    print("tokens", n, "FVU", {k: round(v["fvu"], 4) for k, v in res.items()},
          "assessable", {k: int((v["fired"] >= M.MIN_FIRE).sum()) for k, v in res.items()}, flush=True)
    out = {}
    for name, (x, y) in dict(self=("a", "a"), permuted=("a", "p"), random=("a", "r"), reference=("a", "ref")).items():
        ba, bb = M.corr_best(res[x], res[y], n)
        out[name] = (M.frac(ba, 0.7), M.frac(bb, 0.7))
        print(name, "f(A->B), f(B->A) at r>=0.7:", [round(v, 4) for v in out[name]], flush=True)
    ca, _ = M.dec_cos_best(res["a"]["W_dec"], res["p"]["W_dec"])
    R = M.procrustes(keep, keep)
    print("decoder cosine self/permuted min:", float(ca.min()), "| Procrustes(self) - I max:",
          float((R - torch.eye(R.shape[0])).abs().max()), flush=True)
    assert out["self"] == (1.0, 1.0) and out["permuted"] == (1.0, 1.0), out
    assert max(out["random"]) < 0.05, out["random"]
    assert ca.min() > 0.999
    print("TEST MATCH PASSED", flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
