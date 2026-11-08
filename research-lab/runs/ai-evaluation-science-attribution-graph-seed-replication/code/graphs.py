"""Attribution graphs (plan section 0, "Graphs"). Runs on the guest A100.

  graphs.py smoke SET          load one set, build one graph, print timing and the top 10
  graphs.py build SET [N]      every kept prompt -> data/graphs/<SET>/<i>.pt (pruned top-k summary + everything matching needs)

Settings are identical for every set: the target is the answer token, max_feature_nodes 8,192, prune_graph(node 0.8,
edge 0.98). SET is A, B, C, D (data/sets/<SET>/config.yaml, TopK k=64) or "public" (mwhanna/qwen3-0.6b-transcoders-lowl0).
Per graph we keep: the active features (layer, pos, idx) after pruning with their influence on the target logit, the
top-30 per layer by influence (for subspace replication), the error-node share of influence, and node counts.
"""
import json
import sys
import time
from pathlib import Path

import torch

RUN = Path(__file__).resolve().parents[1]
D = RUN / "data"
MODEL = "Qwen/Qwen3-0.6B"


def load(set_name, dtype=torch.bfloat16):
    from circuit_tracer import ReplacementModel
    if set_name == "public":
        return ReplacementModel.from_pretrained(MODEL, "mwhanna/qwen3-0.6b-transcoders-lowl0", dtype=dtype)
    from circuit_tracer.transcoder.single_layer_transcoder import load_transcoder_set
    d = D / "sets" / set_name
    ts = load_transcoder_set({l: str(d / f"layer_{l}.safetensors") for l in range(28)}, scan_name=f"local-{set_name}",
                             feature_input_hook="mlp.hook_in", feature_output_hook="mlp.hook_out",
                             dtype=dtype, activation="topk", k=64)
    return ReplacementModel.from_pretrained_and_transcoders(MODEL, ts, dtype=dtype)


def summarise(graph):
    from circuit_tracer.graph import compute_node_influence, prune_graph
    pr = prune_graph(graph, node_threshold=0.8, edge_threshold=0.98)
    node_mask = pr[0] if isinstance(pr, tuple) else pr.node_mask
    n_feat = len(graph.selected_features)
    A = graph.adjacency_matrix
    n_logits = len(graph.logit_targets)
    logit_w = torch.zeros(A.shape[0], device=A.device)
    logit_w[-n_logits:] = graph.logit_probabilities.to(A.device)
    infl = compute_node_influence(A, logit_w)
    feats = graph.active_features[graph.selected_features]          # (n_feat, 3): layer, pos, idx
    fi = infl[:n_feat].float().cpu()
    keep = node_mask[:n_feat].cpu()
    n_err = graph.cfg.n_layers * graph.n_pos
    err_infl = infl[n_feat:n_feat + n_err].float().abs().sum().item()
    tot = infl[:n_feat + n_err + graph.n_pos].float().abs().sum().item()
    order = torch.argsort(fi * keep, descending=True)
    top10 = [int(i) for i in order[:10] if keep[i]]
    by_layer = {}
    for i in torch.argsort(fi, descending=True).tolist():
        l = int(feats[i, 0])
        if len(by_layer.setdefault(l, [])) < 30:
            by_layer[l].append(int(feats[i, 2]))
    return {"top10": [{"layer": int(feats[i, 0]), "pos": int(feats[i, 1]), "idx": int(feats[i, 2]), "influence": float(fi[i]),
                       "activation": float(graph.activation_values[i])} for i in top10],
            "top30_by_layer": by_layer, "n_features": n_feat, "n_kept": int(keep.sum()),
            "error_share": err_infl / tot if tot else None, "n_pos": int(graph.n_pos)}


def prompts():
    return [json.loads(l) for l in (RUN / "results" / "tables" / "prompts.jsonl").read_text().splitlines()]


def smoke(set_name):
    from circuit_tracer import attribute
    t0 = time.time()
    m = load(set_name)
    print("loaded", round(time.time() - t0, 1), "s", flush=True)
    p = prompts()[0]
    t1 = time.time()
    g = attribute(p["prompt"], m, attribution_targets=[p["target_token"]], max_feature_nodes=8192, batch_size=256)
    s = summarise(g)
    print("graph", round(time.time() - t1, 1), "s; features", s["n_features"], "kept", s["n_kept"], "error share", round(s["error_share"], 3))
    for f in s["top10"]:
        print(f)


def build(set_name, limit=None):
    from circuit_tracer import attribute
    out = D / "graphs" / set_name
    out.mkdir(parents=True, exist_ok=True)
    m = load(set_name)
    ps = prompts()[: int(limit)] if limit else prompts()
    for i, p in enumerate(ps):
        f = out / f"{i:03d}.json"
        if f.exists():
            continue
        try:
            g = attribute(p["prompt"], m, attribution_targets=[p["target_token"]], max_feature_nodes=8192, batch_size=256)
            s = summarise(g)
            s.update({"i": i, "family": p["family"], "prompt": p["prompt"], "target": p["target_token"], "status": "ok"})
            torch.save({"active": g.active_features.cpu().to(torch.int32)}, out / f"{i:03d}_active.pt")   # for matching
        except Exception as e:
            s = {"i": i, "status": "failed", "error": str(e)[:200]}
        f.write_text(json.dumps(s))
        if i % 20 == 0:
            print(time.strftime("%H:%M:%S"), set_name, i, flush=True)
    print("== built", set_name)


if __name__ == "__main__":
    a = sys.argv
    {"smoke": lambda: smoke(a[2]), "build": lambda: build(a[2], *(a[3:4]))}[a[1]]()
