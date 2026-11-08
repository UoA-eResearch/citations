"""G4 (plan section 3). Runs on the guest A100 after match.py. -> results/tables/g4.json

For 30 random top-10 features of set A (seed 20261108, direction A -> B):
  1. activation-correlation match: Pearson correlation, over 20 held-out sequences (~20k tokens, position 0 excluded),
     between f's activation in A and every same-layer feature of B; the best match and whether it reaches 0.7;
  2. decoder-cosine match: the B feature with the highest decoder cosine to f (any, not only active ones);
  3. agreement: do the two methods pick the same B feature, and do both clear 0.7?
  4. an independent re-run of f's ablation effect in a fresh process, against the stored effects_A.json value.
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
import match as M  # noqa: E402


def layer_acts(model, toks, l):
    store = {}

    def grab(t, hook):
        store["x"] = t
        return t
    outs = []
    with torch.no_grad():
        for b in range(len(toks)):
            x = torch.tensor(toks[b:b + 1].astype(np.int64), device="cuda")
            model.run_with_hooks(x, fwd_hooks=[(f"blocks.{l}.mlp.hook_in", grab)], stop_at_layer=l + 1)
            outs.append(model.transcoders[l].encode(store["x"][0, 1:]).float())
    return torch.cat(outs)


def main():
    rng = np.random.default_rng(20261108)
    feats = []
    for i in range(212):
        s = json.loads((D / "graphs" / "A" / f"{i:03d}.json").read_text())
        for r, f in enumerate(s["top10"]):
            feats.append((i, r, f["layer"], f["pos"], f["idx"]))
    pick = [feats[k] for k in rng.choice(len(feats), 30, replace=False)]
    toks = np.fromfile(D / "heldout_tokens.u32", dtype=np.uint32).reshape(-1, 1024)[:20]
    stored = {tuple(map(int, k.split(","))): v for k, v in json.loads((D / "match" / "effects_A.json").read_text()).items()}
    mA = G.load("A")
    mB = G.load("B")
    decA, decB = M.decoders_from_model(mA), M.decoders_from_model(mB)
    rows = []
    cacheA, cacheB = {}, {}
    for (i, r, l, t, idx) in pick:
        if l not in cacheA:
            cacheA[l] = layer_acts(mA, toks, l)
            cacheB[l] = layer_acts(mB, toks, l)
        a = cacheA[l][:, idx]
        Bm = cacheB[l]
        if a.std() == 0:
            corr_best, corr_g = None, None
        else:
            az = (a - a.mean()) / a.std()
            bz = (Bm - Bm.mean(0)) / Bm.std(0).clamp_min(1e-8)
            c = (az[:, None] * bz).mean(0)
            corr_best, corr_g = float(c.max()), int(c.argmax())
        cos = decB[l].float() @ decA[l][idx].float()
        cos_best, cos_g = float(cos.max()), int(cos.argmax())
        rows.append({"i": i, "rank": r, "layer": l, "pos": t, "idx": idx, "corr_best": corr_best, "corr_match": corr_g,
                     "cos_best": cos_best, "cos_match": cos_g, "same_feature": corr_g == cos_g,
                     "both_clear_0.7": (corr_best or 0) >= 0.7 and cos_best >= 0.7,
                     "active_frac_heldout": float((a > 0).float().mean())})
    del mA, mB
    torch.cuda.empty_cache()
    m32 = G.load("A", dtype=torch.float32)
    e = M.Effects(m32, G.prompts())
    for row in rows:
        row["effect_rerun"] = e(row["i"], row["layer"], row["pos"], row["idx"])
        row["effect_stored"] = stored.get((row["i"], row["layer"], row["pos"], row["idx"]))
    ok = [r for r in rows if r["corr_best"] is not None]
    out = {"features": len(rows), "with_heldout_activity": len(ok),
           "same_feature_by_both_methods": sum(r["same_feature"] for r in ok),
           "cosine_match_clears_0.7": sum(r["cos_best"] >= 0.7 for r in rows),
           "correlation_match_clears_0.7": sum((r["corr_best"] or 0) >= 0.7 for r in rows),
           "both_clear_and_same": sum(r["same_feature"] and r["both_clear_0.7"] for r in ok),
           "ablation_rerun_identical": sum(abs(r["effect_rerun"] - r["effect_stored"]) < 1e-4 for r in rows if r["effect_stored"] is not None),
           "rows": rows}
    (RUN / "results" / "tables" / "g4.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=1))


if __name__ == "__main__":
    main()
