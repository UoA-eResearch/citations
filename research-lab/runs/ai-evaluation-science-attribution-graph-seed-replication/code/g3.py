"""G3 plausibility (plan section 3). Runs on the guest A100. -> results/tables/g3.json
(1) For prompt 0 ("The capital of France is" -> " Paris"), set A's top-10 features: the 5 vocabulary tokens their
decoders promote most (decoder x unembedding). (2) Three prompts traced: top-3 features with influence and ablation
effect in A, and whether each has a counterpart in B and C.
D4 (after the independent review): the three traced prompts are drawn at random (seed 20261110), not the first prompt
of chosen families; prompts are addressed by their stable index; counterparts come from data/match_d4/."""
import json
import sys
from pathlib import Path

import torch

RUN = Path(__file__).resolve().parents[1]
D = RUN / "data"
sys.path.insert(0, str(RUN / "code"))
import graphs as G  # noqa: E402

m = G.load("A")
WU = m.W_U.float()
s = json.loads((D / "graphs" / "A" / "000.json").read_text())
lens = []
for f in s["top10"]:
    v = m.transcoders[f["layer"]].W_dec[f["idx"]].float() @ WU
    lens.append({**{k: f[k] for k in ("layer", "pos", "idx")}, "top_tokens": [m.tokenizer.decode([int(t)]) for t in v.topk(5).indices]})
eff = {tuple(map(int, k.split(","))): v for k, v in json.loads((D / "match" / "effects_A.json").read_text()).items()}
match = {}
for Y in ("B", "C"):
    for line in (D / "match_d4" / f"A_{Y}.jsonl").read_text().splitlines():
        r = json.loads(line)
        match[(Y, r["i"], r["rank"])] = r["counterpart"]
import random
ps = {p["i"]: p for p in G.prompts()}
picks = {}
for i in sorted(random.Random(20261110).sample(sorted(ps), 3)):
    g = json.loads((D / "graphs" / "A" / f"{i:03d}.json").read_text())
    picks[str(i)] = {"family": ps[i]["family"], "prompt": ps[i]["prompt"], "target": ps[i]["target_token"], "n_kept": g["n_kept"], "error_share": g["error_share"],
                  "top3": [{**{k: f[k] for k in ("layer", "pos", "idx", "influence")}, "ablation_effect": eff.get((i, f["layer"], f["pos"], f["idx"])),
                            "counterpart_B": match.get(("B", i, r)), "counterpart_C": match.get(("C", i, r))} for r, f in enumerate(g["top10"][:3])]}
(RUN / "results" / "tables" / "g3.json").write_text(json.dumps({"capital_prompt_logit_lens": lens, "traced": picks}, indent=1) + "\n")
print(json.dumps(lens[:6])); print(json.dumps(picks)[:1200])
