"""Counterparts, node replication and subspace replication (plan section 0, H1 and H2). Runs on the guest A100 after
graphs.py. -> data/match/<X>_<Y>.jsonl (one line per top-10 feature of X's graph for each prompt)

Counterpart of a top-10 feature f of set X (prompt p, layer l, position t) in set Y: a feature g that is active on p at
t (Y's graph active features), in layer l, with decoder cosine(f, g) >= 0.7, and whose zero-ablation changes the target
logit with the same sign as f's and by at least 50% of its magnitude. Ablation: circuit-tracer feature_intervention,
value 0 at (l, t), freeze_attention=False (effects propagate through the replacement model), the same for every set;
the effect is ablated minus baseline target logit.
Subspace replication: the norm of f's unit decoder projected onto the span of Y's 30 most influential layer-l decoders
for p is at least 0.7.
Directions: the 6 ordered pairs of A, B, C (H1, H2); A<->D (data order); public<->A.
"""
import json
import sys
import time
from pathlib import Path

import torch

RUN = Path(__file__).resolve().parents[1]
D = RUN / "data"
sys.path.insert(0, str(RUN / "code"))
import graphs as G  # noqa: E402

PAIRS = [("A", "B"), ("B", "A"), ("A", "C"), ("C", "A"), ("B", "C"), ("C", "B"), ("A", "D"), ("D", "A"), ("public", "A"), ("A", "public")]
COS, FRAC, SUB = 0.7, 0.5, 0.7


def decoders_from_model(model):
    out = []
    for l in range(28):
        W = model.transcoders[l].W_dec.detach().to("cuda", torch.float16)
        out.append(torch.nn.functional.normalize(W.float(), dim=-1).half())
    return out


def decoders(set_name):
    """Unit decoder rows per layer, fp16 on the GPU, without loading a model (local sets read the safetensors)."""
    if set_name == "public":
        m = G.load("public")
        d = decoders_from_model(m)
        del m
        torch.cuda.empty_cache()
        return d
    from safetensors.torch import load_file
    out = []
    for l in range(28):
        W = load_file(str(D / "sets" / set_name / f"layer_{l}.safetensors"))["W_dec"].to("cuda", torch.float32)
        out.append(torch.nn.functional.normalize(W, dim=-1).half())
    return out


def summary(set_name, i):
    f = D / "graphs" / set_name / f"{i:03d}.json"
    if not f.exists():
        return None
    s = json.loads(f.read_text())
    if s.get("status") != "ok":
        return None
    s["active"] = torch.load(D / "graphs" / set_name / f"{i:03d}_active.pt")["active"]
    return s


class Effects:
    def __init__(self, model, prompts):
        self.m, self.p, self.cache, self.base = model, prompts, {}, {}

    def __call__(self, i, l, t, idx):
        key = (i, l, t, idx)
        if key in self.cache:
            return self.cache[key]
        p = self.p[i]
        tid = p["target_id"]
        if i not in self.base:
            self.tok = getattr(self, "tok", {})
            self.tok[i] = self.m.ensure_tokenized(p["prompt"])          # the same BOS-prefixed tokens attribute() uses
            lg, _ = self.m.feature_intervention(self.tok[i], [], freeze_attention=False, return_activations=False)
            self.base[i] = float(lg[0, -1, tid] if lg.dim() == 3 else lg[-1, tid])
        lg, _ = self.m.feature_intervention(self.tok[i], [(l, t, idx, 0.0)], freeze_attention=False, return_activations=False)
        v = float(lg[0, -1, tid] if lg.dim() == 3 else lg[-1, tid]) - self.base[i]
        self.cache[key] = v
        return v


def main():
    """Per target set Y: load Y's replacement model in float32 (ablation effects; D2), then for each X with (X, Y) in
    PAIRS compute counterparts and subspace replication. X's own ablation effects come from a first pass per set."""
    prompts = G.prompts()
    (D / "match").mkdir(exist_ok=True)
    names = ["A", "B", "C", "D", "public"]
    # pass 1: each set's own top-10 ablation effects
    own = {}
    for S in names:
        f = D / "match" / f"effects_{S}.json"
        if f.exists():
            own[S] = {tuple(map(int, k.split(","))): v for k, v in json.loads(f.read_text()).items()}
            continue
        m = G.load(S, dtype=torch.float32)
        e = Effects(m, prompts)
        for i in range(len(prompts)):
            s = summary(S, i)
            if s:
                for x in s["top10"]:
                    e(i, x["layer"], x["pos"], x["idx"])
        own[S] = dict(e.cache)
        f.write_text(json.dumps({",".join(map(str, k)): v for k, v in e.cache.items()}))
        del m, e
        torch.cuda.empty_cache()
        print("== effects", S, len(own[S]), flush=True)
    # pass 2: per target Y
    for Y in names:
        todo = [(X, Y2) for X, Y2 in PAIRS if Y2 == Y and not (D / "match" / f"{X}_{Y}.jsonl").exists()]
        if not todo:
            continue
        m = G.load(Y, dtype=torch.float32)
        eY = Effects(m, prompts)
        decY = decoders_from_model(m)
        for X, _ in todo:
            decX = decoders(X)
            lines = []
            for i in range(len(prompts)):
                sx, sy = summary(X, i), summary(Y, i)
                if sx is None or sy is None:
                    continue
                act_y = sy["active"]
                for rank, f in enumerate(sx["top10"]):
                    l, t, idx = f["layer"], f["pos"], f["idx"]
                    ef = own[X][(i, l, t, idx)]
                    dx = decX[l][idx].float()
                    cand = act_y[(act_y[:, 0] == l) & (act_y[:, 1] == t)][:, 2].long().to("cuda")
                    cos = (decY[l][cand].float() @ dx) if len(cand) else torch.zeros(0, device="cuda")
                    ok = cand[cos >= COS].tolist()
                    matched = False
                    for g in ok:
                        eg = eY(i, l, t, g)
                        if ef != 0 and eg * ef > 0 and abs(eg) >= FRAC * abs(ef):
                            matched = True
                            break
                    top30 = sy["top30_by_layer"].get(str(l), [])
                    if top30:
                        Q, _ = torch.linalg.qr(decY[l][torch.tensor(top30, device="cuda")].float().T)
                        proj = float(torch.linalg.norm(Q.T @ dx))
                    else:
                        proj = 0.0
                    lines.append({"i": i, "family": sx["family"], "rank": rank, "layer": l, "pos": t, "idx": idx, "effect_x": ef,
                                  "n_candidates_cos": len(ok), "best_cos_active": float(cos.max()) if len(cos) else None,
                                  "counterpart": matched, "subspace_norm": proj, "subspace": proj >= SUB,
                                  "error_share_x": sx.get("error_share"), "n_kept_x": sx.get("n_kept")})
            (D / "match" / f"{X}_{Y}.jsonl").write_text("\n".join(json.dumps(x) for x in lines) + "\n")
            del decX
            torch.cuda.empty_cache()
            print("== pair", X, Y, len(lines), time.strftime("%H:%M:%S"), flush=True)
        del m, eY, decY
        torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
