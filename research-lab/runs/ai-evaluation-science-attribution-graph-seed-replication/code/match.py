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

D4 (after the independent review) writes data/match_d4/ (the first run's rows stay in data/match/):
  - prompts are addressed by their stable index "i" (the rebuilt arithmetic prompts are new indices);
  - every candidate with decoder cosine >= 0.5 is ablated and stored as [idx, cosine, effect], so the full rule can be
    re-read at other cosine and magnitude thresholds (the counterpart flag is unchanged: any candidate at >= 0.7 that
    passes the magnitude condition);
  - duplicate indices in Y's top-30 are removed before the QR (the same feature at another position added spurious
    directions), and the first run's value with duplicates is kept as subspace_norm_dup;
  - two nulls for subspace replication: f projected onto Y's same-layer top-30 for a different prompt of a different
    family, and for a different prompt of the same family (seeded choice per prompt).
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
COS_STORE = 0.5
OUT = D / "match_d4"


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
        self.m, self.p, self.cache, self.base, self.tok = model, {p["i"]: p for p in prompts}, {}, {}, {}

    def __call__(self, i, l, t, idx):
        key = (i, l, t, idx)
        if key in self.cache:
            return self.cache[key]
        p = self.p[i]
        tid = p["target_id"]
        if i not in self.base:
            self.tok[i] = self.m.ensure_tokenized(p["prompt"])          # the same BOS-prefixed tokens attribute() uses
            lg, _ = self.m.feature_intervention(self.tok[i], [], freeze_attention=False, return_activations=False)
            self.base[i] = float(lg[0, -1, tid] if lg.dim() == 3 else lg[-1, tid])
        lg, _ = self.m.feature_intervention(self.tok[i], [(l, t, idx, 0.0)], freeze_attention=False, return_activations=False)
        v = float(lg[0, -1, tid] if lg.dim() == 3 else lg[-1, tid]) - self.base[i]
        self.cache[key] = v
        return v


def span_norm(dec_l, idxs, dx):
    if not idxs:
        return 0.0
    Q, _ = torch.linalg.qr(dec_l[torch.tensor(idxs, device="cuda")].float().T)
    return float(torch.linalg.norm(Q.T @ dx))


def null_prompts(prompts, valid):
    """For each prompt i: a different-family and a same-family prompt (seeded per i), among prompts with graphs."""
    import random
    fam = {p["i"]: p["family"] for p in prompts}
    out = {}
    for i in valid:
        rng = random.Random(20261110 + i)
        other = [j for j in valid if fam[j] != fam[i]]
        same = [j for j in valid if fam[j] == fam[i] and j != i]
        out[i] = (rng.choice(other) if other else None, rng.choice(same) if same else None)
    return out


def main():
    """Per target set Y: load Y's replacement model in float32 (ablation effects; D2), then for each X with (X, Y) in
    PAIRS compute counterparts and subspace replication. X's own ablation effects come from a first pass per set."""
    prompts = G.prompts()
    idx_all = [p["i"] for p in prompts]
    (D / "match").mkdir(exist_ok=True)
    OUT.mkdir(exist_ok=True)
    names = ["A", "B", "C", "D", "public"]
    # pass 1: each set's own top-10 ablation effects (D4: extend the stored file with any prompt not yet in it)
    own = {}
    for S in names:
        f = D / "match" / f"effects_{S}.json"
        have = {tuple(map(int, k.split(","))): v for k, v in json.loads(f.read_text()).items()} if f.exists() else {}
        need = []
        for i in idx_all:
            s = summary(S, i)
            if s:
                need += [(i, x["layer"], x["pos"], x["idx"]) for x in s["top10"] if (i, x["layer"], x["pos"], x["idx"]) not in have]
        if need:
            m = G.load(S, dtype=torch.float32)
            e = Effects(m, prompts)
            for k in need:
                have[k] = e(*k)
            f.write_text(json.dumps({",".join(map(str, k)): v for k, v in have.items()}))
            del m, e
            torch.cuda.empty_cache()
        own[S] = have
        print("== effects", S, len(have), "new", len(need), flush=True)
    # pass 2: per target Y
    for Y in names:
        todo = [(X, Y2) for X, Y2 in PAIRS if Y2 == Y and not (OUT / f"{X}_{Y}.jsonl").exists()]
        if not todo:
            continue
        m = G.load(Y, dtype=torch.float32)
        eY = Effects(m, prompts)
        decY = decoders_from_model(m)
        SY = {i: summary(Y, i) for i in idx_all}
        for X, _ in todo:
            decX = decoders(X)
            SX = {i: summary(X, i) for i in idx_all}
            valid = [i for i in idx_all if SX[i] is not None and SY[i] is not None]
            nulls = null_prompts(prompts, valid)
            lines = []
            for i in valid:
                sx, sy = SX[i], SY[i]
                act_y = sy["active"]
                for rank, f in enumerate(sx["top10"]):
                    l, t, idx = f["layer"], f["pos"], f["idx"]
                    ef = own[X][(i, l, t, idx)]
                    dx = decX[l][idx].float()
                    cand = act_y[(act_y[:, 0] == l) & (act_y[:, 1] == t)][:, 2].long().to("cuda")
                    cos = (decY[l][cand].float() @ dx) if len(cand) else torch.zeros(0, device="cuda")
                    keep = cos >= COS_STORE
                    cands = [[int(g), round(float(c), 5), eY(i, l, t, int(g))] for g, c in zip(cand[keep].tolist(), cos[keep].tolist())]
                    ok = [c for c in cands if c[1] >= COS]
                    matched = any(ef != 0 and c[2] * ef > 0 and abs(c[2]) >= FRAC * abs(ef) for c in ok)
                    top30 = sy["top30_by_layer"].get(str(l), [])
                    proj = span_norm(decY[l], list(dict.fromkeys(top30)), dx)
                    proj_dup = span_norm(decY[l], top30, dx)
                    jo, js = nulls[i]
                    null_o = span_norm(decY[l], list(dict.fromkeys(SY[jo]["top30_by_layer"].get(str(l), []))), dx) if jo is not None else None
                    null_s = span_norm(decY[l], list(dict.fromkeys(SY[js]["top30_by_layer"].get(str(l), []))), dx) if js is not None else None
                    lines.append({"i": i, "family": sx["family"], "rank": rank, "layer": l, "pos": t, "idx": idx, "effect_x": ef,
                                  "n_candidates_cos": len(ok), "best_cos_active": float(cos.max()) if len(cos) else None,
                                  "candidates": cands, "counterpart": matched, "subspace_norm": proj, "subspace": proj >= SUB,
                                  "subspace_norm_dup": proj_dup, "n_top30_unique": len(set(top30)), "n_top30": len(top30),
                                  "null_other_family": null_o, "null_other_family_i": jo, "null_same_family": null_s, "null_same_family_i": js,
                                  "error_share_x": sx.get("error_share"), "n_kept_x": sx.get("n_kept")})
            (OUT / f"{X}_{Y}.jsonl").write_text("\n".join(json.dumps(x) for x in lines) + "\n")
            del decX
            torch.cuda.empty_cache()
            print("== pair", X, Y, len(lines), time.strftime("%H:%M:%S"), flush=True)
        del m, eY, decY
        torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
