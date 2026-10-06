"""Download the two open reference-generator models (plan section 3) and record their exact revisions."""
import json
import os
from pathlib import Path

from huggingface_hub import HfApi, snapshot_download

RUN = Path(__file__).resolve().parents[1]
tok_path = Path.home() / ".config" / "hf" / "token"
token = tok_path.read_text().strip() if tok_path.exists() else None
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
revs = {}
for repo in ["Qwen/Qwen2.5-32B-Instruct", "allenai/OLMo-2-0325-32B-Instruct"]:
    info = HfApi().model_info(repo, token=token)
    revs[repo] = info.sha
    snapshot_download(repo, revision=info.sha, local_dir=RUN / "data" / "models" / repo.split("/")[1], token=token,
                      allow_patterns=["*.json", "*.safetensors", "*.txt", "*.model", "tokenizer*"])
    print(repo, info.sha, flush=True)
json.dump(revs, open(RUN / "results" / "tables" / "generator_revisions.json", "w"), indent=1)
