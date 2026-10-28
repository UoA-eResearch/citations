"""D3: recompute N as the non-embedding parameter count (plan section 2).

evaluate.py excluded parameters whose name contains "embed", but transformers names the GPT-NeoX output head
`lm_head`, so the stored N included one vocab x d matrix (50,304 x d) for every size. N depends only on the
architecture, so it is recomputed here from each model's config, without weights or a GPU:

  per layer   12 d^2 + 13 d   (qkv 3d^2+3d, attn dense d^2+d, mlp 8d^2+5d, two layer norms 4d)
  plus        2 d             (final layer norm)

  fix_n.py -> results/tables/losses.csv (N corrected, N_with_head and N_total kept), results/tables/n_params.csv
"""
import json
import urllib.request
from pathlib import Path

import pandas as pd

T = Path(__file__).resolve().parents[1] / "results" / "tables"
SIZES = {"14m": "EleutherAI/pythia-14m", "31m": "EleutherAI/pythia-31m", "70m": "EleutherAI/pythia-70m",
         "160m": "EleutherAI/pythia-160m", "410m": "EleutherAI/pythia-410m", "1b": "EleutherAI/pythia-1b",
         "1.4b": "EleutherAI/pythia-1.4b", "2.8b": "EleutherAI/pythia-2.8b"}
rows = []
for s, mid in SIZES.items():
    c = json.load(urllib.request.urlopen(f"https://huggingface.co/{mid}/raw/main/config.json", timeout=60))
    d, L, V = c["hidden_size"], c["num_hidden_layers"], c["vocab_size"]
    nonemb = L * (12 * d * d + 13 * d) + 2 * d
    rows.append({"size": s, "hidden": d, "layers": L, "vocab": V, "N_nonembedding": nonemb,
                 "N_with_head": nonemb + V * d, "N_total": nonemb + 2 * V * d})
P = pd.DataFrame(rows)
P.to_csv(T / "n_params.csv", index=False)
print(P.to_string(index=False))
L = pd.read_csv(T / "losses.csv")
m = P.set_index("size")
old = L.groupby("size").N.first()
bad = {s: (int(old[s]), int(m.loc[s, "N_with_head"])) for s in old.index if int(old[s]) != int(m.loc[s, "N_with_head"])}
assert not bad, f"stored N is not non-embedding+head: {bad}"      # confirms the diagnosis before overwriting
L["N_with_head"] = L["size"].map(m.N_with_head)
L["N_total"] = L["size"].map(m.N_total)
L["N"] = L["size"].map(m.N_nonembedding)
L.to_csv(T / "losses.csv", index=False)
print("\nlosses.csv N corrected; ratio old/new:", {s: round(int(old[s]) / int(m.loc[s, "N_nonembedding"]), 2) for s in old.index})
