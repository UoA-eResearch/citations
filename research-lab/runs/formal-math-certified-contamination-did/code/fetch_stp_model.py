"""Download the STP prover (kfdong/STP_model_Lean_0320, trained on STP_Lean_0320) for the D3 secondary analysis."""
import json
import os
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download, snapshot_download

RUN = Path(__file__).resolve().parents[1]
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
tok = (Path.home() / ".config" / "hf" / "token").read_text().strip()
repo = "kfdong/STP_model_Lean_0320"
info = HfApi().model_info(repo, token=tok)
snapshot_download(repo, revision=info.sha, local_dir=RUN / "data" / "models" / "STP_model_Lean_0320", token=tok,
                  allow_patterns=["*.json", "*.safetensors", "*.txt", "tokenizer*", "*.model", "*.jinja", "*.py", "README.md"])
f = RUN / "results" / "tables" / "revisions.json"
r = json.load(open(f)); r[repo] = info.sha; json.dump(r, open(f, "w"), indent=1)
print(repo, info.sha)
